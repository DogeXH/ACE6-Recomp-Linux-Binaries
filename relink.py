#!/usr/bin/env python3
"""Relink the supplied AC6 object kit, optionally replacing three static libraries.

Requires a compatible Linux clang++ toolchain and the system development
libraries named by relink-kit/link.json. Never runs the resulting executable.

Original input paths must stay within the kit and match recorded sizes/hashes.
Overrides may live elsewhere, but must be regular (not thin) static archives.
The output must not exist and its parent directory must already exist.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys


REPLACEMENT_NAMES = ("avcodec", "avutil", "mspack")


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def kit_path(kit, name):
    if not isinstance(name, str) or not name or "\0" in name:
        raise ValueError("Each kit input needs a nonempty relative path")
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or "\\" in name:
        raise ValueError("Kit input must remain inside the kit: {}".format(name))
    path = (kit / name).resolve(strict=True)
    try:
        path.relative_to(kit)
    except ValueError:
        raise ValueError("Kit input resolves outside the kit: {}".format(name))
    if not path.is_file():
        raise ValueError("Kit input is not a regular file: {}".format(name))
    return path


def validate_archive(path):
    with path.open("rb") as source:
        magic = source.read(8)
    if magic != b"!<arch>\n":
        raise ValueError("{} must be a regular static archive, not a thin archive".format(path))


def make_command(kit, output, compiler, replacements):
    kit = kit.expanduser().resolve(strict=True)
    manifest = json.loads((kit / "link.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Unsupported relink manifest schema")
    arguments = manifest.get("arguments")
    inputs = manifest.get("inputs")
    targets = manifest.get("replacements", {})
    if (not isinstance(arguments, list) or not arguments
            or not all(isinstance(arg, str) and arg and "\0" not in arg for arg in arguments)
            or not isinstance(inputs, list) or not inputs
            or not isinstance(targets, dict)):
        raise ValueError("Malformed relink arguments, inputs, or replacement map")
    if any(arg == "-o" or arg.startswith("--output") for arg in arguments):
        raise ValueError("Manifest must leave the output path to --output")
    selected = {}
    entries = {}
    for entry in inputs:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("Malformed relink input record")
        name = entry["path"]
        if name in entries:
            raise ValueError("Duplicate relink input: {}".format(name))
        if name not in arguments:
            raise ValueError("Unreferenced relink input: {}".format(name))
        if entry.get("kind") not in ("object", "archive"):
            raise ValueError("Unknown input kind: {}".format(name))
        entries[name] = entry
    for name, replacement in replacements.items():
        if name not in REPLACEMENT_NAMES or name not in targets:
            raise ValueError("No replaceable {} archive in this kit".format(name))
        target = targets[name]
        if target not in entries or entries[target]["kind"] != "archive":
            raise ValueError("Invalid replacement target for {}".format(name))
        path = replacement.expanduser().resolve(strict=True)
        if not path.is_file():
            raise ValueError("Replacement must be a file: {}".format(path))
        validate_archive(path)
        selected[target] = path
    for name, entry in entries.items():
        if name in selected:
            continue
        path = kit_path(kit, name)
        if path.stat().st_size != entry.get("bytes") or sha256(path) != entry.get("sha256"):
            raise ValueError("Original kit input failed its size/hash check: {}".format(name))
        if entry["kind"] == "archive":
            validate_archive(path)
        selected[name] = path
    # Every direct object/archive argument must be declared and checked.
    for arg in arguments:
        if not arg.startswith("-") and arg.endswith((".o", ".a")) and arg not in entries:
            raise ValueError("Undeclared link input: {}".format(arg))
        if arg.startswith("@"):
            raise ValueError("Response-file arguments are not supported in the packaged manifest")
    return [compiler, *[str(selected[arg]) if arg in selected else arg for arg in arguments],
            "-o", str(output)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Original objects/archives are checked against SHA256. Overrides must be existing "
        "regular .a archives; thin archives are rejected. Paths may contain spaces. "
        "The linker is invoked directly, without a shell. A compatible system toolchain "
        "and development libraries are still required."))
    parser.add_argument("--kit", type=Path, default=Path(__file__).resolve().parent / "relink-kit")
    parser.add_argument("--output", required=True, type=Path, help="new output executable path")
    parser.add_argument("--compiler", default="clang++", help="clang++ executable name or path")
    for name in REPLACEMENT_NAMES:
        parser.add_argument("--" + name, type=Path, help="replacement {} static archive".format(name))
    parser.add_argument("--dry-run", action="store_true", help="validate and print the link command only")
    args = parser.parse_args(argv)
    try:
        output = Path(os.path.abspath(os.path.expanduser(str(args.output))))
        if os.path.lexists(str(output)):
            raise ValueError("Output already exists; choose a new path: {}".format(output))
        if not output.parent.is_dir():
            raise ValueError("Output parent directory does not exist: {}".format(output.parent))
        replacements = {name: getattr(args, name) for name in REPLACEMENT_NAMES
                        if getattr(args, name) is not None}
        command = make_command(args.kit, output, args.compiler, replacements)
        if args.dry_run:
            print(shlex.join(command))
            return 0
        completed = subprocess.run(command, cwd=args.kit.expanduser().resolve(), check=False)
        if completed.returncode:
            print("Linker failed; inspect and remove any partial output before retrying.", file=sys.stderr)
            return 1
        if not output.is_file():
            raise ValueError("Linker reported success but did not create the output")
        print("Created {}\nSHA256 {}".format(output, sha256(output)))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print("Relink failed: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

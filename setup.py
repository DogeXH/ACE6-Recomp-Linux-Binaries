#!/usr/bin/env python3
"""Configure this precompiled AC6 package using your own game ISO.

Creates a relative runtime/ac6recomp.toml link so configuration is found when
the executable runs through the bundled loader. Existing configuration paths
are preserved, and a runtime directory symlink is not accepted.
"""

import argparse
import os
from pathlib import Path
import re
import struct
import sys


PACKAGE_DIR = Path(__file__).resolve().parent


def existing_file(value, label):
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("{} must be a file: {}".format(label, path))
    return path


def validate_binary(path):
    """Read the ELF header without executing the binary."""
    with path.open("rb") as source:
        header = source.read(64)
    if len(header) != 64 or header[:7] != b"\x7fELF\x02\x01\x01":
        raise ValueError("ac6recomp must be a 64-bit little-endian Linux ELF executable")
    kind, machine, version, entry = struct.unpack_from("<HHIQ", header, 16)
    header_size = struct.unpack_from("<H", header, 52)[0]
    if (header[7] not in (0, 3) or kind not in (2, 3) or machine != 62
            or version != 1 or entry == 0 or header_size != 64):
        raise ValueError("ac6recomp must be a Linux x86-64 ELF executable")
    if not path.stat().st_mode & 0o111:
        raise ValueError("ac6recomp is not executable; extract the release archive with permissions intact")


def toml_string(value):
    escapes = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t",
               "\n": "\\n", "\f": "\\f", "\r": "\\r"}
    return '"' + "".join(
        escapes.get(char, "\\u{:04X}".format(ord(char)) if ord(char) < 32
                    or ord(char) == 127 else char)
        for char in value
    ) + '"'


def configuration(iso):
    text = (PACKAGE_DIR / "steam-deck.toml").read_text(encoding="utf-8")
    text, count = re.subn(r"^game_iso[ \t]*=.*$",
                          lambda match: "game_iso = " + toml_string(str(iso)),
                          text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Expected exactly one game_iso in steam-deck.toml")
    return text


def steam_wrapper(device):
    return ("#!/usr/bin/env bash\nset -euo pipefail\n"
            + 'script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"\n'
            + 'if [[ ! -f "$script_dir/ac6recomp.toml" ]]; then\n'
            + "  printf 'Run python3 setup.py --iso /path/to/your/game.iso first.\\n' >&2\n"
            + '  exit 1\nfi\n'
            + 'export AC6_GLIBC_RUNTIME="$script_dir/runtime"\n'
            + "export AC6_DECK_TUNE={}\n".format("1" if device == "steam-deck" else "0")
            + 'exec /usr/bin/python3 "$script_dir/ac6-launch.py" "$@"\n')


def configure(iso_value, device):
    config_path = PACKAGE_DIR / "ac6recomp.toml"
    if os.path.lexists(str(config_path)):
        raise ValueError("ac6recomp.toml already exists; setup will not overwrite it. "
                         "Edit that file to change game_iso, or use a fresh extraction.")
    iso = existing_file(iso_value, "--iso")
    binary = existing_file(str(PACKAGE_DIR / "ac6recomp"), "ac6recomp")
    validate_binary(binary)
    runtime = PACKAGE_DIR / "runtime"
    if runtime.is_symlink() or not runtime.is_dir():
        raise ValueError("runtime must be an ordinary directory, not a symlink")
    runtime_config = runtime / "ac6recomp.toml"
    if os.path.lexists(str(runtime_config)):
        raise ValueError("runtime/ac6recomp.toml already exists; setup will not overwrite it. "
                         "Use a fresh extraction or inspect the existing path.")
    loader = existing_file(str(runtime / "ld-linux-x86-64.so.2"),
                           "runtime loader")
    if not os.access(str(loader), os.X_OK):
        raise ValueError("runtime/ld-linux-x86-64.so.2 must be executable")
    existing_file(str(PACKAGE_DIR / "ac6-launch.py"), "launcher")
    wrapper_path = PACKAGE_DIR / "ac6-steam.sh"
    if wrapper_path.is_symlink() or (wrapper_path.exists() and not wrapper_path.is_file()):
        raise ValueError("ac6-steam.sh must be a regular file")
    directories = [PACKAGE_DIR / name for name in ("user-data", "dlc", "runtime-state")]
    for directory in directories:
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise ValueError("{} must be an ordinary directory".format(directory.name))
    config = configuration(iso)
    wrapper = steam_wrapper(device)

    # Exclusive creation protects an existing configuration, including a
    # concurrent setup run. Never copy, modify, or extract the user's ISO.
    with config_path.open("x", encoding="utf-8") as output:
        output.write(config)
    # This build discovers its executable folder through /proc/self/exe,
    # which is the runtime loader's folder during an explicit-loader launch.
    # A relative link keeps discovery working after the package is moved.
    runtime_config.symlink_to("../ac6recomp.toml")
    wrapper_path.write_text(wrapper, encoding="utf-8")
    wrapper_path.chmod(0o755)
    for directory in directories:
        directory.mkdir(exist_ok=True)
    return iso


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Checks package files without launching the game. Your ISO stays in place; "
        "runtime libraries and Steam shortcuts are not installed system-wide."))
    parser.add_argument("--iso", required=True, help="path to your own US-region AC6 ISO")
    parser.add_argument("--device", choices=("steam-deck", "desktop"), default="steam-deck",
                        help="Steam Deck CPU/GPU tuning, or desktop without tuning (default: steam-deck)")
    args = parser.parse_args(argv)
    try:
        iso = configure(args.iso, args.device)
    except (OSError, ValueError) as error:
        print("Setup failed: {}".format(error), file=sys.stderr)
        return 1
    print("Configured {} for {}.".format(PACKAGE_DIR, args.device))
    print("ISO stays at: {}".format(iso))
    print("Launch ac6-steam.sh, or add it to Steam as a Non-Steam Game.")
    print("In Steam, set Start In to this package folder; leave Launch Options empty and Proton off.")
    print("The package can be moved; game_iso remains an absolute path to your ISO.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ac6_relink", ROOT / "relink.py")
relink = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relink)


class RelinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.kit = self.root / "kit with spaces"
        (self.kit / "objects").mkdir(parents=True)
        (self.kit / "libraries").mkdir()
        self.paths = ["objects/game.o", "libraries/liblibavcodecrd.a",
                      "libraries/liblibavutilrd.a", "libraries/libmspackrd.a"]
        inputs = []
        for name in self.paths:
            path = self.kit / name
            kind = "object" if name.endswith(".o") else "archive"
            path.write_bytes(b"synthetic object" if kind == "object" else b"!<arch>\n")
            inputs.append({"path": name, "kind": kind, "bytes": path.stat().st_size,
                           "sha256": relink.sha256(path)})
        self.manifest = {"schema_version": 1, "compiler": "clang++",
                         "arguments": ["-O2", *self.paths, "-pthread", "-ldl"],
                         "inputs": inputs,
                         "replacements": dict(zip(relink.REPLACEMENT_NAMES, self.paths[1:]))}
        self.write_manifest()
        self.output = self.root / "new executable"

    def write_manifest(self):
        (self.kit / "link.json").write_text(json.dumps(self.manifest))

    def command(self, replacements=None):
        return relink.make_command(self.kit, self.output, "clang++", replacements or {})

    def test_relocated_kit_and_paths_with_spaces(self):
        moved = self.kit.with_name("relocated kit")
        self.kit.rename(moved)
        self.kit = moved
        command = self.command()
        self.assertIn(str(moved / self.paths[0]), command)
        self.assertEqual(command[-2:], ["-o", str(self.output)])
        self.assertIn("-ldl", command)

    def test_archive_override_changes_only_selected_input(self):
        archive = self.root / "modified codec.a"
        archive.write_bytes(b"!<arch>\nreplacement fixture")
        original = self.command()
        changed = self.command({"avcodec": archive})
        differences = [(a, b) for a, b in zip(original, changed) if a != b]
        self.assertEqual(differences, [(str(self.kit / self.paths[1]), str(archive))])

    def test_changed_original_rejected(self):
        (self.kit / self.paths[0]).write_bytes(b"changed object")
        with self.assertRaisesRegex(ValueError, "hash check"):
            self.command()

    def test_missing_input_rejected(self):
        (self.kit / self.paths[0]).unlink()
        with self.assertRaises(FileNotFoundError):
            self.command()

    def test_thin_override_rejected(self):
        archive = self.root / "thin.a"
        archive.write_bytes(b"!<thin>\n")
        with self.assertRaisesRegex(ValueError, "thin archive"):
            self.command({"avcodec": archive})

    def test_undeclared_input_rejected(self):
        self.manifest["arguments"].append("hidden.o")
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Undeclared"):
            self.command()

    def test_path_escape_rejected(self):
        self.manifest["inputs"][0]["path"] = "../outside.o"
        self.manifest["arguments"][1] = "../outside.o"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "inside the kit"):
            self.command()

    def test_existing_output_refused(self):
        self.output.write_text("preserve me")
        status = relink.main(["--kit", str(self.kit), "--output", str(self.output), "--dry-run"])
        self.assertEqual(status, 1)
        self.assertEqual(self.output.read_text(), "preserve me")


if __name__ == "__main__":
    unittest.main()

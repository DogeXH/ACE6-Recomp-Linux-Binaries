import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ac6_release_setup", ROOT / "setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / "package with spaces"
        self.package.mkdir()
        self.original_package = setup.PACKAGE_DIR
        setup.PACKAGE_DIR = self.package
        self.addCleanup(setattr, setup, "PACKAGE_DIR", self.original_package)
        shutil.copyfile(ROOT / "steam-deck.toml", self.package / "steam-deck.toml")
        (self.package / "ac6-launch.py").write_text("# test fixture; never launches a game\n")
        header = bytearray(64)
        header[:7] = b"\x7fELF\x02\x01\x01"
        struct.pack_into("<HHIQ", header, 16, 3, 62, 1, 0x400000)
        struct.pack_into("<H", header, 52, 64)
        self.binary = self.package / "ac6recomp"
        self.binary.write_bytes(header)
        self.binary.chmod(0o755)
        (self.package / "runtime").mkdir()
        self.loader = self.package / "runtime" / "ld-linux-x86-64.so.2"
        self.loader.write_bytes(header)
        self.loader.chmod(0o755)
        self.iso = Path(self.temp.name) / 'my AC6 "disc".iso'
        self.iso.write_bytes(b"synthetic ISO placeholder")

    def test_spaces_and_quotes_no_game_data_copied(self):
        original = self.iso.read_bytes()
        setup.configure(str(self.iso), "steam-deck")
        config = (self.package / "ac6recomp.toml").read_text()
        iso_line = next(line for line in config.splitlines() if line.startswith("game_iso = "))
        self.assertEqual(json.loads(iso_line.split(" = ", 1)[1]), str(self.iso.resolve()))
        self.assertEqual(self.iso.read_bytes(), original)
        self.assertFalse((self.package / self.iso.name).exists())
        for name in ("user-data", "dlc", "runtime-state"):
            self.assertEqual(list((self.package / name).iterdir()), [])
        wrapper = (self.package / "ac6-steam.sh").read_text()
        self.assertIn('AC6_GLIBC_RUNTIME="$script_dir/runtime"', wrapper)
        self.assertNotIn(str(self.package), wrapper)
        self.assertIn("export AC6_DECK_TUNE=1", wrapper)
        subprocess.run(["bash", "-n", str(self.package / "ac6-steam.sh")], check=True)

    def test_existing_config_is_preserved(self):
        path = self.package / "ac6recomp.toml"
        path.write_text("precious existing config\n")
        with self.assertRaisesRegex(ValueError, "already exists"):
            setup.configure(str(self.iso), "steam-deck")
        self.assertEqual(path.read_text(), "precious existing config\n")
        self.assertFalse((self.package / "runtime-state").exists())

    def test_dangling_config_symlink_is_rejected(self):
        (self.package / "ac6recomp.toml").symlink_to(self.package / "missing")
        with self.assertRaisesRegex(ValueError, "already exists"):
            setup.configure(str(self.iso), "steam-deck")
        self.assertFalse((self.package / "missing").exists())

    def test_desktop_disables_tuning(self):
        setup.configure(str(self.iso), "desktop")
        self.assertIn("export AC6_DECK_TUNE=0", (self.package / "ac6-steam.sh").read_text())

    def test_loader_folder_finds_configuration_through_relative_link(self):
        setup.configure(str(self.iso), "steam-deck")
        runtime_config = self.package / "runtime" / "ac6recomp.toml"
        self.assertTrue(runtime_config.is_symlink())
        self.assertEqual(runtime_config.readlink(), Path("../ac6recomp.toml"))
        self.assertEqual(runtime_config.resolve(), (self.package / "ac6recomp.toml").resolve())
        self.assertIn(str(self.iso.resolve()).replace('"', '\\"'), runtime_config.read_text())

    def test_existing_runtime_configuration_is_preserved(self):
        runtime_config = self.package / "runtime" / "ac6recomp.toml"
        runtime_config.write_text("preserve runtime config\n")
        with self.assertRaisesRegex(ValueError, "runtime/ac6recomp.toml already exists"):
            setup.configure(str(self.iso), "steam-deck")
        self.assertEqual(runtime_config.read_text(), "preserve runtime config\n")
        self.assertFalse((self.package / "ac6recomp.toml").exists())
        runtime_config.unlink()
        runtime_config.symlink_to("missing-config")
        with self.assertRaisesRegex(ValueError, "runtime/ac6recomp.toml already exists"):
            setup.configure(str(self.iso), "steam-deck")
        self.assertEqual(runtime_config.readlink(), Path("missing-config"))
        self.assertFalse((self.package / "ac6recomp.toml").exists())

    def test_runtime_directory_symlink_is_rejected_before_writes(self):
        runtime = self.package / "runtime"
        outside_runtime = self.package.parent / "outside runtime"
        runtime.rename(outside_runtime)
        runtime.symlink_to(outside_runtime, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "runtime must be an ordinary directory"):
            setup.configure(str(self.iso), "steam-deck")
        self.assertFalse((self.package / "ac6recomp.toml").exists())
        self.assertFalse((outside_runtime / "ac6recomp.toml").exists())

    def test_invalid_binary_rejected_before_writes(self):
        self.binary.write_bytes(b"not a Linux executable")
        with self.assertRaisesRegex(ValueError, "Linux ELF"):
            setup.configure(str(self.iso), "steam-deck")
        self.assertFalse((self.package / "ac6recomp.toml").exists())

    def test_missing_iso_or_loader_rejected_before_writes(self):
        with self.assertRaises(FileNotFoundError):
            setup.configure(str(self.iso) + ".missing", "steam-deck")
        self.loader.unlink()
        with self.assertRaises(FileNotFoundError):
            setup.configure(str(self.iso), "steam-deck")
        self.assertFalse((self.package / "ac6recomp.toml").exists())

    def test_relocated_wrapper_uses_relocated_runtime(self):
        # Execute only a stub Python launcher, never either synthetic ELF file.
        (self.package / "ac6-launch.py").write_text(
            "import os\nfrom pathlib import Path\n"
            "Path(__file__).with_name('observed-runtime.txt').write_text(os.environ['AC6_GLIBC_RUNTIME'])\n")
        setup.configure(str(self.iso), "desktop")
        relocated = self.package.with_name("moved package with spaces")
        self.package.rename(relocated)
        subprocess.run(["bash", str(relocated / "ac6-steam.sh")], check=True)
        self.assertEqual((relocated / "observed-runtime.txt").read_text(), str(relocated / "runtime"))
        self.assertEqual((relocated / "runtime" / "ac6recomp.toml").resolve(),
                         (relocated / "ac6recomp.toml").resolve())


if __name__ == "__main__":
    unittest.main()

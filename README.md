# Ace Combat 6 — precompiled Linux build

Precompiled **Linux x86-64** AC6Recomp for Steam Deck and compatible PCs. Download the executable package from **[Releases](https://github.com/DogeXH/ACE6-Recomp-Linux-Binaries/releases)**; you do not need to compile the game.

You must supply your own **US-region Ace Combat 6 ISO**. No ISO, textures, audio, DLC, game shader cache, or save files are included. The executable contains compiled translated game code and requires the original game data at runtime.

## Install on Steam Deck

1. Download `ac6-linux-x86_64-20261004.tar.gz` from the release and extract it in Desktop Mode. Keep its files together in a writable folder.
2. Open a terminal in the extracted folder and run:

   ```sh
   python3 setup.py --iso "/path/to/your/Ace Combat 6.iso"
   ```

   Your ISO stays where it is. Setup writes the configuration and creates separate, initially empty save/DLC directories. It refuses to overwrite an existing configuration.
3. Add `ac6-steam.sh` to Steam as a **Non-Steam Game**. Set **Start In** to the extracted folder. Leave **Launch Options** empty and **Proton compatibility off**.
4. Launch through that shortcut. Normal controller input is enabled.

For another Linux PC, use `python3 setup.py --iso "/path/to/game.iso" --device desktop` to disable Deck-specific CPU/GPU tuning. The CPU must support x86-64-v3/AVX2. ARM, macOS, and Windows are not supported by this executable.

The package's C/C++ runtime is loaded privately; system libraries are not replaced. It still needs the host's Vulkan driver, GTK 3/X11 or XWayland, SDL audio dependencies, and Python 3. The launcher uses `xdotool` for graceful window shutdown when available. This release uses the host graphics driver; it does not include the private Mesa bundle from the earlier performance experiment.

To move the installation, move the entire extracted folder, then update Steam's **Target** and **Start In** paths or re-add the shortcut. The launcher resolves its runtime relative to itself. The ISO path in `ac6recomp.toml` is absolute; update `game_iso` if you move the ISO. Save data is under `user-data/`; do not overwrite it when updating.

## What this build is

This is a fresh October 4, 2026 build of the preserved September 13 performance-candidate source, using Clang 23.1.1 and the matching application objects supplied for relinking. It is **not byte-identical to the older installed executable**. Source restoration was checked against all 19,016 archived records. The game and renderer source were not replaced with newer upstream code.

It includes the custom Vulkan pipeline path integrated into ReXGlue/Xenia, targeted clear/transfer optimizations, main-scene 1x MSAA at 1280x720, 60 FPS timing/physics hooks, bounded pacing with two frames in flight, and the preserved Linux/audio/save fixes. Original effects sampling and normal controller input remain available.

The earlier executable averaged **59.96 unique FPS over one 80-second Mission 1 segment**, using a private Mesa driver. That measurement is not a benchmark of this rebuilt executable or the host-driver configuration. **Locked 60 FPS across the game is not established.** The relocated package passed a 30-second fresh-profile startup/shutdown check and displayed the opening ESRB notice. This does not validate gameplay, audio quality, or controls across missions. Known shutdown/audio warnings remain. See the [historical measurement details](https://github.com/DogeXH/ACE6-Recomp-Linux/blob/fc3667f759f705777edb3181af8133f14f901ca7/docs/LINUX_PERFORMANCE.md) and this release's `VERIFICATION.json` for the actual checks performed.

## Downloads and source

- `ac6-linux-x86_64-20261004.tar.gz`: executable, private runtime, launcher, setup, configuration template, notices, and verification record.
- `ac6-relink-kit-20261004.tar.gz`: matching application objects, static libraries, link arguments, and relinking tool. Regular players do not need this.
- `ac6-source-20261004.tar.gz`: corresponding project/dependency source and build definitions. Generated guest source and original game assets are excluded; the relink kit supplies compiled application objects.
- `runtime-sources-20261004.tar.gz`: source and packaging material for the privately bundled C/C++ runtime.
- `SHA256SUMS`: SHA256 checksums for the release archives.

The project source is also available in [DogeXH/ACE6-Recomp-Linux](https://github.com/DogeXH/ACE6-Recomp-Linux/tree/fc3667f759f705777edb3181af8133f14f901ca7). See [BUILD_AND_RELINK.md](BUILD_AND_RELINK.md) for rebuild/relink instructions and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for licenses and attribution.

This unofficial fan project builds on AC6Recomp, ReXGlue, Xenia, and their contributors. It is not affiliated with Bandai Namco, Project Aces, or Microsoft.

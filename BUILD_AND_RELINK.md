# Build and relink information

Regular players only need the executable archive. These materials let developers inspect the build and replace the statically linked FFmpeg and libmspack libraries without needing the original application source translation or game ISO for the relink step.

## Release build

The October 4 build restored the preserved modified source archive and verified all 19,016 archive records. It used the preserved generated guest translation, including its existing fixes. That generated source is not distributed; the matching compiled application objects are in the relink kit.

The Linux build ran in an isolated Arch container with:

- Clang and LLD 23.1.1.
- GCC/libstdc++ 16.2.1+r23+gd564253eb6c8-1.
- glibc 2.44+r50+g1848099f063e-1.
- `linux-amd64-relwithdebinfo`, x86-64-v3, `-O2`, and debug information.
- Vulkan enabled; D3D12 and FidelityFX disabled.
- Trace support enabled, but only the `ac6recomp` application target built.
- No LTO: the initial CMake IPO probe could not find LLVM archive tools. The supplied link inputs are ordinary relocatable objects.

The configure/build commands were:

```sh
cmake --preset linux-amd64-relwithdebinfo \
  -DREXGLUE_BUILD_TRACE_TOOLS=ON \
  -DCMAKE_EXE_LINKER_FLAGS=-fuse-ld=lld \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build --preset linux-amd64-relwithdebinfo \
  --target ac6recomp --parallel 3
```

The matching source archive is pinned to source-repository commit `fc3667f759f705777edb3181af8133f14f901ca7`. Its publication/setup files differ from the private historical checkout; its candidate application and vendored SDK source preserve the archived code. For a complete source rebuild, supply your own game executable and follow that archive's `docs/SETUP.md`, including the guarded post-codegen repair. No claim is made that arbitrary toolchains or regenerated code produce a byte-identical executable.

## Relink the supplied objects

Extract `ac6-relink-kit-20261004.tar.gz` on a compatible Linux x86-64 build machine. The archive contains `relink-kit/link.json`, application `.o` files, static `.a` files, this document, and `relink.py`. It does not contain a game ISO, raw XEX, textures, audio, saves, or game shader caches.

Install Clang, LLD, Python 3, a compatible C++ runtime/toolchain, and GTK3/X11 development libraries. The complete build package versions are in `build-packages.txt`. Keep the kit's folder structure intact, then run:

```sh
python3 relink.py --kit relink-kit --output "$PWD/ac6recomp-relinked"
```

The tool checks the size and SHA256 of every original object/archive before invoking `clang++` directly. It refuses to overwrite an existing output. `--dry-run` validates and prints the command without linking. System shared libraries are resolved by the linker from the installed development packages listed in `build-packages.txt`. You can inspect every linker argument in `link.json`.

This release's verification record reports the result of actually relinking these objects and comparing the output with the packaged executable.

## Replace FFmpeg or libmspack

The `ac6-source-20261004.tar.gz` archive includes the complete vendored FFmpeg and libmspack sources, their local changes, FFmpeg configuration/overlay headers, and their CMake recipes. You can modify those libraries and compile their archive targets without compiling the application or supplying game data:

```sh
cmake -S ac6-source -B library-build -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DREXSDK_DIR="$PWD/ac6-source/thirdparty/rexglue-sdk" \
  -DREXGLUE_BUILD_TRACE_TOOLS=ON
cmake --build library-build --target libavcodec libavutil mspack --parallel 3
```

Supply whichever replacement archives you changed:

```sh
python3 relink.py --kit relink-kit --output "$PWD/ac6recomp-modified" \
  --avcodec ac6-source/thirdparty/rexglue-sdk/out/linux-amd64/liblibavcodecrd.a \
  --avutil ac6-source/thirdparty/rexglue-sdk/out/linux-amd64/liblibavutilrd.a \
  --mspack ac6-source/thirdparty/rexglue-sdk/out/linux-amd64/libmspackrd.a
```

Overrides replace only their selected archive inputs. Unchanged inputs still have their hashes checked. Thin archives are rejected because they can depend on object files outside the archive. This package does not prohibit modification for personal use or reverse engineering for debugging those modifications.

## Private runtime

`runtime-sources-20261004.tar.gz` includes the exact glibc/GCC source commits, Arch package recipes and patches, build/package metadata, checksums, and licenses corresponding to the private runtime. The binaries were copied without modification from the package manager's verified packages. The archive documents rebuilding from those inputs; no independent glibc/GCC rebuild or bit-for-bit reproducibility claim is made.

Compatible replacement libraries may be placed in the package's `runtime/` directory. They are used by the launcher without replacing system libraries. Host GTK, audio, X11/Wayland, and Vulkan driver libraries are not distributed in this release.

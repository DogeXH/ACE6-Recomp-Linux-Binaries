# Third-party notices

This AC6 Linux build incorporates work from AC6Recomp, ReXGlue, the Xenia project, and the libraries identified below. Copyright remains with the respective authors. The complete notices and license terms are preserved in `licenses/`; the source locations and SHA256 hashes of those notice files are recorded in [license provenance](licenses/provenance.json).

This inventory follows the vendored runtime build configuration. Static-link dead stripping may omit unused portions of a library. Build tools and system packages have their own notices; separately bundled runtime or driver libraries are documented with those bundles.

## AC6Recomp and ReXGlue

The project builds on [sal063/AC6_recomp](https://github.com/sal063/AC6_recomp), Linux work in [Zexyen/AC6_recomp](https://github.com/Zexyen/AC6_recomp), and [ReXGlue](https://github.com/rexglue/rexglue-sdk), including Xenia-derived components.

- [AC6Recomp license](licenses/ac6-recomp/LICENSE): BSD 3-Clause, copyright 2026 rexglue.
- [ReXGlue/Xenia license](licenses/rexglue/LICENSE): BSD 3-Clause, copyright 2026 Tom Clay; portions copyright 2022 Ben Vanik and Xenia project contributors.

The source tree retains the local AC6 and SDK modifications. Individual file notices and the corresponding source distribution provide further attribution.

## FFmpeg and libmspack

This build uses **FFmpeg libavcodec/libavutil** for audio decoding and **libmspack** for LZX decompression. Their use is covered by the GNU Lesser General Public License.

- FFmpeg: [license overview](licenses/ffmpeg/LICENSE.md) and [LGPL version 2.1](licenses/ffmpeg/COPYING.LGPLv2.1). The vendored Linux x86-64 configuration declares LGPL 2.1-or-later, with GPL, version-3-only and nonfree options disabled.
- libmspack: [LGPL version 2.1](licenses/libmspack/COPYING.LIB) and [LZX source notice](licenses/libmspack/lzxd-NOTICE.txt), copyright 2003–2023 Stuart Caie. The compiled `cabextract/mspack/lzxd.c` header specifies LGPL 2.1.

**This software is based in part on the work of the Independent JPEG Group.** FFmpeg's source list includes IJG-derived DCT code. The original notices from [jfdctfst.c](licenses/ffmpeg/IJG-jfdctfst.c-NOTICE.txt), [jfdctint_template.c](licenses/ffmpeg/IJG-jfdctint_template.c-NOTICE.txt), and [jrevdct.c](licenses/ffmpeg/IJG-jrevdct.c-NOTICE.txt) are preserved. Those vendored files were not changed while preparing this release's notices; their existing upstream adaptations remain in the corresponding source.

The corresponding library material is the exact vendored source, including local changes, FFmpeg configuration headers, the `ffmpeg-overlay` inputs, and the CMake build definitions. Library source paths within the source distribution are:

- `thirdparty/rexglue-sdk/thirdparty/FFmpeg/`
- `thirdparty/rexglue-sdk/thirdparty/ffmpeg-overlay/`
- `thirdparty/rexglue-sdk/thirdparty/libmspack/`
- `thirdparty/rexglue-sdk/thirdparty/CMakeLists.txt`

The release's build and relinking instructions identify the matching source and application-object artifacts. For modifications to these libraries, retain the provided notices and follow the relevant license terms. This package imposes no additional prohibition on modification for personal use or reverse engineering for debugging those modifications.

## Other runtime libraries

| Component | License/notice material | Use |
|---|---|---|
| SDL3 | [zlib license](licenses/sdl3/LICENSE.txt) | Input and audio |
| HIDAPI bundled with SDL3 | [license alternatives](licenses/sdl3/hidapi/LICENSE.txt), [BSD-style license](licenses/sdl3/hidapi/LICENSE-bsd.txt), [original license](licenses/sdl3/hidapi/LICENSE-orig.txt) | Controller device access; permissive licensing alternatives are preserved |
| fmt | [license](licenses/fmt/LICENSE) | Formatting |
| spdlog | [MIT license](licenses/spdlog/LICENSE) | Logging |
| SIMDe | [MIT license](licenses/simde/COPYING) | Portable SIMD |
| toml++ | [MIT license](licenses/tomlplusplus/LICENSE) | Configuration |
| UTFCPP | [Boost Software License](licenses/utfcpp/LICENSE) | UTF conversion |
| CLI11 | [BSD 3-Clause license](licenses/cli11/LICENSE) | Command-line parsing |
| Disruptor++ | [MIT license](licenses/disruptorplus/LICENSE.txt) | Thread synchronization |
| aes_128 | [MIT license](licenses/aes_128/LICENSE) | Cryptographic routines |
| o1heap | [MIT license](licenses/o1heap/LICENSE) | Memory allocation |
| xxHash | [BSD 2-Clause license](licenses/xxhash/LICENSE) | Hashing |
| Snappy | [BSD-style license](licenses/snappy/COPYING) | Trace compression |
| Dear ImGui | [MIT license](licenses/imgui/LICENSE.txt) | UI |
| stb components bundled with ImGui | [rectpack](licenses/imgui/imstb_rectpack.h-LICENSE.txt), [textedit](licenses/imgui/imstb_textedit.h-LICENSE.txt), [truetype](licenses/imgui/imstb_truetype.h-LICENSE.txt) | UI packing, editing and font rendering; MIT/public-domain alternatives |
| RenderDoc API header | [MIT notice](licenses/renderdoc/NOTICE.txt) | Capture integration API |
| Volk | [MIT license](licenses/volk/LICENSE.md) | Vulkan function loading |
| Vulkan Memory Allocator | [MIT license](licenses/vulkan-memory-allocator/LICENSE.txt) | Vulkan allocations |
| Vulkan Headers | [license overview](licenses/vulkan-headers/LICENSE.md), [Apache 2.0](licenses/vulkan-headers/LICENSES/Apache-2.0.txt), [MIT](licenses/vulkan-headers/LICENSES/MIT.txt) | Vulkan API definitions |
| SPIRV-Tools | [Apache 2.0 license](licenses/spirv-tools/LICENSE) | SPIR-V tooling |
| SPIRV-Headers | [combined license](licenses/spirv-headers/LICENSE), [MIT](licenses/spirv-headers/LICENSES/MIT.txt), [CC BY 4.0](licenses/spirv-headers/LICENSES/CC-BY-4.0.txt) | SPIR-V definitions and accompanying specification material |
| glslang | [combined licenses](licenses/glslang/LICENSE.txt) | Shader compilation and SPIR-V generation |
| TinySHA1 | [ISC-style notice](licenses/crypto/TinySHA1-NOTICE.txt) | SHA-1; modified for Xenia |
| DES routines | [MIT license](licenses/crypto/des/LICENSE) | Cryptographic routines |
| Rijndael implementation | [public-domain notice](licenses/crypto/Rijndael-NOTICE.txt) | XEX cryptographic routines |
| Stephan Brumme SHA256 implementation | [source attribution and zlib provenance](licenses/crypto/SHA256-NOTICE.txt) | SHA-256; modified for Xenia |

The Disruptor++ notice was absent from the vendored directory. Its MIT license was restored from [Lewis Baker's upstream repository at commit 748e354476e0bf86dfdbb55f1d925222d7ee631b](https://github.com/lewissbaker/disruptorplus/blob/748e354476e0bf86dfdbb55f1d925222d7ee631b/LICENSE.txt), retrieved October 4, 2026. All other notice texts above are verbatim copies or clearly recorded excerpts from the corresponding local source tree.

Game materials supplied separately by the user remain subject to their respective copyrights. These library notices do not grant rights to those materials.

## Privately bundled C/C++ runtime

The executable package includes Arch glibc `2.44+r50+g1848099f063e-1` and GCC libstdc++/libgcc `16.2.1+r23+gd564253eb6c8-1`. They are loaded from the package’s `runtime/` directory and can be replaced with compatible builds. System libraries are not overwritten.

- glibc: [LGPL 2.1](licenses/runtime/glibc/COPYING.LESSERv2), [component notices](licenses/runtime/glibc/LICENSES), and accompanying GPL texts in the same directory.
- GCC runtime: [GPLv3](licenses/runtime/gcc/COPYING3) with [GCC Runtime Library Exception 3.1](licenses/runtime/gcc/COPYING.RUNTIME); additional libstdc++/libbacktrace notices are retained in that directory.

`runtime-sources-20261004.tar.gz` in the same release supplies the exact upstream source commits, Arch packaging recipes and patches, package build metadata, source URLs and hashes. These upstream runtime libraries were copied from their packages without modification. No Mesa driver is bundled.

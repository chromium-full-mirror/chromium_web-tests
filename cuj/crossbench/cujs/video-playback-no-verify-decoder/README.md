# `video-playback-no-verify-decoder` CUJ

## Overview
Benchmarks HTML5 `<video>` and Media Source Extensions (MSE) MPEG-DASH video playback across AV1, H.264, HEVC, VP8, and VP9 codecs, profiles, bit depths, and frame geometries. Unlike `video-playback-verify-hw-decoder` and `video-playback-verify-sw-decoder`, which strictly enforce hardware or software decoding, this suite lets Chrome choose its default platform or software decoder without failing when hardware acceleration is unavailable or falls back to software.

## Variants
The 25 variants span five playback categories:

- **Baseline muted `<video>`**: Direct single-element `<video>` playback (muted) covering 8-bit 320x240 SDR clips (`av1`, `h264`, `hevc`, `vp8`, `vp9`), 10-bit SDR clips (`hevc10`, `vp9_2`), and 10-bit HDR10 (`vp9_hdr`).
- **MSE / MPEG-DASH (`*_mse`)**: Muted MSE playback via Shaka Player (with automatic bitrate adaptation disabled), demuxing separate 320x240 video and audio representations.
- **Odd non-aligned dimensions (`*_odd_dimension`)**: Muted direct `<video>` playback of `321x241` clips whose odd dimensions are not macroblock- or superblock-aligned, exercising visible-rect cropping, 4:2:0 chroma subsampling, and stride alignment.
- **Dynamic mid-stream resolution switching (`*_switch`)**: Muted direct `<video>` playback of single-stream assets stepping across a 7-stage in-stream resolution ladder (`320x240` -> `854x480` -> `1280x800` -> `1904x1008` and back down to `320x240`) to exercise seamless decoder reconfiguration.
- **Unmuted playback (`*_unmuted`)**: Direct `<video>` playback with audio unmuted, exercising Chrome's unmuted playback path alongside audio output and A/V clock synchronization.

| Variant | Config File | Category | Stream Codec, Profile & Geometry |
| :--- | :--- | :--- | :--- |
| `av1` | `av1.page-config.hjson` | Baseline `<video>` | AV1 Main, 8-bit SDR, 320x240 MP4 (muted, video-only) |
| `av1_mse` | `av1_mse.page-config.hjson` | MSE (MPEG-DASH) | AV1 Main, 8-bit SDR, 320x240 MP4 video + AAC-LC audio (muted) |
| `av1_odd_dimension` | `av1_odd_dimension.page-config.hjson` | Odd dimension | AV1 Main, 8-bit SDR, 321x241 non-superblock-aligned MP4 (muted) |
| `av1_switch` | `av1_switch.page-config.hjson` | Resolution switch | AV1 Main, 8-bit SDR, WebM 7-step ladder (`320x240`–`1904x1008`, muted) |
| `av1_unmuted` | `av1_unmuted.page-config.hjson` | Unmuted `<video>` | AV1 Main, 8-bit SDR, 320x240 MP4 (player unmuted, video-only container) |
| `h264` | `h264.page-config.hjson` | Baseline `<video>` | H.264 High, 8-bit SDR, 320x240 MP4 (muted) |
| `h264_mse` | `h264_mse.page-config.hjson` | MSE (MPEG-DASH) | H.264 High, 8-bit SDR, 320x240 MP4 video + AAC-LC audio (muted) |
| `h264_switch` | `h264_switch.page-config.hjson` | Resolution switch | H.264 Constrained Baseline, 8-bit SDR, MP4 7-step ladder (`320x240`–`1904x1008`, muted) |
| `h264_unmuted` | `h264_unmuted.page-config.hjson` | Unmuted `<video>` | H.264 High, 8-bit SDR, 320x240 MP4 + active AAC-LC audio |
| `hevc` | `hevc.page-config.hjson` | Baseline `<video>` | HEVC Main, 8-bit SDR, 320x240 MP4 (muted) |
| `hevc10` | `hevc10.page-config.hjson` | Baseline `<video>` (10-bit) | HEVC Main 10, 10-bit SDR, 320x240 MP4 (muted) |
| `hevc_mse` | `hevc_mse.page-config.hjson` | MSE (MPEG-DASH) | HEVC Main, 8-bit SDR, 320x240 MP4 video + AAC-LC audio (muted) |
| `hevc_switch` | `hevc_switch.page-config.hjson` | Resolution switch | HEVC Main, 8-bit SDR, MP4 7-step ladder (`320x240`–`1904x1008`, muted) |
| `vp8` | `vp8.page-config.hjson` | Baseline `<video>` | VP8 Profile 0, 8-bit SDR, 320x240 WebM (muted) |
| `vp8_mse` | `vp8_mse.page-config.hjson` | MSE (MPEG-DASH) | VP8 Profile 0, 8-bit SDR, 320x240 WebM video + Vorbis audio (muted) |
| `vp8_odd_dimension` | `vp8_odd_dimension.page-config.hjson` | Odd dimension | VP8 Profile 0, 8-bit SDR, 321x241 non-macroblock-aligned WebM (muted) |
| `vp8_switch` | `vp8_switch.page-config.hjson` | Resolution switch | VP8 Profile 0, 8-bit SDR, WebM 7-step ladder (`320x240`–`1904x1008`, muted) |
| `vp8_unmuted` | `vp8_unmuted.page-config.hjson` | Unmuted `<video>` | VP8 Profile 0, 8-bit SDR, 320x240 WebM + active Vorbis audio |
| `vp9` | `vp9.page-config.hjson` | Baseline `<video>` | VP9 Profile 0, 8-bit SDR, 320x240 WebM (muted) |
| `vp9_2` | `vp9_2.page-config.hjson` | Baseline `<video>` (10-bit) | VP9 Profile 2, 10-bit SDR, 320x240 WebM (muted) |
| `vp9_hdr` | `vp9_hdr.page-config.hjson` | Baseline `<video>` (HDR10) | VP9 Profile 2, 10-bit HDR10 (BT.2020 / PQ), 1280x720 WebM (muted) |
| `vp9_mse` | `vp9_mse.page-config.hjson` | MSE (MPEG-DASH) | VP9 Profile 0, 8-bit SDR, 320x240 WebM video + Opus audio (muted) |
| `vp9_odd_dimension` | `vp9_odd_dimension.page-config.hjson` | Odd dimension | VP9 Profile 0, 8-bit SDR, 321x241 non-superblock-aligned WebM (muted) |
| `vp9_switch` | `vp9_switch.page-config.hjson` | Resolution switch | VP9 Profile 0, 8-bit SDR, WebM 7-step ladder (`320x240`–`1904x1008`, muted) |
| `vp9_unmuted` | `vp9_unmuted.page-config.hjson` | Unmuted `<video>` | VP9 Profile 0, 8-bit SDR, 320x240 WebM + active Opus audio |

## Workflow
- **Prerequisites & Setup**: Requires live network access to the public GCS test asset bucket (`https://storage.googleapis.com/chromiumos-test-assets-public/tast/cros/video/`); no account login, local server, or WPR archive is used. Browser startup configuration permits gestureless autoplay and disables small-resolution software-decode heuristics so 320x240 streams remain eligible for hardware decode without forcing either decoder path.
- **Main Actions**: Navigates to either the direct HTML5 `<video>` harness or the Shaka Player MSE harness (with ABR disabled), starts playback muted or unmuted per variant, waits until the media stream reaches `ended`, emits dropped-frame User Timing marks from `getVideoPlaybackQuality()`, and passively records whether a platform hardware decoder was used at run completion without asserting it.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Never enforce hardware or software decoding**: Do not add strict hardware/software decoder assertions or forced software-decode flags; Chrome's default decoder choice must succeed on both hardware-accelerated and software-fallback devices, while still running a real `<video>` decode session so passive acceleration telemetry can query decoder properties at run stop.
- **Preserve codec, bit-depth, HDR, and geometry fidelity**: Keep each variant's exact codec profile, 10-bit pixel depth (`hevc10`, `vp9_2`), BT.2020/PQ HDR10 transfer (`vp9_hdr` at 1280x720), odd `321x241` non-aligned dimensions (`*_odd_dimension`), or 7-step mid-stream resolution ladder (`*_switch`).
- **Keep direct `<video>` vs. MSE delivery distinct**: Do not substitute direct `<video src>` playback on `*_mse` variants or vice versa, and keep ABR disabled on MSE runs so playback remains deterministic. Note that the direct `<video>` harness relies on quirks-mode case-insensitive class matching (`class="videoTile"` matched by `.videotile`).
- **Maintain muted vs. unmuted audio separation**: Keep muted variants muted to isolate video decode/compositing, and keep `*_unmuted` variants actively unmuted (with gestureless autoplay enabled) to exercise audio output and A/V clock synchronization.
- **Preserve dropped-frame User Timing marks**: Always wait for full stream completion (`ended`) before reading `getVideoPlaybackQuality()` and emitting the `dropped-frames-count` and `dropped-frames-percent` `performance.mark` entries (`detail` payload) consumed by the dropped-frames trace metrics.

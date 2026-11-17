# `video-playback-verify-hw-decoder` CUJ

## Overview
Benchmarks muted HTML5 and Media Source Extensions (MSE) video playback across AV1, H.264, HEVC, VP8, and VP9 streams while strictly asserting that Chromium decodes every stream with a platform hardware video decoder. Covers standard 8-bit SDR clips, 10-bit profiles (HEVC Main 10 and VP9 Profile 2), 10-bit HDR10 (PQ/BT.2020), Shaka Player MPEG-DASH streaming, odd non-macroblock-aligned dimensions (`321x241`), and dynamic mid-stream resolution switching. Captures dropped-frame playback smoothness and system resource telemetry on a verified hardware decode path.

## Variants
The 21 variants span four delivery and geometry categories across five codec families:
- **Direct `<video>` baselines & 10-bit/HDR (`*_hw`, `hevc10_hw`, `vp9_2_hw`, `vp9_hdr_hw`)**: Progressive MP4 or WebM playback covering `320x240` 8-bit SDR baselines, `320x240` 10-bit profiles, and `1280x720` 10-bit HDR10 (PQ/BT.2020).
- **MPEG-DASH MSE (`*_mse_hw`)**: Streams demuxed video and audio tracks into an MSE `SourceBuffer` via Shaka Player with adaptive bitrate switching disabled.
- **Odd dimensions (`*_odd_dimension_hw`)**: Direct `321x241` clips exercising hardware decoder stride alignment, padding, and visible-rect cropping on non-even dimensions.
- **Dynamic resolution switch (`*_switch_hw`)**: Direct streams that step through 7 in-stream resolutions (`320x240 -> 854x480 -> 1280x800 -> 1904x1008 -> 1280x800 -> 854x480 -> 320x240`) to exercise mid-stream hardware decoder surface reallocation without falling back to software decode.

| Variant | Config File | Delivery Mode | Codec, Profile & Geometry |
| :--- | :--- | :--- | :--- |
| `av1_hw` | `av1_hw.page-config.hjson` | Direct `<video>` (MP4) | AV1 Main, 8-bit SDR, `320x240` |
| `av1_mse_hw` | `av1_mse_hw.page-config.hjson` | Shaka MPEG-DASH MSE (MP4) | AV1 Main, 8-bit SDR video + AAC audio, `320x240` |
| `av1_odd_dimension_hw` | `av1_odd_dimension_hw.page-config.hjson` | Direct `<video>` (MP4) | AV1 Main, 8-bit SDR, odd `321x241` |
| `av1_switch_hw` | `av1_switch_hw.page-config.hjson` | Direct `<video>` (WebM) | AV1 Main, 8-bit SDR, 7-step resolution ladder (`320x240`..`1904x1008`) |
| `h264_hw` | `h264_hw.page-config.hjson` | Direct `<video>` (MP4) | H.264 High, 8-bit SDR, `320x240` |
| `h264_mse_hw` | `h264_mse_hw.page-config.hjson` | Shaka MPEG-DASH MSE (MP4) | H.264 High, 8-bit SDR video + AAC audio, `320x240` |
| `h264_switch_hw` | `h264_switch_hw.page-config.hjson` | Direct `<video>` (MP4) | H.264 Constrained Baseline, 8-bit SDR, 7-step resolution ladder (`320x240`..`1904x1008`) |
| `hevc_hw` | `hevc_hw.page-config.hjson` | Direct `<video>` (MP4) | HEVC Main, 8-bit SDR, `320x240` |
| `hevc10_hw` | `hevc10_hw.page-config.hjson` | Direct `<video>` (MP4) | HEVC Main 10, 10-bit, `320x240` |
| `hevc_mse_hw` | `hevc_mse_hw.page-config.hjson` | Shaka MPEG-DASH MSE (MP4) | HEVC Main, 8-bit SDR video + AAC audio, `320x240` |
| `hevc_switch_hw` | `hevc_switch_hw.page-config.hjson` | Direct `<video>` (MP4) | HEVC Main, 8-bit SDR, 7-step resolution ladder (`320x240`..`1904x1008`) |
| `vp8_hw` | `vp8_hw.page-config.hjson` | Direct `<video>` (WebM) | VP8 Profile 0, 8-bit SDR, `320x240` |
| `vp8_mse_hw` | `vp8_mse_hw.page-config.hjson` | Shaka MPEG-DASH MSE (WebM) | VP8 Profile 0, 8-bit SDR video + Vorbis audio, `320x240` |
| `vp8_odd_dimension_hw` | `vp8_odd_dimension_hw.page-config.hjson` | Direct `<video>` (WebM) | VP8 Profile 0, 8-bit SDR, odd `321x241` |
| `vp8_switch_hw` | `vp8_switch_hw.page-config.hjson` | Direct `<video>` (WebM) | VP8 Profile 0, 8-bit SDR, 7-step resolution ladder (`320x240`..`1904x1008`) |
| `vp9_hw` | `vp9_hw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 0, 8-bit SDR, `320x240` |
| `vp9_2_hw` | `vp9_2_hw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 2, 10-bit, `320x240` |
| `vp9_hdr_hw` | `vp9_hdr_hw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 2, 10-bit HDR10 (SMPTE ST 2084 PQ / BT.2020), `1280x720` |
| `vp9_mse_hw` | `vp9_mse_hw.page-config.hjson` | Shaka MPEG-DASH MSE (WebM) | VP9 Profile 0, 8-bit SDR video + Opus audio, `320x240` |
| `vp9_odd_dimension_hw` | `vp9_odd_dimension_hw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 0, 8-bit SDR, odd `321x241` |
| `vp9_switch_hw` | `vp9_switch_hw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 0, 8-bit SDR, 7-step resolution ladder (`320x240`..`1904x1008`) |

## Workflow
- **Prerequisites & Setup**: Requires live network access to `https://storage.googleapis.com/chromiumos-test-assets-public/tast/cros/video/` (no login account, local server, or WPR archive is used) and target hardware/GPU decode support for the tested codec, bit depth, and profile. Chrome launches with gestureless autoplay enabled and with small-resolution software-fallback heuristics and GPU driver bug workarounds disabled so `320x240` and `321x241` clips remain eligible for hardware decode; Perfetto tracing and the `video_acceleration` probe attach before playback begins.
- **Main Actions**: Opens either the direct HTML5 `<video>` harness or the Shaka Player MPEG-DASH MSE harness (with ABR disabled), plays the muted video stream through to completion, invokes the `video_acceleration` probe to assert that a platform hardware video decoder was used, and reads `getVideoPlaybackQuality()` to emit dropped-frame User Timing marks.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Mandatory hardware decoder assertion**: Never remove, bypass, or invert the `video_acceleration` hardware-decode check—or fall back to software/unverified decoding—to make a failing device or codec variant pass.
- **Stream codec, bit-depth, HDR, and geometry fidelity**: Preserve each variant's exact media characteristics: keep 10-bit streams (`hevc10_hw`, `vp9_2_hw`), 10-bit HDR10 PQ/BT.2020 `1280x720` (`vp9_hdr_hw`), odd `321x241` alignment clips (`*_odd_dimension_hw`), and 7-step dynamic resolution-switching clips (`*_switch_hw`) intact rather than substituting standard 8-bit SDR fixed-resolution clips.
- **Delivery path & quirks-mode DOM**: Keep direct `<video>` playback distinct from Shaka MSE (`*_mse_hw`) `SourceBuffer` streaming, keep playback muted, and note that the direct HTML5 harness omits `<!DOCTYPE html>` (quirks mode, where `.videotile` matches `<video class="videoTile">` case-insensitively).
- **Dropped-frame User Timing contract**: Keep post-playback emission of the `dropped-frames-count` and `dropped-frames-percent` User Timing marks (`blink.user_timing`) after playback reaches `.ended` so downstream trace metrics remain populated.

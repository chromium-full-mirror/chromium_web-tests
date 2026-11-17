# `video-playback-verify-sw-decoder` CUJ

## Overview
Benchmarks muted direct HTML5 `<video>` playback across AV1, H.264, VP8, and VP9 streams with hardware video decoding disabled, strictly asserting that Chromium decodes every stream through its non-platform software video decoder pipeline. Covers `320x240` 8-bit SDR baselines, `320x240` 10-bit VP9 Profile 2, and `1280x720` 10-bit HDR10 (PQ/BT.2020) VP9 Profile 2. Measures dropped-frame playback smoothness and CPU/memory telemetry on a verified software decode path.

## Variants
All 6 variants use direct progressive HTML5 `<video>` playback (there are no MSE, odd-dimension, or resolution-switching variants in this CUJ), varying codec family, bit depth, color transfer, and resolution:

| Variant | Config File | Delivery Mode | Codec, Profile & Geometry |
| :--- | :--- | :--- | :--- |
| `av1_sw` | `av1_sw.page-config.hjson` | Direct `<video>` (MP4) | AV1 Main, 8-bit SDR, `320x240` |
| `h264_sw` | `h264_sw.page-config.hjson` | Direct `<video>` (MP4) | H.264 High, 8-bit SDR, `320x240` |
| `vp8_sw` | `vp8_sw.page-config.hjson` | Direct `<video>` (WebM) | VP8 Profile 0, 8-bit SDR, `320x240` |
| `vp9_sw` | `vp9_sw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 0, 8-bit SDR, `320x240` |
| `vp9_2_sw` | `vp9_2_sw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 2, 10-bit, `320x240` |
| `vp9_hdr_sw` | `vp9_hdr_sw.page-config.hjson` | Direct `<video>` (WebM) | VP9 Profile 2, 10-bit HDR10 (SMPTE ST 2084 PQ / BT.2020), `1280x720` |

## Workflow
- **Prerequisites & Setup**: Requires live network access to `https://storage.googleapis.com/chromiumos-test-assets-public/tast/cros/video/` (no login account, local server, or WPR archive is used). Chrome launches with gestureless autoplay enabled and hardware-accelerated video decoding explicitly disabled so every stream is forced onto Chromium's built-in software decoders regardless of host GPU capabilities; Perfetto tracing and the `video_acceleration` probe attach before playback begins.
- **Main Actions**: Opens the direct HTML5 `<video>` harness, plays the muted video clip through to completion, invokes the `video_acceleration` probe to assert that software decoding (non-platform decoder) was used, and reads `getVideoPlaybackQuality()` to emit dropped-frame User Timing marks.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Mandatory software decoder enforcement & assertion**: Never re-enable hardware video decoding in browser flags, and never remove, bypass, or invert the `video_acceleration` software-decode assertion to make a failing test pass.
- **Stream codec, bit-depth, and HDR fidelity**: Preserve each variant's intended codec, profile, bit depth, and color space—specifically keeping 10-bit VP9 Profile 2 (`vp9_2_sw`) and 10-bit HDR10 PQ/BT.2020 `1280x720` (`vp9_hdr_sw`) distinct from 8-bit SDR `vp9_sw`.
- **Direct playback & quirks-mode DOM**: Keep muted direct `<video>` playback and note that the HTML5 video harness omits `<!DOCTYPE html>` (quirks mode, where `.videotile` matches `<video class="videoTile">` case-insensitively).
- **Dropped-frame User Timing contract**: Keep post-playback emission of the `dropped-frames-count` and `dropped-frames-percent` User Timing marks (`blink.user_timing`) after playback reaches `.ended` so downstream trace metrics remain populated.

# `video-seek` CUJ

## Overview
The `video-seek` CUJ benchmarks HTML5 `<video>` random-seek latency and seek completion reliability across unencrypted media streams. Variants evaluate five video codecs under baseline single-resolution seeking, high-iteration stress seeking, and mid-stream dynamic resolution changes, in both error-tolerant benchmarking and strict seek-completion verification modes.

## Variants
All **30 variants** span three orthogonal axes (`3 seek modes x 5 codecs x 2 verification modes`):

- **Seek Mode**:
  - **Standard (`<codec>`)**: 25 deterministic pseudo-random seeks within a fixed-resolution 720p video stream.
  - **Stress (`stress_<codec>`)**: 1000 consecutive deterministic pseudo-random seeks on the same 720p stream to stress sustained seek latency and decoder flush/reset stability.
  - **Resolution-switch (`switch_<codec>`)**: 25 deterministic pseudo-random seeks across an in-stream SMPTE-bars resolution-ladder video whose frame dimensions change mid-stream, exercising dynamic decoder reconfiguration during seeks.
- **Codec**: **AV1**, **H.264/AVC**, **HEVC/H.265**, **VP8**, and **VP9** (in MP4 or WebM containers; AV1 uses MP4 for standard/stress and WebM for `switch_*`).
- **Verification**: Unverified variants tolerate early seek failures so partial runs still report seek completion rate, whereas **`-verify`** variants fail the test unless **100% of target seeks complete**. Note that unlike `video-playback` verification suites, `-verify` here checks **functional seek completion**, *not* hardware decoder acceleration.

| Variant | Config File | Seek Mode | Codec | Seek Count | Verification |
| :--- | :--- | :--- | :--- | ---: | :--- |
| `av1` | `av1.page-config.hjson` | Standard (720p) | AV1 (MP4) | 25 | Unverified |
| `av1-verify` | `av1-verify.page-config.hjson` | Standard (720p) | AV1 (MP4) | 25 | 100% seek completion |
| `h264` | `h264.page-config.hjson` | Standard (720p) | H.264/AVC (MP4) | 25 | Unverified |
| `h264-verify` | `h264-verify.page-config.hjson` | Standard (720p) | H.264/AVC (MP4) | 25 | 100% seek completion |
| `hevc` | `hevc.page-config.hjson` | Standard (720p) | HEVC/H.265 (MP4) | 25 | Unverified |
| `hevc-verify` | `hevc-verify.page-config.hjson` | Standard (720p) | HEVC/H.265 (MP4) | 25 | 100% seek completion |
| `vp8` | `vp8.page-config.hjson` | Standard (720p) | VP8 (WebM) | 25 | Unverified |
| `vp8-verify` | `vp8-verify.page-config.hjson` | Standard (720p) | VP8 (WebM) | 25 | 100% seek completion |
| `vp9` | `vp9.page-config.hjson` | Standard (720p) | VP9 (WebM) | 25 | Unverified |
| `vp9-verify` | `vp9-verify.page-config.hjson` | Standard (720p) | VP9 (WebM) | 25 | 100% seek completion |
| `stress_av1` | `stress_av1.page-config.hjson` | Stress (720p) | AV1 (MP4) | 1000 | Unverified |
| `stress_av1-verify` | `stress_av1-verify.page-config.hjson` | Stress (720p) | AV1 (MP4) | 1000 | 100% seek completion |
| `stress_h264` | `stress_h264.page-config.hjson` | Stress (720p) | H.264/AVC (MP4) | 1000 | Unverified |
| `stress_h264-verify` | `stress_h264-verify.page-config.hjson` | Stress (720p) | H.264/AVC (MP4) | 1000 | 100% seek completion |
| `stress_hevc` | `stress_hevc.page-config.hjson` | Stress (720p) | HEVC/H.265 (MP4) | 1000 | Unverified |
| `stress_hevc-verify` | `stress_hevc-verify.page-config.hjson` | Stress (720p) | HEVC/H.265 (MP4) | 1000 | 100% seek completion |
| `stress_vp8` | `stress_vp8.page-config.hjson` | Stress (720p) | VP8 (WebM) | 1000 | Unverified |
| `stress_vp8-verify` | `stress_vp8-verify.page-config.hjson` | Stress (720p) | VP8 (WebM) | 1000 | 100% seek completion |
| `stress_vp9` | `stress_vp9.page-config.hjson` | Stress (720p) | VP9 (WebM) | 1000 | Unverified |
| `stress_vp9-verify` | `stress_vp9-verify.page-config.hjson` | Stress (720p) | VP9 (WebM) | 1000 | 100% seek completion |
| `switch_av1` | `switch_av1.page-config.hjson` | Resolution-switch | AV1 (WebM) | 25 | Unverified |
| `switch_av1-verify` | `switch_av1-verify.page-config.hjson` | Resolution-switch | AV1 (WebM) | 25 | 100% seek completion |
| `switch_h264` | `switch_h264.page-config.hjson` | Resolution-switch | H.264/AVC (MP4) | 25 | Unverified |
| `switch_h264-verify` | `switch_h264-verify.page-config.hjson` | Resolution-switch | H.264/AVC (MP4) | 25 | 100% seek completion |
| `switch_hevc` | `switch_hevc.page-config.hjson` | Resolution-switch | HEVC/H.265 (MP4) | 25 | Unverified |
| `switch_hevc-verify` | `switch_hevc-verify.page-config.hjson` | Resolution-switch | HEVC/H.265 (MP4) | 25 | 100% seek completion |
| `switch_vp8` | `switch_vp8.page-config.hjson` | Resolution-switch | VP8 (WebM) | 25 | Unverified |
| `switch_vp8-verify` | `switch_vp8-verify.page-config.hjson` | Resolution-switch | VP8 (WebM) | 25 | 100% seek completion |
| `switch_vp9` | `switch_vp9.page-config.hjson` | Resolution-switch | VP9 (WebM) | 25 | Unverified |
| `switch_vp9-verify` | `switch_vp9-verify.page-config.hjson` | Resolution-switch | VP9 (WebM) | 25 | 100% seek completion |

## Workflow
- **Prerequisites & Setup**: Requires live network access to `https://storage.googleapis.com/chromiumos-test-assets-public/tast/cros/video/` to load the hosted HTML player and video clips (no account login or WPR archive is used).
- **Main Actions**: Opens the hosted test video page, starts muted looped playback of the target video asset, and executes the target number of deterministic seeded pseudo-random seeks, waiting for each `seeked` event before issuing the next seek while recording per-seek User Timing duration marks. For `-verify` variants, the run fails if fewer than all target seeks complete.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Deterministic sequential seeking**: Keep seeks driven by a fixed pseudo-random seed and awaited sequentially on each `seeked` event (never overlapping seeks) so target timestamps and seek counts remain reproducible across runs.
- **Single-resolution vs. mid-stream resolution-ladder assets**: Preserve fixed-resolution 720p clips for standard and `stress_*` variants, and in-stream SMPTE resolution-ladder clips for `switch_*` variants so seeks continue to cross mid-stream resolution boundaries.
- **Completion verification vs. hardware-decode checks**: Preserve the distinction between `-verify` variants (which assert 100% seek completion) and unverified variants (which allow partial completion to be captured by metrics without failing). Do **not** add hardware-decoder acceleration assertions when healing (`-verify` in `video-seek` validates seek completion only).
- **Hosted page quirks-mode `.videotile` selector**: The hosted test HTML omits a `<!DOCTYPE>`, so the lowercase `.videotile` selector matches `<video class="videoTile">` via quirks-mode case-insensitive CSS matching. Preserve single-video muted looped playback, and use case-exact `.videoTile` if healing against a standards-mode DOM.
- **User Timing marks for trace metrics**: Average seek time (`cuj.video-seek.avg_seek_time_s`) and seek completion percentage (`cuj.video-seek.seek_completion_percentage`) are derived from the `test-config` User Timing mark (carrying `numTargetSeeks` in its detail payload) and per-seek `randomSeek-*-duration` User Timing measures. Preserve these exact event names and payload structure.

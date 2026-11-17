# `tiktok` CUJ

## Overview
Benchmarks online social video streaming playback on TikTok Web. Across 4 variants, it evaluates steady-state 720p video decoding efficiency, rendered resolution, and dropped video frames across default in-page and fullscreen player views at 30fps and 60fps.

## Variants
Variants span two axes: **player view mode** (default in-page desktop web player vs. browser fullscreen) × **frame rate & playback window** (720p @ 30fps for 50 seconds vs. 720p @ 60fps for 120 seconds, using dedicated public test videos).

| Variant | Config File | Player View | Target Resolution & Frame Rate | Playback Window |
| :--- | :--- | :--- | :--- | :--- |
| `default-720p-30fps` | `default-720p-30fps.page-config.hjson` | Default in-page | 720p @ 30fps | 50s |
| `default-720p-60fps` | `default-720p-60fps.page-config.hjson` | Default in-page | 720p @ 60fps | 120s |
| `fullscreen-720p-30fps` | `fullscreen-720p-30fps.page-config.hjson` | Fullscreen mode | 720p @ 30fps | 50s |
| `fullscreen-720p-60fps` | `fullscreen-720p-60fps.page-config.hjson` | Fullscreen mode | 720p @ 60fps | 120s |

## Workflow
- **Prerequisites & Setup**: Requires live internet access to `tiktok.com` (no WPR archive). Runs unauthenticated as a guest without a TikTok login; guest sessions may encounter an optional dismissible prompt/verification overlay on initial load. Launches the browser in desktop-site mode with autoplay allowed and notifications suppressed.
- **Main Actions**:
  1. Navigates directly to the dedicated 720p 30fps or 60fps TikTok test video and dismisses any optional closeable guest overlay if present.
  2. Leaves the player in its default in-page web layout (`default-*` variants) or opens the player's more-options menu to enter and verify browser fullscreen mode (`fullscreen-*` variants).
  3. Confirms active video playback, streams for the variant's full playback window (50s for 30fps; 120s for 60fps), and records HTML5 video playback quality statistics (elapsed time, decoded dimensions, total frames, and dropped frames).
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Clip duration must exceed the measured playback window**: Keep dedicated 720p 30fps and 60fps test videos whose runtime is strictly longer than the measured playback window (50s and 120s, respectively). Because TikTok auto-loops finished videos, a shorter clip would wrap around and reset `currentTime` to `0` mid-run, failing the end-of-run playback duration check.
- **Player view mode**: Keep `default-*` variants in TikTok's standard in-page layout and ensure `fullscreen-*` variants enter true browser fullscreen before timed playback starts.
- **Native touch input & guest overlay handling**: Use native touch input for all UI clicks; keep guest overlay dismissal strictly optional and never attempt to solve or bypass an interactive CAPTCHA challenge.
- **User Timing streaming metrics**: Preserve the `video-started` and `streaming-stats` User Timing (`performance.mark`) events—including the minimum playback duration assertion and the detail payload (`currentTime`, `videoWidth`, `videoHeight`, `totalVideoFrames`, `droppedVideoFrames`)—consumed by trace-based streaming metrics.

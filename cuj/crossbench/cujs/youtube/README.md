# `youtube` CUJ

## Overview
Benchmarks sustained foreground online video streaming on YouTube without concurrent browsing or background tab activity. Across 12 variants, it evaluates steady-state video decoding efficiency, rendered resolution, and frame-drop behavior across combinations of player view mode, target resolution, and frame rate over a 2-minute playback window.

## Variants
Variants span three axes: **player view mode** (default in-page, theater, or fullscreen) × **target resolution** (1080p or 4K / 2160p) × **frame rate** (30fps or 60fps, each backed by a matching 30fps or 60fps YouTube source video).

| Variant | Config File | Player View | Target Resolution & Frame Rate |
| :--- | :--- | :--- | :--- |
| `default-1080p-30fps` | `default-1080p-30fps.page-config.hjson` | Default in-page | 1080p (1920×1080) @ 30fps |
| `default-1080p-60fps` | `default-1080p-60fps.page-config.hjson` | Default in-page | 1080p (1920×1080) @ 60fps |
| `default-4k-30fps` | `default-4k-30fps.page-config.hjson` | Default in-page | 4K / 2160p (3840×2160) @ 30fps |
| `default-4k-60fps` | `default-4k-60fps.page-config.hjson` | Default in-page | 4K / 2160p (3840×2160) @ 60fps |
| `theater-1080p-30fps` | `theater-1080p-30fps.page-config.hjson` | Theater mode | 1080p (1920×1080) @ 30fps |
| `theater-1080p-60fps` | `theater-1080p-60fps.page-config.hjson` | Theater mode | 1080p (1920×1080) @ 60fps |
| `theater-4k-30fps` | `theater-4k-30fps.page-config.hjson` | Theater mode | 4K / 2160p (3840×2160) @ 30fps |
| `theater-4k-60fps` | `theater-4k-60fps.page-config.hjson` | Theater mode | 4K / 2160p (3840×2160) @ 60fps |
| `fullscreen-1080p-30fps` | `fullscreen-1080p-30fps.page-config.hjson` | Fullscreen mode | 1080p (1920×1080) @ 30fps |
| `fullscreen-1080p-60fps` | `fullscreen-1080p-60fps.page-config.hjson` | Fullscreen mode | 1080p (1920×1080) @ 60fps |
| `fullscreen-4k-30fps` | `fullscreen-4k-30fps.page-config.hjson` | Fullscreen mode | 4K / 2160p (3840×2160) @ 30fps |
| `fullscreen-4k-60fps` | `fullscreen-4k-60fps.page-config.hjson` | Fullscreen mode | 4K / 2160p (3840×2160) @ 60fps |

## Workflow
- **Prerequisites & Setup**: Requires live internet access (no WPR archive) and a signed-in Google test account provisioned with **YouTube Premium** so ads do not interrupt playback or alter player controls. To add YouTube Premium to your test account, follow the instructions at go/ypc-inspector-user-instruction. Launches the browser in desktop-site mode with autoplay allowed and notifications suppressed.
- **Main Actions**:
  1. Navigates to the variant's 30fps or 60fps YouTube test video, completes sign-in if the session did not propagate automatically, waits for initial playback, and pauses/rewinds the video to the start.
  2. Opens the YouTube player Settings → Quality menu to explicitly lock the target resolution and frame rate, then sets the player view mode (staying in default view, or switching to theater or fullscreen via keyboard shortcut).
  3. Resumes playback, streams uninterrupted in the foreground for 120 seconds, and records HTML5 video playback quality statistics (elapsed time, decoded dimensions, total frames, and dropped frames).
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Explicit quality lock (never `Auto`)**: Always lock the YouTube player Quality setting to the variant's exact target resolution and frame rate before starting timed playback rather than relying on adaptive `Auto` quality.
- **Matched 30fps vs. 60fps source assets & ad-free playback**: Keep 30fps and 60fps variants paired with source videos encoded at the corresponding frame rate, and always run with an active YouTube Premium test account (go/ypc-inspector-user-instruction) so ad streams never replace the benchmarked video.
- **Player view mode**: Preserve each variant's intended layout (default in-page player, wide theater mode, or browser fullscreen) throughout the timed playback window.
- **Native input events**: Trigger player menu interactions and view-mode shortcuts via native touch and keyboard input rather than synthetic JavaScript clicks.
- **User Timing streaming metrics**: Preserve the `video-started` and `streaming-stats` User Timing (`performance.mark`) events—including the assertion that playback reached the full 120-second duration and the detail payload reporting `currentTime`, `videoWidth`, `videoHeight`, `totalVideoFrames`, and `droppedVideoFrames`—used by trace-based streaming metrics.

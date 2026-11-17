# `youtube-watch-browse` CUJ

## Overview
Benchmarks multitasking online video streaming on YouTube while concurrently loading and scrolling a heavy web page in a second browser window. Across 12 variants, it configures YouTube across player view modes, target resolutions, and frame rates before shifting foreground focus to browse and scroll the single-page HTML Living Standard (`https://html.spec.whatwg.org/`). It evaluates sustained unfocused video decoding, frame-drop resilience, and touch-scrolling responsiveness under combined media and DOM/layout load.

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
- **Prerequisites & Setup**: Requires live internet access (no WPR archive) and a signed-in Google test account provisioned with **YouTube Premium** so ads do not interrupt playback or alter player controls; see go/ypc-inspector-user-instruction to enable YouTube Premium on the test account. Launches the browser in desktop-site mode with autoplay allowed, notifications suppressed, and background media suspension disabled so YouTube continues decoding video while unfocused.
- **Main Actions**:
  1. Navigates to the variant's 30fps or 60fps YouTube test video, completes sign-in if needed, waits for initial playback, and pauses/rewinds the video to the start.
  2. Locks the target resolution and frame rate in the YouTube player Quality menu, sets the player view mode (default, theater, or fullscreen), and resumes video playback.
  3. Opens `https://html.spec.whatwg.org/` in a second browser window while YouTube continues playing and performs 6 consecutive multi-step touch-scrolling passes down the page.
  4. Switches focus back to the YouTube tab and collects HTML5 video playback quality statistics (elapsed time, decoded dimensions, total frames, and dropped frames).
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Explicit quality lock (never `Auto`)**: Always lock the YouTube player Quality setting to the variant's exact target resolution and frame rate rather than leaving YouTube on `Auto`.
- **Matched 30fps vs. 60fps source assets & ad-free playback**: Keep 30fps and 60fps variants paired with corresponding 30fps/60fps source videos, and run with a YouTube Premium test account (go/ypc-inspector-user-instruction) so ads never interrupt playback.
- **Player view mode & active background video decoding**: Preserve each variant's player view mode (default, theater, or fullscreen) and ensure background media suspension remains disabled so YouTube continues decoding video frames while the secondary browsing window is focused.
- **Concurrent secondary-window browsing & native input**: Preserve opening the heavy HTML spec page in a separate browser window, performing the multi-pass native touch-scrolling workload, and switching back to the YouTube tab before reading playback stats. Use native touch and keyboard input rather than synthetic JavaScript events.
- **User Timing streaming & scroll marks**: Preserve the `video-started` and `streaming-stats` User Timing (`performance.mark`) events (`currentTime`, `videoWidth`, `videoHeight`, `totalVideoFrames`, `droppedVideoFrames`) as well as the scroll start/end timing marks used by trace metrics.

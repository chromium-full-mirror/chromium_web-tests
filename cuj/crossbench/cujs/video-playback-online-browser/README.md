# `video-playback-online-browser` CUJ

## Overview
Benchmarks online HTML5 video playback in the browser using the hosted CrosVideo test player (`https://crosvideo.appspot.com/`). It streams a looped 1080p 60fps VP9 video in a standard in-page `<video>` element over a ~70-second window, isolating browser media pipeline and hardware/software VP9 decoding performance from third-party streaming site UI churn.

## Variants
This CUJ defines a single default variant testing looped 1080p 60fps VP9 playback in the standard browser viewport.

| Variant | Config File | Player View | Target Stream |
| :--- | :--- | :--- | :--- |
| `default` | `page-config.hjson` | Default in-page | 1080p @ 60fps VP9 (looped, ~70s) |

## Workflow
- **Prerequisites & Setup**: Requires live internet access to `https://crosvideo.appspot.com/` (runs unauthenticated without a login account or WPR archive). Launches the browser in desktop-site mode with autoplay allowed.
- **Main Actions**:
  1. Navigates to the hosted CrosVideo player configured for 1080p 60fps VP9 looped playback and waits for the video element and stream buffer to become ready.
  2. Starts playback via script, recording initial readiness timing and pausing automatically once playback progresses past ~70 seconds.
  3. Reads HTML5 video playback quality counters at the end of the ~70-second playback window to record total dropped frames and dropped-frame percentage.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Stream codec, resolution & frame rate**: Preserve the 1080p, 60fps, VP9, and looped playback configuration on CrosVideo in the standard in-page player view.
- **Synchronized playback measurement window**: Keep the script-driven ~70-second playback cutoff aligned with the Crossbench wait duration so frame-drop counters are sampled after a consistent ~1-minute active playback window.
- **User Timing dropped-frame & playback marks**: Preserve the User Timing (`performance.mark` / `performance.measure`) events emitted for dropped-frame metrics (`dropped-frames-count` and `dropped-frames-percent`) and playback lifecycle milestones (`page-loaded`, `video-start`, `video-ready`, `video-stop`, `video-duration`) consumed by trace metrics.

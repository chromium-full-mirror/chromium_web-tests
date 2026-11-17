# `videocall-scroll` CUJ

## Overview
Benchmarks native touch-scrolling smoothness, scroll distance, and input latency across a massive DOM document—the single-page WHATWG HTML Living Standard specification—while a high-preset WebRTC videocall plays concurrently in a separate window. Comparing the baseline and perceptible-CPU variants isolates how foreground CPU contention affects compositor frame production and scroll jank during active WebRTC video playback.

## Variants
Variants differ by whether an unoccluded perceptible CPU-load window runs alongside the WebRTC call and scrolling windows.

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Baseline 2-window run (WebRTC videocall window + WHATWG HTML spec scrolling window) with no synthetic CPU load. |
| `with-perceptible-cpu` | `with-perceptible-cpu.page-config.hjson` | 3-window run adding an unoccluded window of `hardwareConcurrency + 1` busy-loop Web Workers kept in the perceptible/foreground CPU cgroup. |

## Workflow
- **Prerequisites & Setup**: Uses the publicly hosted `power_VideoCall` WebRTC page on `storage.googleapis.com` and the live single-page HTML specification at `html.spec.whatwg.org` with auto-granted synthetic media streams (no Google login or secrets required). For `with-perceptible-cpu`, setup first opens a separate, uncovered window running busy-loop Web Workers so they remain at foreground/perceptible CPU priority. Setup then starts the high-preset WebRTC call in the main window, confirms all video feeds are actively playing, and loads the HTML specification in another browser window.
- **Main Actions**: Resets the specification page to the top, marks `'scroll-begin'`, performs a 15-second native touch scroll of 15,000 pixels down the document while WebRTC video playback continues in the other window, and records `'scroll-end'` (capturing final `scrollTop` in event detail) along with the `'scroll'` User Timing measure.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Scroll User Timing Marks & Distance Payload**: Preserve the exact `'scroll-begin'` mark, `'scroll-end'` mark (carrying the document's `scrollTop` offset in `detail`), and `'scroll'` measure, which directly power the `scroll_distance` and `scroll_duration` trace metrics.
- **Native Touch Scroll Profile**: Keep scroll-to-top reset and native touch scrolling (15,000 pixels over 15 seconds, never synthetic JS scrolling) so scroll-jank and input-latency histograms remain comparable across runs and playback loops.
- **Multi-Window & Foreground CPU Cgroup Topology**: Keep the WebRTC call actively playing in its own window while scrolling the specification in a separate browser window, and for `with-perceptible-cpu`, keep the CPU-load window unoccluded so its Web Workers are not background-throttled.

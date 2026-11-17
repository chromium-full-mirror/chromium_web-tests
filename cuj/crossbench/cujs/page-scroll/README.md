# `page-scroll` CUJ

## Overview
Benchmarks page loading and native touch-scroll smoothness, frame drops, and input latency across 10 archived web pages. Replayed deterministically from a shared Web Page Replay (WPR) archive in both single-tab reuse (`default`) and accumulating multi-tab (`multiple-tab`) modes.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | **Single-tab reuse**: Loads and touch-scrolls all 10 pages sequentially inside the same tab across 2 passes (20 page loads/scrolls in 1 tab). |
| `multiple-tab` | `multiple-tab.page-config.hjson` | **Multi-tab accumulation**: Opens every page visit in a new tab across 2 passes, accumulating 20 open tabs under background-tab memory pressure before teardown. |

## Workflow
- **Prerequisites & Setup**: Replays recorded pages from the `page-click-scroll.wprgo` WPR archive (fetched via `cuj/crossbench/wpr/wpr-setup.sh`, requiring `gcloud storage` authentication on first download; no live login or separate setup actions).
- **Main Actions**: Loops **2x** across 10 archived sites (Amazon product, Amazon deals, Apple, Ebay, Google, BBC, Weather, Yahoo, StackOverflow, Wikipedia). For each site, Chrome loads the page to completion (reusing the current tab in `default` or opening a new tab in `multiple-tab`) and performs 6 consecutive native touch-scroll gestures down the page, pausing briefly for layout stabilization before the next site.
- **Teardown**: Closes all open tabs once after both playback passes finish.

## Metrics & Invariants (Preserve When Healing)
- **Native `touch` scroll input**: Scroll actions must always use native OS/WebDriver `touch` injection (never simulated JavaScript scrolling) so Chrome's input and compositor pipelines record `Event.ScrollJank.*`, `EventLatency.*`, `Graphics.Smoothness.*`, and slow-input metrics.
- **Single-tab vs accumulating multi-tab behavior**: Keep `default` in a single tab and keep `multiple-tab` opening new tabs without closing them mid-run so the impact of background-tab memory and throttling on scroll smoothness is isolated.
- **WPR archive & User-Timing marks**: Keep all 10 URLs covered by `page-click-scroll.wprgo` and preserve the `page-load`, `page-loaded`, `scroll-entire-page-start`, `scroll-entire-page-end` (with scroll offset detail), and `scroll-entire-page-duration` User-Timing marks/measures.

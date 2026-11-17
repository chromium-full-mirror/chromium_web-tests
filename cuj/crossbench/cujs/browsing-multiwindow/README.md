# `browsing-multiwindow` CUJ

## Overview
Benchmarks long-running power, memory, compositor visibility/occlusion, and cross-window tab-switching performance when browsing across multiple browser windows. It maintains 5 persistent tabs split across 2 browser windows and rotates 10 static `power_LoadTest` web pages through those tabs over a ~60-minute session.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Opens 5 persistent tabs across 2 browser windows (2 tabs in Window 1, 3 tabs in Window 2) and rotates the 10 casual `power_LoadTest` snapshots across them over 2 passes (~60 minutes total). |

## Workflow
- **Prerequisites & Setup**:
  - Requires live network access to `https://storage.googleapis.com/chromiumos-test-assets-public/power_LoadTest/2023-08-09/` (no login or WPR archive).
  - **One-time setup**: Closes any pre-existing tabs, then creates 5 `about:blank` tabs split across **2 browser windows** (2 tabs in the first window and 3 tabs in a second newly opened window).
- **Main Actions**: Loops **2x** over the 10 casual snapshot pages. In each pass, Chrome cycles through the 5 persistent tabs twice (visiting tabs 0–4 for pages 1–5, then tabs 0–4 again for pages 6–10): switching focus across the two windows, loading the next snapshot URL in place, verifying that no browser error interstitial is shown, and dwelling for 3 minutes while periodically scrolling down and back up every 40 seconds.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Preserve the 2-window, 5-tab topology**: Setup must keep 2 tabs in Window 1 and 3 tabs in Window 2, and main actions must switch across those 5 existing tabs and load pages in place rather than opening additional windows/tabs or collapsing into a single window.
- **Fail fast on error interstitials**: Retain the post-load check verifying that Chrome did not land on an offline/certificate/timeout interstitial page before spending 3 minutes scrolling.
- **User-Timing marks & session cadence**: Preserve `page-load`, `page-loaded`, `scroll-start`, `scroll-end`, and `scroll-duration` User-Timing marks along with the 2-pass, 3-minute-per-page dwell cadence.

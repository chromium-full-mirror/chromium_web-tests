# `browsing` CUJ

## Overview
Benchmarks long-running single-tab power consumption, thermal behavior, CPU utilization, and memory usage during sustained sequential web browsing. Chrome visits 10 static web page snapshots in a single tab, dwelling on each page while periodically scrolling down and back up over a ~20-minute or ~60-minute session.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `casual` | `casual.page-config.hjson` | Visits the lighter **casual** 10-page snapshot set, dwelling and scrolling for 3 minutes per page across 2 passes (~60 minutes total). |
| `casual-20min` | `casual-20min.page-config.hjson` | Visits the same **casual** 10-page set as `casual`, shortened to 1 minute per page across 2 passes (~20 minutes total). |
| `heavy` | `heavy.page-config.hjson` | Visits the DOM- and media-heavier **heavy** 10-page snapshot set, dwelling and scrolling for 3 minutes per page across 2 passes (~60 minutes total). |
| `heavy-20min` | `heavy-20min.page-config.hjson` | Visits the same **heavy** 10-page set as `heavy`, shortened to 1 minute per page across 2 passes (~20 minutes total). |

## Workflow
- **Prerequisites & Setup**: Requires live network access to the static `power_LoadTest` HTML snapshots hosted at `https://storage.googleapis.com/chromiumos-test-assets-public/power_LoadTest/2023-08-09/` (no login or WPR archive; media autoplay without user gesture is enabled).
- **Main Actions**: Loops **2x** over the variant's 10-page sequence inside a single reused tab (20 page visits total). On each visit, Chrome navigates the current tab to the snapshot URL and dwells for 3 minutes (`casual`, `heavy`) or 1 minute (`casual-20min`, `heavy-20min`) while an asynchronous background script periodically scrolls the window down and back up every 40 seconds.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Single-tab reuse**: All navigations must happen in place within one tab (contrasting with `browsing-multitab` and `browsing-multiwindow`).
- **Session duration & scroll cadence**: Preserve the 2-pass loop, per-page dwell durations (~60-minute vs ~20-minute variants), and periodic up/down scroll behavior so power and thermal profiles remain comparable over time.
- **Paired casual vs heavy snapshot sets**: Keep `casual`/`casual-20min` and `heavy`/`heavy-20min` aligned on their respective 10 static `power_LoadTest` snapshot URLs.
- **User-Timing marks**: Preserve the `page-load`, `page-loaded`, `scroll-start`, `scroll-end` (with scroll offset detail), and `scroll-duration` User-Timing marks/measures alongside system CPU, memory, and power telemetry.

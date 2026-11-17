# `browsing-multitab` CUJ

## Overview
Benchmarks sustained multi-tab memory pressure, background-tab throttling and discarding, tab-switch latency, and power consumption over long browsing sessions. All tabs are opened and loaded up front during setup, and the main workload repeatedly cycles focus through every open tab and scrolls it without explicitly reloading tabs.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `10tabs` | `10tabs.page-config.hjson` | Opens **10** concurrent tabs (the heavy 10-page `power_LoadTest` snapshot set) and cycles through them across 2 passes at 3 minutes per tab (~60 minutes main-loop runtime). |
| `20tabs` | `20tabs.page-config.hjson` | Opens **20** concurrent tabs (combining the 10 heavy and 10 casual `power_LoadTest` snapshot sets) and cycles through them across 2 passes at 3 minutes per tab (~120 minutes main-loop runtime). |

## Workflow
- **Prerequisites & Setup**:
  - Requires live network access to the static `power_LoadTest` snapshots at `https://storage.googleapis.com/chromiumos-test-assets-public/power_LoadTest/2023-08-09/` (no login or WPR archive).
  - **One-time setup**: Opens and loads all 10 (`10tabs`) or 20 (`20tabs`) snapshot pages into separate tabs in a single window before the playback loop begins (loading the first page in the initial tab and the remaining pages in new tabs).
- **Main Actions**: Loops **2x** through all open tabs sequentially without closing or re-navigating them. For each tab, Chrome switches focus to that tab and dwells for 3 minutes while periodically scrolling down and back up every 40 seconds.
- **Teardown**: None (all 10 or 20 tabs remain open through the end of the run).

## Metrics & Invariants (Preserve When Healing)
- **Persistent 10-tab / 20-tab residency**: All tabs must be opened once during setup and revisited solely via tab switching during the main loop—never close tabs mid-run or replace tab switches with fresh navigations, as the benchmark specifically measures multi-tab memory residency, low-memory/PSI pressure, and background tab discarding/reloading.
- **Session duration & scroll cadence**: Preserve the 2-pass loop and 3-minute per-tab scroll dwell so ~60-minute (`10tabs`) and ~120-minute (`20tabs`) memory, tab-switch (`Browser.Tabs.*`), and power profiles remain comparable.
- **User-Timing marks**: Preserve `page-load`, `page-loaded`, `scroll-start`, `scroll-end`, and `scroll-duration` User-Timing instrumentation.

# `open-close` CUJ

## Overview
Benchmarks native and Java memory leak behavior, tab and window teardown cleanup, and cold renderer process startup latency across repeated open-and-close lifecycles. Each cycle opens a page in a new tab or browser window, closes it via a native keyboard shortcut, and measures post-close memory to detect per-cycle leaks and retained Android `Activity`, `View`, or `Drawable` hierarchies.

## Variants
Eight variants cross **four page workloads** (Amazon product page, multi-process cross-origin iframe page, Chrome's internal New Tab Page, and Google Sheets) with **two container modes** (new tab vs. new browser window) over 40 open-close cycles. A ninth variant (`javaless-renderer-startup`) reuses the multi-process tab workload to profile cold Android renderer startup.

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `amazon-tab` | `amazon-tab.page-config.hjson` | Opens and closes an Amazon product page in a new tab 40 times using deterministic Web Page Replay (WPR). |
| `amazon-window` | `amazon-window.page-config.hjson` | Opens and closes the WPR-backed Amazon product page in a separate browser window 40 times. |
| `javaless-renderer-startup` | `javaless-renderer-startup.page-config.hjson` | Aliases `multi-process-tab` over 5 open-close cycles with javaless renderers enabled and spare renderer pre-warming disabled, measuring cold native zygote fork and renderer initialization latency. |
| `multi-process-tab` | `multi-process-tab.page-config.hjson` | Opens and closes a hosted page containing 5 cross-origin iframes in a new tab 40 times; also serves as the base workload for `javaless-renderer-startup`. |
| `multi-process-window` | `multi-process-window.page-config.hjson` | Opens and closes the 5-cross-origin-iframe page in a separate browser window 40 times. |
| `new-tab-page-tab` | `new-tab-page-tab.page-config.hjson` | Opens and closes `chrome://newtab` in a new tab 40 times, isolating baseline tab lifecycle cleanup. |
| `new-tab-page-window` | `new-tab-page-window.page-config.hjson` | Opens and closes `chrome://newtab` in a separate browser window 40 times, isolating browser window and Android `Activity` teardown leaks. |
| `sheets-tab` | `sheets-tab.page-config.hjson` | Opens and closes a publicly shared Google Sheets spreadsheet in a new tab 40 times. |
| `sheets-window` | `sheets-window.page-config.hjson` | Opens and closes the shared Google Sheets spreadsheet in a separate browser window 40 times. |

## Workflow
- **Prerequisites & Setup**: No account login is needed. `amazon-*` replays recorded traffic offline from the repository's WPR archive; `new-tab-page-*` runs offline on `chrome://newtab`; `multi-process-*`, `javaless-renderer-startup`, and `sheets-*` require live network access to the hosted cross-origin test pages and the public Google Sheets document. `javaless-renderer-startup` additionally launches Chrome with javaless renderers enabled and spare renderer pre-warming disabled so every cycle cold-starts renderer processes.
- **Main Actions**: Loops 40 times by default (5 times for `javaless-renderer-startup`). Each cycle opens the target page in a new tab or window, waits for load completion, sends a native `Ctrl+W` key press to close it, switches focus back to the initial anchor tab, and captures a post-close memory snapshot (`closed`).
- **Teardown**: Captures an Android Java heap dump after all open-close cycles finish to detect leaked `Activity`, `View`, and `Drawable` instances.

## Metrics & Invariants (Preserve When Healing)
- **Native `Ctrl+W` close & anchor focus**: Close the tab or window via native keyboard `Ctrl+W` input and return focus to the anchor tab; do not replace `Ctrl+W` with WebDriver tab-close APIs, which bypass browser keyboard-shortcut UI teardown paths.
- **Tab vs. window separation**: Preserve new-tab vs. new-window targets; `*-window` variants specifically test whether destroyed windows leak Android `Activity` and view hierarchies.
- **Cross-origin OOPIF teardown & cold renderer forks**: Preserve the 5 cross-origin subframes in `multi-process-*` (and its `javaless-renderer-startup` alias) together with `javaless-renderer-startup`'s disabled spare renderer pre-warming so renderer processes are freshly forked from the native zygote and torn down each cycle.
- **WPR archive alignment**: In `amazon-*`, keep the exact recorded Amazon product URL so offline WPR playback succeeds without network misses.
- **Post-close memory & Java heap checkpoints**: Preserve the per-cycle `closed` memory snapshot (used to compute per-iteration memory leak slopes) and the final teardown Java heap dump.

# `open` CUJ

## Overview
Benchmarks cumulative browser memory growth, multi-process renderer scaling, and Android Java heap retention as a user repeatedly opens new tabs or browser windows without closing earlier ones. Over 20 iterations, the benchmark measures marginal per-tab and per-window memory cost alongside live `Activity`, `View`, and `Drawable` heap footprints.

## Variants
Variants cross **three page workloads** (Chrome's internal New Tab Page, a multi-frame test page with cross-origin subframes, and a complex Google Sheets web app) with **two container modes** (opening new tabs inside a single browser window vs. opening separate top-level browser windows).

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `multi-process-tab` | `multi-process-tab.page-config.hjson` | Opens 20 cumulative tabs of a hosted multi-frame page embedding 5 cross-origin iframes per tab to exercise site-isolated renderer processes. |
| `multi-process-window` | `multi-process-window.page-config.hjson` | Opens 20 separate browser windows of the same 5-cross-origin-iframe page, combining multi-process renderer load with OS window / Android `Activity` creation. |
| `new-tab-page-tab` | `new-tab-page-tab.page-config.hjson` | Opens 20 cumulative `chrome://newtab` tabs in one window, isolating baseline per-tab browser overhead from external web content. |
| `new-tab-page-window` | `new-tab-page-window.page-config.hjson` | Opens 20 separate browser windows on `chrome://newtab`, isolating baseline per-window and Android `Activity` overhead. |
| `sheets-tab` | `sheets-tab.page-config.hjson` | Opens 20 cumulative tabs of a publicly shared Google Sheets spreadsheet in a single window. |
| `sheets-window` | `sheets-window.page-config.hjson` | Opens 20 separate browser windows of the same shared Google Sheets spreadsheet. |

## Workflow
- **Prerequisites & Setup**: No account login or WPR archive is used. `new-tab-page-*` runs offline against Chrome's internal NTP; `multi-process-*` and `sheets-*` require live network access to the hosted cross-origin test pages and the publicly shared Google Sheets document.
- **Main Actions**: Loops 20 times by default. Each iteration opens the target page in a new tab or new browser window, waits for document load completion, and records a system and per-process memory snapshot (`opened`) while leaving all previously opened tabs/windows alive.
- **Teardown**: Captures an Android Java heap dump while all 20 opened tabs or windows remain open so retained `Activity`, `View`, and `Drawable` objects can be analyzed.

## Metrics & Invariants (Preserve When Healing)
- **Tab vs. window separation**: Preserve opening in a new tab for `*-tab` variants and a new top-level browser window for `*-window` variants; changing container mode alters OS window and Android `Activity` allocation.
- **Cumulative open behavior**: Never close tabs or windows between iterations—accumulating 20 live instances is the core purpose of `open` (whereas `open-close` tests teardown leaks).
- **Cross-origin iframe isolation**: In `multi-process-*`, preserve the 5 distinct cross-origin subframes per page so Chrome spawns site-isolated out-of-process iframe renderers.
- **Named memory snapshots & Java heap dump**: Preserve the per-iteration `opened` memory snapshot checkpoint (used to compute per-iteration memory growth slopes) and the final Java heap dump at teardown.

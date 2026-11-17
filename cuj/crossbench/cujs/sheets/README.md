# `sheets` CUJ

## Overview
Benchmarks interactive Google Sheets editing and grid-scrolling responsiveness on a large spreadsheet (an Ontario public-sector salary dataset): opening a fresh copy of the template Sheet, inserting and posting a cell comment, and scrolling vertically through the grid. Measures comment-box open latency, grid scroll distance and duration, and touch/keyboard input latency both idle and under background CPU contention.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Baseline Google Sheets commenting and grid-scrolling workflow with no background workload. |
| `with-background-cpu` | `with-background-cpu.page-config.hjson` | Runs the Sheets workflow while a hidden background tab executes spinning Web Workers to contend for CPU cores. |

## Workflow
- **Prerequisites & Setup**: Requires Google test account login plus `google_workspace` service-account and Shared Drive credentials in the secrets config so the `google_workspace` probe can clone the canonical template spreadsheet via the Google Drive API before editing. In `with-background-cpu`, a secondary browser window first launches a multi-worker CPU spin tab occluded behind `example.com` before returning focus to the primary tab.
- **Main Actions**: Clones the canonical template spreadsheet into the Shared Drive and redirects the browser to the disposable copy, opens the Insert menu to add a comment, types the comment via native keyboard input and posts it, then performs a sequence of native touch scrolls down the spreadsheet grid.
- **Teardown**: No explicit browser teardown actions; cloned Shared Drive spreadsheets carry a 4-hour TTL metadata property set at creation time for external cleanup.

## Metrics & Invariants (Preserve When Healing)
- **Never mutate the canonical template Sheet**: Always preserve the `google_workspace` probe's copy-and-redirect step so comments are only posted to disposable Shared Drive copies rather than polluting the shared template.
- **Comment-open observer and User Timing marks**: Preserve the pre-click `MutationObserver` on the comment stream and its User Timing marks/measures (`comment-click`, `comment-opened-dom`, `comment-opened-next-frame`, `comment-opened`, and `comment-type`), which power the `comment-opened` latency metric.
- **Decoupled grid scroll target vs scrollbar offset**: Unlike Docs, Google Sheets separates the grid container that receives touch-scroll gestures from the native vertical scrollbar element whose `scrollTop` property reflects the scrolled pixel distance. Preserve both distinct targets when healing so `scroll-begin`, `scroll-end` (with `scrollTop` detail), and the `scroll` measure report non-zero distance and duration.
- **Native input and exact menu targeting**: Keep native touch clicks and native keyboard typing for `EventLatency` tracking, and use exact Workspace menu labels rather than prefix wildcards (e.g., avoid `[aria-label^='Comment']`).
- **Background-CPU occlusion**: In `with-background-cpu`, keep the CPU-worker tab covered by a real web page (`example.com`, not `about:blank`) in the secondary window so Chrome applies background priority throttling, and return focus to the primary tab.

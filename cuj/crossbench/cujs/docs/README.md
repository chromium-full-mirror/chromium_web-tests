# `docs` CUJ

## Overview
Benchmarks interactive Google Docs editing and scrolling responsiveness on a multi-page prose document: opening a fresh copy of a template document, inserting and posting a margin comment, and scrolling through the document editor. Evaluates comment-box open latency, scroll smoothness/distance, and touch/keyboard input latency both idle and under competing CPU or video workloads.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Baseline Google Docs commenting and scrolling workflow with no background workload. |
| `with-background-cpu` | `with-background-cpu.page-config.hjson` | Runs the Docs workflow while a hidden background tab executes spinning Web Workers to contend for CPU cores. |
| `with-background-video` | `with-background-video.page-config.hjson` | Runs the Docs workflow while a secondary browser window plays a looping 1080p60 VP9 video (with gestureless autoplay enabled). |

## Workflow
- **Prerequisites & Setup**: Requires Google test account login plus `google_workspace` service-account and Shared Drive credentials in the secrets config so the `google_workspace` probe can clone the canonical template Doc via the Google Drive API before editing. Background-CPU and background-video variants first set up a secondary browser window running either an occluded Web Worker CPU-spin tab or a visible looping 1080p60 VP9 video, then return focus to the primary tab.
- **Main Actions**: Clones the canonical template document into the Shared Drive and redirects the browser to the disposable copy, opens the Insert menu to add a new comment, types the comment text via native keyboard input and posts it, then performs a sequence of native touch scrolls down the Docs editor canvas.
- **Teardown**: No explicit browser teardown actions; cloned Shared Drive documents are tagged with a 4-hour TTL metadata property at creation time for external cleanup.

## Metrics & Invariants (Preserve When Healing)
- **Never mutate the canonical template Doc**: Always preserve the `google_workspace` probe's copy-and-redirect step so every iteration edits an isolated Shared Drive copy rather than accumulating comments on the shared template.
- **Comment-open observer and User Timing marks**: Preserve the pre-click `MutationObserver` on the Docs comment stream and its User Timing marks/measures (`comment-click`, `comment-opened-dom`, `comment-opened-next-frame`, `comment-opened`, and `comment-type`), which directly power the `comment-opened` latency metric.
- **Scroll metrics**: Preserve the `scroll-begin` / `scroll-end` marks, the `scroll` measure, and recording the Docs editor's vertical `scrollTop` offset in `scroll-end`'s event detail (ensuring it remains non-zero after scrolling) so scroll distance and duration metrics stay populated.
- **Native input and exact menu targeting**: Keep native touch clicks and native keyboard typing for `EventLatency` tracking, and match Workspace menu items with exact labels rather than prefix wildcards (e.g., avoid `[aria-label^='Comment']`, which can match multiple menu items).
- **Background-load window visibility**: Keep the background-CPU tab covered by a real web page (`example.com`, not `about:blank`) so background throttling applies, and keep the secondary video window visible/unoccluded in `with-background-video`.

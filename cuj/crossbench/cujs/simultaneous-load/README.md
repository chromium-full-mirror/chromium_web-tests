# `simultaneous-load` CUJ

## Overview
Benchmarks concurrent multi-tab page-load contention, tab-open latency, and total wall-clock completion time when 10 web pages are opened back-to-back in new tabs without waiting for earlier tabs to finish loading. Replayed deterministically against the shared `page-click-scroll.wprgo` Web Page Replay archive.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Launches 10 archived web pages concurrently in separate new tabs in a single pass, then waits for all 10 tabs to finish loading and closes them. |

## Workflow
- **Prerequisites & Setup**:
  - Replays recorded pages from the `page-click-scroll.wprgo` WPR archive (downloaded via `cuj/crossbench/wpr/wpr-setup.sh`, requiring `gcloud storage` authentication on first setup; no live login).
  - Relies on Crossbench's initial `data:text` splash tab remaining open during tab launch so early `page-load` User-Timing marks execute on an already-live renderer rather than getting dropped during new renderer startup.
- **Main Actions**: Runs a single pass with two phases over 10 archived sites (Amazon product, Amazon deals, Apple, Ebay, Google, Wattpad, BBC, Yahoo, StackOverflow, Wikipedia):
  1. **Concurrent launch**: For each of the 10 sites, switches back to the `data:text` splash tab to emit a `page-load` mark, immediately opens the site in a new tab without blocking on load completion, and attaches a `readystatechange` handler on the new tab to emit a matching `page-loaded` mark when the document reaches `complete`.
  2. **Completion barrier & cleanup**: Switches to each of the 10 opened tabs in turn, waits for its document ready state to reach `complete`, and closes the tab.
- **Teardown**: None (all 10 opened tabs are closed during the completion barrier phase).

## Metrics & Invariants (Preserve When Healing)
- **Non-blocking concurrent launch & `data:text` splash tab**: New tabs must be opened asynchronously (`ready_state: any`) so all 10 pages contend concurrently rather than loading serially, and `page-load` marks must continue to be emitted from the persistent `data:text` splash tab (which also drives `tab_open_latency`).
- **Matching `{ url, index }` User-Timing detail payload**: Custom CUJ metrics (`cuj.simultaneous-load.tab_load_duration` and `cuj.simultaneous-load.total_load_duration`) match cross-process `page-load` and `page-loaded` marks by exact serialized JSON equality on their `detail` payload and parse the URL assuming `url` precedes `index`—both marks must emit identical `{ url, index }` detail objects in that key order.
- **1-to-1 URL alignment with WPR**: Keep the 10 launched URLs, the tab-matching patterns in the completion barrier, and the `page-click-scroll.wprgo` archive aligned 1-to-1.

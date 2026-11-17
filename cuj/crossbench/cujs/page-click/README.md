# `page-click` CUJ

## Overview
Benchmarks initial page-load Largest Contentful Paint (LCP) and in-page link-click navigation latency (from native click input dispatch to the destination page's LCP) across 10 archived web pages. Replayed deterministically from a Web Page Replay (WPR) archive in both single-tab reuse (`default`) and accumulating multi-tab (`multiple-tab`) modes.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | **Single-tab reuse**: Registers the LCP observer once per pass on the active tab and runs all 10 page loads and link-click navigations sequentially within that single tab across 2 passes. |
| `multiple-tab` | `multiple-tab.page-config.hjson` | **Multi-tab accumulation**: Opens a fresh tab and registers a per-tab LCP observer before every page visit across 2 passes, accumulating 20 open tabs before teardown. |

## Workflow
- **Prerequisites & Setup**:
  - Replays recorded pages from the `page-click-scroll.wprgo` WPR archive (downloaded via `cuj/crossbench/wpr/wpr-setup.sh`, which requires `gcloud storage` authentication on first setup; no live login).
  - Injects a new-document `PerformanceObserver` script (`largest-contentful-paint`) on the active tab (`default`) or on each newly opened tab (`multiple-tab`) so every navigation can await LCP completion.
- **Main Actions**: Loops **2x** across 10 archived sites (Amazon product, Amazon deals, Apple, Ebay, Google, Wattpad, BBC, Yahoo, StackOverflow, Wikipedia). On each site, Chrome loads the initial URL and waits for LCP, then clicks an in-page navigation link with native mouse input, verifies an expected element on the destination page, and waits for the destination page's LCP.
- **Teardown**: Closes all open tabs once after both playback passes finish.

## Metrics & Invariants (Preserve When Healing)
- **Strict 1-to-1 User-Timing mark sequence**: Custom CUJ metrics (`cuj.page_click.page_load_time` and `cuj.page_click.link_load_time`) pair `page-load` / `page-loaded` and `click-link-on-page` / `click-link-on-page-loaded` marks strictly by chronological order—every step must emit all four marks in exact 1-to-1 correspondence.
- **Native `mouse` clicks triggering real LCP navigations**: Link clicks must use native `mouse` input (never simulated JS clicks), because link-load latency is measured from Chrome's native `EventLatency` tap-down event to `NavigationToLargestContentfulPaint` on the destination page.
- **WPR archive coverage**: Any healed link target and verification element must navigate to a destination URL already recorded inside `page-click-scroll.wprgo` and produce a valid LCP event.
- **Tab lifecycle & per-tab LCP observer**: Preserve single-tab reuse in `default` vs accumulating unclosed tabs in `multiple-tab` (including registering the new-document LCP observer on each newly opened tab, since CDP new-document scripts are tab-scoped).

# `docs-tab-switches` CUJ

## Overview
Benchmarks multi-tab switching latency, 2D canvas hibernation/eviction, and GPU `GrContext` cleanup overhead across 9 simultaneously open heavy Google Docs browser tabs. Each browser tab loads a distinct document tab of a large multi-tab Google Doc and scrolls it to allocate canvas/GPU backing stores before cycling rapidly across all 9 tabs twice.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Opens 9 Google Docs tabs and performs two 9-tab switch passes (18 switches total) with 2D canvas hibernation and background resource-clearing features enabled. |

## Workflow
- **Prerequisites & Setup**: No Google account login is required because all 9 target URLs reference a publicly readable multi-tab Google Doc via a `resourcekey` link. Browser flags enable 2D canvas hibernation and background canvas eviction features, and tracing enables detailed task-level GPU slices. (Note: the initial browser tab at index `0` remains open, so the 9 newly opened Docs tabs occupy tab indices `1` through `9`.)
- **Main Actions**: Sequentially opens 9 distinct document sub-tabs of the Google Doc in new browser tabs, performing a short native touch scroll on each tab after load so canvas and GPU resources are populated. Once all 9 tabs are loaded, cycles sequentially through tabs `1` through `9` twice (18 tab switches total).
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Tab-switch User Timing gate and switch count**: The tab-switch latency metric filters Chrome's `*SwitchDuration3` histograms strictly after the first `navigate_to_tab*` User Timing mark (`navigate_to_tab` / `navigate_to_tab_done`) and expects 18 tab switches per run; preserve both those exact mark names and the two-pass 18-switch sequence.
- **Tab count and index alignment**: Keep opening all 9 document URLs in separate new browser tabs alongside initial tab `0` so tab indices `1` through `9` remain aligned with the 9 loaded Google Docs tabs.
- **Canvas allocation and GPU cleanup tracing**: Preserve the native touch scroll on each loaded tab (so canvas/GPU resources exist to hibernate and clean up when backgrounded) as well as the canvas hibernation browser features and task-level tracing needed to measure `ScheduleGrContextCleanup` durations on the GPU main thread.

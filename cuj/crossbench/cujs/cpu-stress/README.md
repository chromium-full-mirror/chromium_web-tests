# `cpu-stress` CUJ

## Overview
Benchmarks renderer CPU throughput, multi-process CPU scheduling contention, and background-tab throttling under sustained compression load. Each opened tab continuously gzip-compresses a locally served payload via `CompressionStream('gzip')`, comparing an uncontended single foreground tab (`1`) against 1 foreground tab competing with 15 background tabs (`16`).

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `1` | `1.page-config.hjson` | **Uncontended baseline**: Runs continuous gzip compression in **1** foreground tab with 0 background tabs. |
| `16` | `16.page-config.hjson` | **Multi-tab contention**: Spawns **15** additional tabs 1 second apart so 1 foreground tab competes with 15 background tabs (16 concurrent compression tabs total). |

*(Note: `action-blocks/page-config.hjson` is the shared template imported by `1.page-config.hjson` and `16.page-config.hjson`, not a standalone variant.)*

## Workflow
- **Prerequisites & Setup**:
  - Serves `cpu-stress.html` and the `perf.report` compression payload locally via Crossbench's built-in local HTTP file server (`cujs/cpu-stress/www` on `localhost:8000`; no external network or login required).
  - Disables popup blocking so variant `16` can programmatically spawn 15 additional tabs via `window.open`, while keeping standard background-tab interventions active.
- **Main Actions**: Runs a single pass with two phases:
  1. **Ramp-up**: Loads `cpu-stress.html` in the initial tab (which fetches `perf.report` once into memory, tracks whether the tab has ever been hidden via `visibilitychange`, and enters an infinite `CompressionStream('gzip')` loop emitting a `compress` User-Timing mark after each iteration). Variant `16` then opens 15 additional `cpu-stress.html` tabs spaced 1 second apart with `noopener`, pushing the first 15 tabs into the background while the 16th tab stays in the foreground.
  2. **Steady-state measurement**: Waits **60 seconds** while all opened tabs compress `perf.report` concurrently.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **`compress` User-Timing mark contract**: Custom CUJ metrics (`cuj.cpu-stress.foreground_throughput`, `foreground_size`, `background_throughput`, `background_size`) wait until every worker track has emitted at least one `compress` mark before aggregating steady-state samples, and rely on `{ everHidden, size, time }` inside the `compress` mark's `detail` object—never rename `compress` or change those detail fields.
- **Renderer process isolation (`noopener`)**: Additional tabs in variant `16` must be opened with `noopener` so each tab runs on its own isolated renderer main-thread track (`workers = 1` vs `workers = 16`); omitting `noopener` shares a single renderer process and invalidates multi-process contention and worker counting.
- **Foreground vs background visibility split**: Do not switch back to earlier tabs or occlude the final tab—`everHidden` latches permanently once a tab becomes hidden, so variant `1` must keep its sole tab visible and variant `16` must maintain 15 hidden background tabs plus 1 visible foreground tab.

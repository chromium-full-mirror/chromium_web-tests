# `memory-pressure` CUJ

## Overview
Benchmarks Chrome background tab discarding, zram/swap compression and reclaim, Low Memory Killer (LMK) renderer kills, and tab allocation latency under synthetic 2x-RAM memory overcommit. Over the course of a run, Chrome opens 100 tabs whose cumulative JavaScript heap allocations equal twice the target device's physical RAM, measuring how many renderer processes remain alive as memory pressure builds.

## Variants
Each variant targets a specific **device RAM tier**, scaling the per-tab `Float64Array` allocation so that 100 tabs collectively allocate **2x total device RAM**.

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `4g` | `4g.page-config.hjson` | Targets 4 GiB RAM devices (~82 MiB allocated per tab; 8 GiB total across 100 tabs). |
| `8g` | `8g.page-config.hjson` | Targets 8 GiB RAM devices (~164 MiB allocated per tab; 16 GiB total across 100 tabs). |
| `16g` | `16g.page-config.hjson` | Targets 16 GiB RAM devices (~328 MiB allocated per tab; 32 GiB total across 100 tabs). |
| `32g` | `32g.page-config.hjson` | Targets 32 GiB RAM devices (~655 MiB allocated per tab; 64 GiB total across 100 tabs). |

## Workflow
- **Prerequisites & Setup**: Self-contained offline workload using inline `data:` URLs; requires no login, network access, WPR archive, or extensions. Run the variant matching the test device's physical RAM size.
- **Main Actions**: Runs 1 pass across 100 sequentially opened tabs (`00`–`99`). For each tab, the benchmark marks the start of navigation, opens a new tab, allocates the variant's per-tab `Float64Array` filled with ~67% random floats and ~33% zeros per 4 KiB page, retains the buffer on `document` to prevent garbage collection, emits User Timing completion marks, and pauses briefly before opening the next tab to avoid sudden kernel OOM instability.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **2x-RAM scaling, zram entropy, & GC retention**: Preserve the per-variant allocation size, the ~67% random per-page fill ratio (which prevents zram/zero-page deduplication from trivially compressing away the memory footprint), and retaining the allocated buffer on `document` so V8 GC cannot reclaim it.
- **Cumulative tab opens & allocation pacing**: Keep opening all 100 tabs without closing prior tabs, and preserve the brief inter-tab pacing pause so background tab discarding and kernel memory reclaim can react progressively.
- **Indexed User Timing marks**: Preserve the `page-load~<index>`, `page-loaded~<index>`, `allocation-start~<index>`, and `allocation-done~<index>` User Timing marks with integer tab indices (`00`–`99`), which trace queries join with renderer process lifetimes to compute load/allocation durations, surviving tab counts, and first-kill thresholds.

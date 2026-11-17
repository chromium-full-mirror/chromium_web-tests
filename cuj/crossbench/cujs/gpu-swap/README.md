# `gpu-swap` CUJ

## Overview
Benchmarks kernel DRM GPU buffer shrinker swap-out, system memory Pressure Stall Information (PSI), and foreground vs. background WebGL frame rates under sustained multi-window GPU memory pressure. Opens a GPU-heavy background window followed by an actively growing GPU-heavy foreground window, then soaks for 5 minutes while monitoring how much GPU buffer memory the kernel offloads to swap.

## Variants
Both variants run the same two-window GPU memory pressure workload and differ only in whether the background window keeps rendering or goes idle once its initial GPU buffer pool is allocated.

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `busyback` | `busyback.page-config.hjson` | Background GPU window (`back`) keeps its rendering loop actively running after freezing buffer-pool growth, keeping its GPU buffers hot while the foreground window grows GPU memory demand. |
| `haltback` | `haltback.page-config.hjson` | Background GPU window (`back`) halts its rendering loop once its buffer pool is built, letting its retained GPU buffers go cold and eligible for DRM shrinker swap-out while the foreground window grows. |

## Workflow
- **Prerequisites & Setup**:
  - Requires live network access to the hosted `gpu_mem_pressure` test pages on Google Cloud Storage (no login needed).
  - Requires **root ADB shell access (`su 0`)** on Android/DRM devices with debugfs shrinker support: a background shell probe spawns a root daemon that polls `/sys/kernel/debug/dri/0/backed_up_bos` and writes offloaded buffer/byte counts into `/sys/kernel/tracing/trace_marker`.
  - Closes any pre-existing browser tabs before starting the workload.
- **Main Actions**: Runs once (`1x`). Opens the background `gpu_mem_pressure` workload (`back`) in a new browser window and verifies it loaded without a network/certificate error interstitial, opens the foreground `gpu_mem_pressure` workload (`main`) in a second browser window (pushing the first window into the background), and waits 5 minutes (`300s`) while foreground GPU buffer allocation drives memory pressure.
- **Teardown**: Terminates the background root shrinker-monitoring daemon and flushes its captured logs when tracing stops.

## Metrics & Invariants (Preserve When Healing)
- **Separate foreground and background windows**: Preserve opening both workloads in separate top-level browser windows so `back` and `main` hold distinct background and foreground GPU contexts, and preserve the 5-minute soak duration.
- **Active vs. halted background rendering**: Preserve the active background render loop in `busyback` vs. halting the background render loop in `haltback`, along with each window's GPU buffer pool size and growth behavior.
- **Trace slice & ftrace telemetry names**: Preserve the `back` and default (`main`) workload instance names (which emit `cxbx.frames.back` and `cxbx.frames.main` FPS/stored-buffer trace events) and the root shrinker probe's `cxbx.mem` ftrace markers used to correlate offloaded GPU buffers with PSI memory stalls.

# `click-input-latency` CUJ

## Overview
Benchmarks end-to-end browser click and tap input latency (`EventLatency` distributions and slow-input tail rates) on a minimal local click-counter page. Measures input responsiveness both in an idle baseline browser and while the system contends with background Web Worker CPU saturation or concurrent 1080p60 VP9 video playback.

## Variants
Variants form a 2x3 matrix crossing **native input modality** (`mouse` clicks vs. `touch` taps) with **competing background workload** (idle baseline, background CPU load, or concurrent video playback).

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `mouse` | `mouse.page-config.hjson` | Native `mouse` clicks on the click-counter page with no competing background workload. |
| `mouse-with-background-cpu` | `mouse-with-background-cpu.page-config.hjson` | Native `mouse` clicks while spinning Web Workers saturate CPU cores from an occluded background tab in a second window. |
| `mouse-with-background-video` | `mouse-with-background-video.page-config.hjson` | Native `mouse` clicks while a second browser window plays looped 1080p60 VP9 video. |
| `touch` | `touch.page-config.hjson` | Native `touch` taps on the click-counter page with no competing background workload. |
| `touch-with-background-cpu` | `touch-with-background-cpu.page-config.hjson` | Native `touch` taps while spinning Web Workers saturate CPU cores from an occluded background tab in a second window. |
| `touch-with-background-video` | `touch-with-background-video.page-config.hjson` | Native `touch` taps while a second browser window plays looped 1080p60 VP9 video. |

## Workflow
- **Prerequisites & Setup**:
  - Crossbench automatically starts a local HTTP file server (`localhost:8000`) serving the local `www/` click-counter page (`mouse` and `touch` require no external network or login).
  - `*-with-background-cpu` and `*-with-background-video` additionally require live network access to open their background workload in a second browser window before returning focus to the primary window:
    - **Background CPU**: Opens the hosted Web Worker CPU-load page (spawning `hardwareConcurrency + 1` spinning workers) in a new window, opens a real web page (`example.com`) in a foreground tab of that second window to hide and background-throttle the CPU tab, and switches focus back to the primary window.
    - **Background video**: Opens `crosvideo.appspot.com` playing a looped 1080p60 VP9 stream in a new window, starts video playback, and switches focus back to the primary window.
- **Main Actions**: Runs 1 pass by default (or repeats per `--playback`). Loads the local click-counter page in the primary window, performs 100 paced native `mouse` clicks or `touch` taps on the counter button, and validates that the page's displayed click counter equals 100.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Native `mouse` vs. `touch` injection**: Always preserve native `mouse` input in `mouse*` variants and native `touch` input in `touch*` variants—never substitute synthetic JavaScript clicks or swap input sources, as `EventLatency` and slow-input metrics classify latency by native input type.
- **100-click count & DOM count validation**: Preserve all 100 paced clicks/taps against the locally served counter page and the final assertion checking that all 100 clicks registered on the page without dropped inputs.
- **Occluding the background CPU tab**: In `*-with-background-cpu`, keep the CPU-worker tab hidden behind a real navigated page (such as `example.com`, *not* `about:blank`) in the second window before returning to the primary window; otherwise Chrome will not demote the worker tab into background CPU priority/cgroups.
- **Unoccluded concurrent video window**: In `*-with-background-video`, keep the 1080p60 VP9 video playing in its own separate browser window rather than hiding or closing it so media decode and GPU compositing remain active during the click loop.

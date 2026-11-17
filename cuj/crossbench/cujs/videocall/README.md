# `videocall` CUJ

## Overview
Benchmarks deterministic multi-window WebRTC video conferencing alongside concurrent note-taking using static, publicly hosted test pages rather than live Google Meet rooms. One browser window renders a high-preset multi-stream WebRTC video call while a second window continuously types notes, evaluating both short-term responsiveness under background vs perceptible CPU contention and multi-hour thermal, power, and memory endurance.

## Variants
Variants differ along **call duration** (1 minute for detailed responsiveness vs 25 minutes and 2 hours with lower-overhead endurance tracing) and **synthetic CPU contention** (no extra load, hidden background CPU load subject to tab throttling, or visible foreground/perceptible CPU load competing directly for CPU time).

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `1m` | `1m.page-config.hjson` | 1-minute call + note-taking baseline with no synthetic CPU load and high-detail tracing. |
| `1m-with-background-cpu` | `1m-with-background-cpu.page-config.hjson` | 1-minute call + note-taking with a hidden CPU-load tab (Web Workers occluded behind another tab in the same window so Chrome/OS demotes them to background priority). |
| `1m-with-perceptible-cpu` | `1m-with-perceptible-cpu.page-config.hjson` | 1-minute call + note-taking with a visible CPU-load window (Web Workers left unoccluded in their own window so they stay in the perceptible/foreground CPU cgroup). |
| `25m` | `25m.page-config.hjson` | 25-minute sustained call + note-taking run (~25 typing cycles) with no synthetic CPU load and lower-overhead long-running tracing. |
| `2hr` | `2hr.page-config.hjson` | 2-hour endurance call + note-taking run (~120 typing cycles) with no synthetic CPU load and lower-overhead long-running tracing. |

## Workflow
- **Prerequisites & Setup**: Uses publicly hosted ChromiumOS `power_VideoCall` WebRTC and note-taking pages on `storage.googleapis.com` with auto-granted synthetic media streams (no Google login or external secrets required). CPU-contention variants first launch a separate window spawning `hardwareConcurrency + 1` busy-loop Web Workers—either covering that tab with a real web page (`example.com`) to trigger background priority demotion, or leaving it visible as the active tab of its window for perceptible/foreground priority. Setup then loads the high-preset WebRTC page in the first window, verifies all video streams are actively advancing, and opens the note-taking page in a second browser window.
- **Main Actions**: Continuously types paced numeric lines via native keyboard input into the note-taking window (60 seconds per 10-line cycle), looping until the variant's target duration (`1m`, `25m`, or `2hr`) elapses while the WebRTC video grid plays concurrently.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Dual-Window WebRTC + Typing Split**: Keep the WebRTC video grid and the note-taking page in separate browser windows, and preserve the setup check confirming all `<video>` elements have started advancing before measurement begins.
- **Occluded Background vs Visible Perceptible CPU Cgroup Topology**:
  - For `1m-with-background-cpu`, the CPU-load tab must be occluded in its window by navigating a foreground tab to a real page (not `about:blank`, which fails to demote WebDriver tab priority) with background interventions enabled.
  - For `1m-with-perceptible-cpu`, the CPU-load window must remain uncovered so its Web Workers stay in the perceptible/foreground CPU cgroup while the note-taking window holds input focus.
- **Endurance Tracing & Paced Native Typing**: Preserve the separation between high-detail short-run tracing (`1m*`) and low-overhead long-running tracing (`25m`, `2hr`), and keep paced native keyboard input for consistent slow-input, PSI, memory, CPU, and smoothness metrics.

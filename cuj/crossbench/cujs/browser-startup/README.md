# `browser-startup` CUJ

## Overview
Benchmarks initial browser startup latency, memory footprint, and first-paint overhead when launching Chrome directly into `about:blank`. It provides a clean, content-free A/B comparison between traditional top-chrome UI (`baseline`) and the WebUI-as-a-Platform (WaaP) `InitialWebUI` top-chrome experiment (`initial-webui-enabled`).

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `baseline` | `baseline.page-config.hjson` | Launches into `about:blank` with the `InitialWebUI` (WaaP) top-chrome experiment explicitly disabled via variant browser flags. |
| `initial-webui-enabled` | `initial-webui-enabled.page-config.hjson` | Launches into `about:blank` with the `InitialWebUI` (WaaP) top-chrome experiment enabled via variant browser flags. |

## Workflow
- **Prerequisites & Setup**: None—requires no login, network access, WPR archive, local server, or setup actions. Tracing starts during browser/story setup so cold/initial startup events are captured.
- **Main Actions**: Runs a single pass that navigates the initial tab once to `about:blank`.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Keep the workload strictly `about:blank`**: Do not add extra navigations, waits, scripts, or DOM interactions, as any post-launch activity pollutes startup CPU, memory, and initial paint metrics.
- **Maintain identical page-config behavior across variants**: Both variants must execute the exact same minimal workload so comparisons isolate the `InitialWebUI` browser-flag configuration rather than workload differences.
- **Preserve startup tracing window**: Tracing must continue starting before browser launch/navigation so `Startup.*` and initial memory footprint histograms are captured completely.

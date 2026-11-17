# `tab-stress` CUJ

## Overview
Benchmarks browser memory footprint, renderer process scaling, background tab discarding, tab-open latency, and tab-switching responsiveness when 100 tabs (or 100 browser windows) are open concurrently. Variants compare minimal blank pages, massive single-page documents, cross-origin iframe trees, and diverse real-world websites—both with and without popular Chrome extensions installed.

## Variants
Variants span **five page workloads**, **tab vs. window containers** (`multi-window-blank` opens 100 windows instead of tabs), and **extension overhead** (the four `*-extensions` variants alias their base workload while loading 11 popular Chrome Web Store extensions).

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `blank` | `blank.page-config.hjson` | Opens and cycles through 100 `about:blank` tabs in a single window without extensions (baseline tab-strip overhead). |
| `blank-extensions` | `blank-extensions.page-config.hjson` | Aliases `blank` (100 `about:blank` tabs) with 11 Chrome Web Store extensions installed. |
| `heavy` | `heavy.page-config.hjson` | Opens and cycles through 100 tabs of the single-page HTML Living Standard (`html.spec.whatwg.org`) without extensions, heavily stressing DOM memory and tab discarding. |
| `heavy-extensions` | `heavy-extensions.page-config.hjson` | Aliases `heavy` (100 HTML spec tabs) with 11 Chrome Web Store extensions installed. |
| `multi-process` | `multi-process.page-config.hjson` | Opens and cycles through 100 tabs each embedding 5 fixed cross-origin iframes (`chromium-workloads-{0..4}.web.app`) without extensions, testing site-isolated subframe process sharing. |
| `multi-process-extensions` | `multi-process-extensions.page-config.hjson` | Aliases `multi-process` (100 tabs with 5 cross-origin iframes each) with 11 Chrome Web Store extensions injecting across main frames and subframes. |
| `multi-process-cycling` | `multi-process-cycling.page-config.hjson` | Opens and cycles through 100 tabs each embedding 11 cross-origin iframes whose origins rotate across 34 distinct hosts, stressing Chrome's renderer process cap and cross-site process reuse. |
| `multi-window-blank` | `multi-window-blank.page-config.hjson` | Opens and cycles through 100 separate browser windows on `about:blank` without extensions, isolating OS window-manager and Android `Activity` scaling relative to `blank`. |
| `real-tab` | `real-tab.page-config.hjson` | Opens and cycles through 100 tabs repeating a 10-site mix of realistic pages (Amazon, Apple, Wattpad, and archived eBay/Google/BBC/Yahoo/StackOverflow/Wikipedia snapshots) via WPR without extensions. |
| `real-tab-extensions` | `real-tab-extensions.page-config.hjson` | Aliases `real-tab` (100 real-world tabs) with 11 Chrome Web Store extensions installed; loads pages over live network unless `--wpr` is explicitly passed on the CLI. |

## Workflow
- **Prerequisites & Setup**:
  - No account login is required. `blank` and `multi-window-blank` run offline; `real-tab` uses the repository's WPR archive by default; `heavy*`, `multi-process*`, and `real-tab-extensions` require live network access, and all `*-extensions` variants require network/CWS access at startup to install the 11 Chrome Web Store extensions (Docs Offline, Grammarly, LastPass, Honey, Loom, Everynote, Perfetto UI, Microsoft Defender, Hola VPN, Japan MyNumber Portal, and CWS Payments).
  - During one-time story setup, the benchmark records a `before_open` memory snapshot, opens all 100 tabs (or windows) sequentially while emitting page-load User Timing marks on each navigation, and records an `after_open` memory snapshot.
- **Main Actions**: Runs 1 pass by default (or repeats per `--playback`). Switches back to the initial anchor tab, cycles sequentially through all 100 opened tabs or windows in creation order, and records an `after_switch` memory snapshot.
- **Teardown**: Waits 60 seconds so background memory reclaim settles and idle extension background/service-worker processes exit (after ~30 seconds of inactivity), then records a final `after_cooldown` memory snapshot.

## Metrics & Invariants (Preserve When Healing)
- **100-tab scale & ordered cycling**: Preserve opening all 100 tabs/windows during setup and visiting every opened tab/window sequentially from the initial anchor tab during the main action loop; keep tab-switch URL patterns aligned with the opened URLs.
- **Tab vs. window & cross-origin iframe topology**: Preserve 100 top-level browser windows in `multi-window-blank` (vs. tabs elsewhere), 5 fixed cross-origin subframes per tab in `multi-process*`, and 11 rotating cross-origin subframes spanning 34 distinct origins in `multi-process-cycling`.
- **Page-load User Timing marks**: Preserve the post-load script emitting `page-load` and `page-loaded` User Timing marks (including `domComplete` and `domInteractive` details), which drive tab-open latency and DOM completion metrics.
- **Four-stage memory checkpoints & 60s extension cooldown**: Preserve all four named memory snapshots (`before_open`, `after_open`, `after_switch`, `after_cooldown`) and the 60-second teardown wait required for idle extension workers to terminate before `after_cooldown`.

# `alice` CUJ

## Overview
`alice` is a flexible Crossbench `loading` harness for executing caller-supplied or agent-generated page configurations at runtime. It pairs standard real-user browser settings with an in-memory rolling Perfetto ring-buffer trace session so external harnesses or agents can clone trace snapshots mid-run or inspect traces upon completion. Currently no static page configs are checked in on disk, though static `page-config.hjson` or variant configs may be added in the future and overridden via `--page-config`.

## Variants
`alice` currently has no static `*.page-config.hjson` files checked in on disk (if static `page-config.hjson` or `<variant>.page-config.hjson` files are added later, document each variant as a row here):

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | None on disk (`--page-config` CLI flag or `TestGroup.page_config`) | Supplies the workload dynamically via `--page-config` (inline HJSON or file path) or a test-group config's `page_config` field; `--page-config` will also support overriding static configs if added later. |

## Workflow
- **Prerequisites & Setup**:
  - Requires a valid Crossbench `loading` page configuration supplied at runtime via `--page-config` or `TestGroup.page_config` while no static config exists on disk (plus optional `--secrets` or `--wpr` if the supplied workload requires authentication or replay).
  - Records traces into an in-memory rolling Perfetto ring buffer rather than streaming directly to disk, enabling mid-run snapshot cloning (`perfetto --clone-by-name`).
  - Runs any one-time `login` or `setup` steps defined by the caller-provided page configuration.
- **Main Actions**: Executes the stories and interactive actions defined in the active page configuration in a maximized viewport, repeating according to `--playback` if specified (once by default).
- **Teardown**: Executes any `teardown` steps defined in the active page configuration (none by default).

## Metrics & Invariants (Preserve When Healing)
- **Valid `loading` page configuration & native inputs**: Any static or dynamically supplied page configuration must parse cleanly as a Crossbench `loading` config and use native input sources (`mouse`, `touch`, `keyboard`) rather than simulated JavaScript events unless explicitly intended.
- **Rolling ring-buffer tracing**: Preserve the named in-memory ring-buffer trace session so external tooling that clones rolling snapshots mid-run continues to function alongside standard system, memory, input, and UMA histogram metrics.

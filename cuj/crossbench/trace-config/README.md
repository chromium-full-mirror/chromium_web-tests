# Perfetto Trace Configs

This directory contains the Perfetto trace configuration files used by
`web-tests` benchmarks and CUJs:

- **`detailed-trace-config.template.pbtxt`** (generates **`detailed-trace-config.pbtxt`**):
  Default trace config used by most CUJs.
- **`extra-detailed-trace-config.template.pbtxt`** (generates **`extra-detailed-trace-config.pbtxt`**):
  Includes everything in `detailed-trace-config` plus an additional buffer for
  higher-overhead Chrome `toplevel` trace events.
- **`long-running-trace-config.template.pbtxt`** (generates **`long-running-trace-config.pbtxt`**):
  Lower-overhead trace config with larger ring buffers and a smaller subset of
  low-frequency UMA histograms for long-running / stress CUJs (e.g.
  `memory-pressure`, `tab-stress`, `videocall`).

## Modifying Trace Configs & Chrome UMA Histograms

**Do not edit the generated `*.pbtxt` files directly.** Instead, edit the
corresponding `*.template.pbtxt` files and regenerate the output configs.

Perfetto's `org.chromium.histogram_sample` data source requires exact histogram
names at runtime and does not natively support wildcards. To make maintaining
the config easier:

1. Edit the `*.template.pbtxt` file(s) in this directory. Inside the
   `chromium_histogram_samples` block, `histogram_name` entries support both
   exact names and wildcard patterns (`*` and `?`, e.g. `EventLatency.*`,
   `Event.ScrollJank.*`).
2. Run [`tools/update_trace_config_histograms.py`](../../../tools/update_trace_config_histograms.py)
   pointing to a local Chromium checkout (which uses Chromium's
   `tools/metrics/histograms/print_expanded_histograms.py` to expand wildcards
   and serialize the final protobuf configs):
   ```bash
   vpython3 tools/update_trace_config_histograms.py --chromium-src /path/to/chromium/src
   ```
3. If any newly added histograms have a known optimization direction
   (`LOWER_IS_BETTER` or `HIGHER_IS_BETTER`), add their prefix to
   `histogram_polarities` in
   [`cuj/crossbench/sql_packages/queries/uma_histogram_constants.sql`](../sql_packages/queries/uma_histogram_constants.sql).

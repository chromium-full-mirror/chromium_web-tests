# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
Gathers crossbench execution results and compiles them into a unified flat
metrics JSON file.

JSON Schema:
The output `metrics.json` uses a tabular (flat list) format for metrics
to maximize compatibility with data analysis pipelines (like Pandas,
BigQuery, etc.) and visualization tools, paired with top-level `"metadata"`.
Unavailable string metadata fields default to `""` (`browser_flags` defaults
to `[]` and `system_ram_bytes` defaults to `null`).

{
  "metadata": {
    "run_id": "2026-07-16_161929",
    "generated_at_utc": "2026-07-16T16:19:29Z",
    # Browser metadata (from stories/cb.results.json)
    "cr_version": "158.0.8127.36",
    "cr_channel": "beta",
    "browser_app_name": "com.chrome.beta",
    "browser_flags": ["--enable-field-trial-config"],
    # OS and DUT hardware metadata (from cb.system.details.json)
    "cr_os_name": "Android",      # 'Android', 'CrOS', 'Linux', 'Darwin', etc.
    "cr_os_version": "17",
    "android_build_fingerprint": "Generic/device_a/...",  # Android only
    "android_build_id": "AB1A.260101.001",                # Android only
    "dut_board": "device_a",      # Android or CrOS board/device
    "dut_model": "Generic Device",  # Android ro.product.model
    "hwid": "HWID-GENERIC-001",   # Android ro.boot.product.hardware.id
    "dut_sku": "SKU-GENERIC-99",  # Android hardware SKU
    "system_machine": "x64",
    "system_ram_bytes": 34359738368
  },
  "metrics": [
    {
      "test_name": "speedometer_3.1",
      # Corresponds to web-tests variant (e.g. from --variant flag)
      "variant": "default",
      "browser": "chrome_v150",
      "metric": "Score",             # The specific metric name
      "values": [36.7, 37.1],        # Array of float values
      "units": "score",
      "improvement_direction": "up"  # 'up', 'down', or ''
    },
    ...
  ]
}
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from protos.perfetto.trace_summary import file_pb2, v2_metric_pb2

from runner.test_discovery import enumerate_all_tests

_ANDROID_PKG_CHANNELS: dict[str, str] = {
    "com.android.chrome": "stable",
    "com.chrome.beta": "beta",
    "com.chrome.dev": "dev",
    "com.chrome.canary": "canary",
}


def _extract_browser_metadata(pass_dir: Path, metadata: dict[str, Any]) -> bool:
  results_file = next(pass_dir.glob("*/stories/cb.results.json"), None)
  if results_file is None:
    return False
  browser = json.loads(results_file.read_text(encoding="utf-8")).get("browser")
  if not browser:
    return False
  path = browser["path"]
  metadata["cr_version"] = browser["version"]
  metadata["cr_channel"] = _ANDROID_PKG_CHANNELS.get(path, browser["channel"])
  metadata["browser_app_name"] = (
      path if path in _ANDROID_PKG_CHANNELS else browser["app_name"])
  metadata["browser_flags"] = browser["flags"]
  return True


def _extract_system_metadata(pass_dir: Path, metadata: dict[str, Any]) -> bool:
  details_file = next(pass_dir.rglob("cb.system.details.json"), None)
  if details_file is None:
    return False
  details = json.loads(details_file.read_text(encoding="utf-8"))
  metadata["system_machine"] = details["machine"]
  if sys_mem := details.get("system_memory_bytes"):
    metadata["system_ram_bytes"] = sys_mem

  if "Android" in details:
    android = details["Android"]
    metadata["cr_os_name"] = "Android"
    metadata["cr_os_version"] = android.get("ro.build.version.release", "")
    metadata["android_build_fingerprint"] = android.get("ro.build.fingerprint",
                                                        "")
    metadata["android_build_id"] = android.get("ro.build.id", "")
    metadata["dut_board"] = (
        android.get("ro.product.board") or android.get("ro.product.device", ""))
    metadata["dut_model"] = android.get("ro.product.model", "")
    metadata["hwid"] = android.get("ro.boot.product.hardware.id", "")
    metadata["dut_sku"] = (
        android.get("ro.boot.hardware.sku") or
        android.get("ro.boot.product.hardware.sku", ""))
  elif "ChromeOS" in details:
    cros = details["ChromeOS"]
    metadata["cr_os_name"] = "CrOS"
    metadata["cr_os_version"] = cros.get("CHROMEOS_RELEASE_VERSION", "")
    metadata["dut_board"] = cros.get("CHROMEOS_RELEASE_BOARD", "")
  else:
    os_info = details["os"]
    metadata["cr_os_name"] = os_info["system"]
    metadata["cr_os_version"] = os_info["release"]

  return True


def _parse_v2_metrics(pb_file: Path, test_name: str, variant: str,
                      browser: str) -> list[dict]:

  metric_polarity = v2_metric_pb2.TraceMetricV2Spec.MetricPolarity
  metrics = []
  summary = file_pb2.TraceSummary()
  summary.ParseFromString(pb_file.read_bytes())
  for bundle in summary.metric_bundles:
    for row in bundle.row:
      metric_dimensions = []
      for dimension in row.dimension:
        dimension_field = dimension.WhichOneof("value_oneof")
        if dimension_field == "string_value":
          dim_val = dimension.string_value
        elif dimension_field == "int64_value":
          dim_val = dimension.int64_value
        elif dimension_field == "double_value":
          dim_val = dimension.double_value
        elif dimension_field == "bool_value":
          dim_val = dimension.bool_value
        else:
          dim_val = "None"
        metric_dimensions.append(str(dim_val))

      for value_i, value in enumerate(row.values):
        if value_i >= len(bundle.specs):
          continue
        if value.WhichOneof("value_oneof") == "null_value":
          continue

        spec = bundle.specs[value_i]
        polarity = spec.polarity
        if polarity == metric_polarity.HIGHER_IS_BETTER:
          imp_dir = "up"
        elif polarity == metric_polarity.LOWER_IS_BETTER:
          imp_dir = "down"
        else:
          imp_dir = ""

        val = value.double_value
        metric_name = "-".join([spec.id, *metric_dimensions])

        which_unit = spec.WhichOneof("unit_oneof")
        if which_unit == "unit":
          unit = v2_metric_pb2.TraceMetricV2Spec.MetricUnit.Name(spec.unit)
        elif which_unit == "custom_unit":
          unit = spec.custom_unit
        else:
          unit = "unknown"

        metrics.append({
            "test_name": test_name,
            "variant": variant,
            "browser": browser,
            "metric": metric_name,
            "values": [val],
            "units": unit,
            "improvement_direction": imp_dir
        })
  return metrics


def _parse_probe_json(json_file: Path, test_name: str,
                      variant: str) -> list[dict]:
  metrics = []
  with json_file.open("r", encoding="utf-8") as f:
    data = json.load(f)

  for browser, browser_data in data.items():
    if not isinstance(browser_data, dict) or "data" not in browser_data:
      continue
    for metric_name, metric_info in browser_data["data"].items():
      if not isinstance(metric_info, dict) or "values" not in metric_info:
        continue

      metrics.append({
          "test_name":
              test_name,
          "variant":
              variant,
          "browser":
              browser,
          "metric":
              metric_name,
          "values":
              metric_info["values"],
          "units":
              "score",
          "improvement_direction":
              metric_info.get("improvement_direction", "up")
      })
  return metrics


def generate_metrics_json(results_dir: Path) -> None:
  all_tests = {t.full_name: t for t in enumerate_all_tests()}
  metrics: list[dict[str, Any]] = []
  metadata: dict[str, Any] = {
      "run_id":
          results_dir.name,
      "generated_at_utc":
          dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
      "cr_version":
          "",
      "cr_channel":
          "",
      "browser_app_name":
          "",
      "browser_flags": [],
      "cr_os_name":
          "",
      "cr_os_version":
          "",
      "android_build_fingerprint":
          "",
      "android_build_id":
          "",
      "dut_board":
          "",
      "dut_model":
          "",
      "hwid":
          "",
      "dut_sku":
          "",
      "system_machine":
          "",
      "system_ram_bytes":
          None,
  }
  found_browser = False
  found_system = False

  for test_dir in sorted(results_dir.glob("*")):
    if not test_dir.is_dir() or test_dir.name not in all_tests:
      continue
    test_obj = all_tests[test_dir.name]

    for pass_dir in sorted(test_dir.glob("pass/*")):
      if not found_browser:
        found_browser = _extract_browser_metadata(pass_dir, metadata)
      if not found_system:
        found_system = _extract_system_metadata(pass_dir, metadata)

      # 1. Parse JSON probe data (press benchmarks)
      json_file = pass_dir / f"{test_obj.name}.json"
      if json_file.exists():
        metrics.extend(
            _parse_probe_json(json_file, test_obj.name, test_obj.variant))

      # 2. Parse Perfetto v2_metrics.pb
      for pb_file in sorted(pass_dir.rglob("v2_metrics.pb")):
        # Extract browser from path (e.g. <timestamp>/<browser>/...)
        rel_parts = pb_file.relative_to(pass_dir).parts
        if len(rel_parts) > 1:
          browser = rel_parts[0]
          metrics.extend(
              _parse_v2_metrics(pb_file, test_obj.name, test_obj.variant,
                                browser))

  out_file = results_dir / "metrics.json"
  with out_file.open("w", encoding="utf-8") as f:
    json.dump({"metadata": metadata, "metrics": metrics}, f, indent=2)

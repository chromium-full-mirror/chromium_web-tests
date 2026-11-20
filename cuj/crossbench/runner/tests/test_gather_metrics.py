# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

from runner.config import Benchmark
from runner.gather_metrics import generate_metrics_json


def _fake_benchmark(name: str = "speedometer_3.1") -> Benchmark:
  return Benchmark(
      name=name,
      variant="",
      path=Path(f"/fake/benchmarks/{name}"),
      probe_config=None,
      browser_flags=Path("/fake/flags.hjson"),
      extensions=None,
      crossbench_args="",
  )


def test_generate_metrics_json_press_benchmark_without_perfetto(
    tmp_path: Path) -> None:
  results_dir = tmp_path / "press-repro_2026-11-20_100000"
  pass_dir = results_dir / "speedometer_3.1" / "pass" / "2026-11-20_100005"
  stories_dir = pass_dir / "chrome_v158_com.chrome.beta" / "stories"
  stories_dir.mkdir(parents=True)

  (pass_dir / "speedometer_3.1.json").write_text(
      json.dumps({
          "chrome_v158_com.chrome.beta": {
              "data": {
                  "Score": {
                      "values": [38.4, 39.1],
                      "improvement_direction": "up",
                  }
              }
          }
      }),
      encoding="utf-8",
  )

  (stories_dir / "cb.results.json").write_text(
      json.dumps({
          "browser": {
              "app_name": "com.chrome",
              "version": "158.0.8127.36",
              "channel": "stable",
              "flags": [
                  "--allow-background-interventions",
                  "--enable-field-trial-config",
              ],
              "path": "com.chrome.beta",
          }
      }),
      encoding="utf-8",
  )

  with mock.patch(
      "runner.gather_metrics.enumerate_all_tests",
      return_value=[_fake_benchmark("speedometer_3.1")],
  ):
    generate_metrics_json(results_dir)

  output = json.loads((results_dir / "metrics.json").read_text("utf-8"))
  meta = output["metadata"]

  assert meta["run_id"] == "press-repro_2026-11-20_100000"
  assert meta["generated_at_utc"].endswith("Z")
  assert meta["cr_version"] == "158.0.8127.36"
  assert meta["cr_channel"] == "beta"
  assert meta["browser_app_name"] == "com.chrome.beta"
  assert meta["browser_flags"] == [
      "--allow-background-interventions",
      "--enable-field-trial-config",
  ]
  assert output["metrics"] == [{
      "test_name": "speedometer_3.1",
      "variant": "",
      "browser": "chrome_v158_com.chrome.beta",
      "metric": "Score",
      "values": [38.4, 39.1],
      "units": "score",
      "improvement_direction": "up",
  }]


def test_generate_metrics_json_missing_optional_files(tmp_path: Path) -> None:
  results_dir = tmp_path / "2026-11-20_130000"
  pass_dir = results_dir / "speedometer_3.1" / "pass" / "2026-11-20_130005"
  pass_dir.mkdir(parents=True)

  (pass_dir / "speedometer_3.1.json").write_text(
      json.dumps(
          {"chrome_v158": {
              "data": {
                  "Score": {
                      "values": [40.0],
                  }
              }
          }}),
      encoding="utf-8",
  )

  with mock.patch(
      "runner.gather_metrics.enumerate_all_tests",
      return_value=[_fake_benchmark("speedometer_3.1")],
  ):
    generate_metrics_json(results_dir)

  output = json.loads((results_dir / "metrics.json").read_text("utf-8"))
  meta = output["metadata"]

  assert meta["run_id"] == "2026-11-20_130000"
  assert meta["generated_at_utc"].endswith("Z")
  assert meta["cr_version"] == ""
  assert meta["cr_channel"] == ""
  assert meta["browser_app_name"] == ""
  assert meta["browser_flags"] == []
  assert output["metrics"][0]["values"] == [40.0]

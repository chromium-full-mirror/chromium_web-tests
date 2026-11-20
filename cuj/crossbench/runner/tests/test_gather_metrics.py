# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

from runner.config import Benchmark, RunConfig, TargetPlatform
from runner.gather_metrics import generate_metrics_json


def _make_run_config(
    results_root: Path,
    platform: TargetPlatform = TargetPlatform.ANDROID,
    browser: str | None = None,
    tag: str | None = None,
) -> RunConfig:
  return RunConfig(
      platform=platform,
      device="localhost:5555",
      adb_bin=None,
      browser=browser,
      secrets=None,
      wpr=None,
      upload=False,
      results_root=results_root,
      tag=tag,
      debug=False,
      dry_run=False,
      no_symlinks=True,
      list_tests=False,
      tests=[],
  )


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

  fingerprint = (
      "Generic/device_a/device_a:17/AB1A.260101.001/12345678:userdebug/dev-keys"
  )
  (pass_dir / "cb.system.details.json").write_text(
      json.dumps({
          "machine": "x64",
          "system_memory_bytes": 32 * 1024**3,
          "os": {
              "system": "Linux",
              "release": "6.18.0-generic",
          },
          "Android": {
              "ro.build.fingerprint": fingerprint,
              "ro.build.id": "AB1A.260101.001",
              "ro.build.version.release": "17",
              "ro.product.device": "device_a",
              "ro.product.model": "Generic Device 14",
              "ro.boot.product.hardware.id": "HWID-GENERIC-001",
              "ro.boot.hardware.sku": "SKU-GENERIC-99",
          },
      }),
      encoding="utf-8",
  )

  run_cfg = _make_run_config(
      results_dir,
      platform=TargetPlatform.ANDROID,
      browser="chrome-latest-beta",
      tag="press-repro",
  )

  with mock.patch(
      "runner.gather_metrics.enumerate_all_tests",
      return_value=[_fake_benchmark("speedometer_3.1")],
  ):
    generate_metrics_json(results_dir, run_config=run_cfg)

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
  assert meta["cr_os_name"] == "Android"
  assert meta["cr_os_version"] == "17"
  assert meta["android_build_fingerprint"] == fingerprint
  assert meta["android_build_id"] == "AB1A.260101.001"
  assert meta["dut_board"] == "device_a"
  assert meta["dut_model"] == "Generic Device 14"
  assert meta["hwid"] == "HWID-GENERIC-001"
  assert meta["dut_sku"] == "SKU-GENERIC-99"
  assert meta["system_machine"] == "x64"
  assert meta["system_ram_bytes"] == 32 * 1024**3
  assert meta["platform"] == "adb"
  assert meta["requested_browser"] == "chrome-latest-beta"
  assert meta["tag"] == "press-repro"
  assert output["metrics"] == [{
      "test_name": "speedometer_3.1",
      "variant": "",
      "browser": "chrome_v158_com.chrome.beta",
      "metric": "Score",
      "values": [38.4, 39.1],
      "units": "score",
      "improvement_direction": "up",
  }]


def test_generate_metrics_json_chromeos_press_benchmark(tmp_path: Path) -> None:
  results_dir = tmp_path / "2026-11-20_110000"
  pass_dir = results_dir / "jetstream_2.2" / "pass" / "2026-11-20_110005"
  stories_dir = pass_dir / "chrome_v151__opt_google_chrome_chrome" / "stories"
  stories_dir.mkdir(parents=True)

  (pass_dir / "jetstream_2.2.json").write_text(
      json.dumps({
          "chrome_v151__opt_google_chrome_chrome": {
              "data": {
                  "Total": {
                      "values": [245.5],
                  }
              }
          }
      }),
      encoding="utf-8",
  )
  (stories_dir / "cb.results.json").write_text(
      json.dumps({
          "browser": {
              "app_name": "chrome",
              "version": "151.0.7922.222",
              "channel": "dev",
              "path": "/opt/google/chrome/chrome",
              "flags": [],
          }
      }),
      encoding="utf-8",
  )
  (pass_dir / "cb.system.details.json").write_text(
      json.dumps({
          "machine": "x64",
          "system_memory_bytes": 8093872128,
          "os": {
              "system": "Linux",
              "release": "6.6.119",
          },
          "ChromeOS": {
              "CHROMEOS_RELEASE_BOARD": "generic_board",
              "CHROMEOS_RELEASE_VERSION": "16733.60.0",
          },
      }),
      encoding="utf-8",
  )

  run_cfg = _make_run_config(
      results_dir, platform=TargetPlatform.CHROME_OS, browser=None, tag=None)

  with mock.patch(
      "runner.gather_metrics.enumerate_all_tests",
      return_value=[_fake_benchmark("jetstream_2.2")],
  ):
    generate_metrics_json(results_dir, run_config=run_cfg)

  meta = json.loads(
      (results_dir / "metrics.json").read_text("utf-8"))["metadata"]
  assert meta["cr_version"] == "151.0.7922.222"
  assert meta["cr_channel"] == "dev"
  assert meta["browser_app_name"] == "chrome"
  assert meta["cr_os_name"] == "CrOS"
  assert meta["cr_os_version"] == "16733.60.0"
  assert meta["android_build_fingerprint"] == ""
  assert meta["android_build_id"] == ""
  assert meta["dut_board"] == "generic_board"
  assert meta["dut_model"] == ""
  assert meta["hwid"] == ""
  assert meta["dut_sku"] == ""
  assert meta["system_ram_bytes"] == 8093872128
  assert meta["platform"] == "cros"
  assert meta["requested_browser"] == ""
  assert meta["tag"] == ""


def test_generate_metrics_json_missing_optional_files(tmp_path: Path) -> None:
  results_dir = tmp_path / "2026-11-20_130000"
  pass_dir = results_dir / "speedometer_3.1" / "pass" / "2026-11-20_130005"
  pass_dir.mkdir(parents=True)

  (pass_dir / "speedometer_3.1.json").write_text(
      json.dumps({"chrome_v158": {
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
  assert meta["cr_os_name"] == ""
  assert meta["dut_board"] == ""
  assert meta["dut_model"] == ""
  assert meta["system_ram_bytes"] is None
  assert output["metrics"][0]["values"] == [40.0]

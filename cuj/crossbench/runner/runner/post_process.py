# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import csv
import json
import logging
import subprocess
import sys
from pathlib import Path


def _parse_metrics_row(key: str, value: dict) -> dict | None:
  try:
    key_dict = json.loads(key)
  except json.JSONDecodeError:
    return None

  return {
      "label": key_dict.get("label", ""),
      "metric_name": key_dict.get("metric_name", ""),
      "run_id": key_dict.get("run_id", ""),
      "test_name": key_dict.get("test_name", ""),
      "variant": key_dict.get("variant", ""),
      "improvement_direction": value.get("improvement_direction", ""),
      "units": value.get("units", ""),
      "value": value.get("value", 0.0),
  }


def generate_metrics_csv(results_dir: Path) -> None:
  metrics_file = results_dir / "metrics.json"
  if not metrics_file.exists():
    logging.warning("Cannot generate metrics CSV: %s does not exist.",
                    metrics_file)
    return

  with metrics_file.open("r", encoding="utf-8") as f:
    data = json.load(f)

  results_obj = data.get("results", {})
  if not results_obj:
    logging.warning("No results to convert to CSV.")
    return

  rows = []
  for key, value in results_obj.items():
    if row := _parse_metrics_row(key, value):
      rows.append(row)

  if not rows:
    logging.warning("No valid rows for metrics CSV.")
    return

  csv_file = results_dir / "metrics.csv"
  with csv_file.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)


def do_upload(results_dir: Path, uploader: Path | None = None) -> None:
  csv_file = results_dir / "metrics.csv"
  if not csv_file.exists():
    logging.error("Cannot upload: %s does not exist.", csv_file)
    return

  if not uploader:
    logging.warning("No --uploader specified. Skipping upload.")
    return

  if not uploader.exists():
    logging.error("Uploader script %s does not exist.", uploader)
    return

  logging.info("Running uploader script: %s", uploader)
  subprocess.run([sys.executable, str(uploader), str(results_dir)], check=True)

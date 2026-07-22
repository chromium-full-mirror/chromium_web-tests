# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import getpass
import logging
import subprocess
from pathlib import Path

from runner.gather_metrics import generate_metrics_json


def do_upload(results_dir: Path, tag: str | None = None) -> None:
  json_file = results_dir / "metrics.json"
  if not json_file.exists():
    logging.info("metrics.json not found, generating...")
    generate_metrics_json(results_dir)

  if not json_file.exists():
    logging.error("Cannot upload: %s does not exist even after generation.",
                  json_file)
    return

  username = getpass.getuser()
  filename = results_dir.name
  if tag and not filename.startswith(f"{tag}_"):
    filename = f"{tag}_{filename}"

  gcs_dest = f"gs://web_tests_metrics/{username}/{filename}.json"
  logging.info("Uploading %s to %s", json_file, gcs_dest)

  try:
    subprocess.run(["gcloud", "storage", "cp",
                    str(json_file), gcs_dest],
                   check=True)
    logging.info("Successfully uploaded metrics.")
  except subprocess.CalledProcessError as e:
    logging.error("Failed to upload metrics.json: %s", e)

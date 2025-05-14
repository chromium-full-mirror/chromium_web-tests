#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
from pathlib import Path
import subprocess
import sys


def crossbench_dry_run() -> None:
  web_tests_root = Path(__file__).resolve().parent
  runner_path = web_tests_root / "cuj" / "crossbench" / "runner"

  os.chdir(runner_path)

  try:
    subprocess.run([
        "poetry", "run", "python", "run.py", "--platform", "local", "--dry-run"
    ],
                   check=True,
                   capture_output=False)
  except subprocess.CalledProcessError:
    print("Crossbench dry run failed!")
    sys.exit(1)


if __name__ == "__main__":
  crossbench_dry_run()

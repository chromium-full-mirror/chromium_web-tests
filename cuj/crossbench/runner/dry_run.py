#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from pathlib import Path
import sys

# This script is run by PRESUBMIT.py which uses vpython and
# thus cannot rely on poetry setting up the crossbench dependency properly.
#
# Up-to-date crossbench is not available as a vpython wheel,
# so manually add the crossbench included as part of web-tests here.
web_tests_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(web_tests_root / "third_party" / "crossbench"))

# pylint: disable=wrong-import-position
from runner.cli import runner_cli


def dry_run():
  runner_cli(argv=["--platform=local", "--dry-run"])


if __name__ == "__main__":
  dry_run()

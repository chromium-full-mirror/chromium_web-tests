#!/usr/bin/env vpython3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import sys

# This is the earliest entrypoint into the runner.
# Try to import some simple crossbench package here to
# check that crossbench is setup properly.
try:
  # pylint: disable=unused-import
  from crossbench.types import Json
except ImportError:
  logging.error("Failed to import crossbench. "
                "Have you run 'gclient sync' and 'poetry install'?")
  sys.exit(-1)

from runner.cli import runner_cli

if __name__ == "__main__":
  argv = sys.argv
  runner_cli(argv[1:])

#!/usr/bin/env vpython3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys

from runner.cli import runner_cli

if __name__ == "__main__":
  argv = sys.argv
  runner_cli(argv[1:])

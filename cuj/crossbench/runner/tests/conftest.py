# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import sys
from pathlib import Path

RUNNER_ROOT = Path(__file__).resolve().parent.parent
WEB_TESTS_ROOT = RUNNER_ROOT.parent.parent.parent

for extra_path in (
    RUNNER_ROOT,
    WEB_TESTS_ROOT / "third_party" / "crossbench",
    WEB_TESTS_ROOT / "protoc" / "gen",
):
  path_str = str(extra_path)
  if path_str not in sys.path:
    sys.path.insert(0, path_str)

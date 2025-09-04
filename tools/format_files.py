#!/usr/bin/env vpython3

# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable

from immutabledict import immutabledict

WEB_TESTS_ROOT = Path(__file__).resolve().parent.parent
NODE_BIN = (
    WEB_TESTS_ROOT / "third_party" / "node" / "linux" / "node-linux-x64" /
    "bin" / "node")
HJSON_JS_BIN = WEB_TESTS_ROOT / "third_party" / "hjson_js" / "bin" / "hjson"


def format_sql_file(sql_file: Path) -> None:
  subprocess.run([
      str(WEB_TESTS_ROOT / "third_party" / "perfetto" / "tools" /
          "format-sql-sources"),
      str(sql_file)
  ],
                 check=True,
                 cwd=WEB_TESTS_ROOT / "third_party" / "perfetto",
                 capture_output=True)


def format_hjson_file(hjson_file: Path) -> None:
  formatted_file = subprocess.run(
      [
          NODE_BIN, HJSON_JS_BIN, "-rt", "-sl", "-nocol", "-cond=0",
          str(hjson_file)
      ],
      check=True,
      capture_output=True).stdout.decode(encoding="utf-8")
  hjson_file.write_text(formatted_file, encoding="utf-8")


FORMATTERS: immutabledict[str, Callable] = immutabledict({
    ".sql": format_sql_file,
    ".hjson": format_hjson_file
})


def format_files(files: list[str]) -> None:
  logging.getLogger().setLevel(logging.INFO)

  for file in files:
    full_path: Path = Path(file).resolve()

    if full_path.suffix not in FORMATTERS:
      logging.warning("No formatter for file: %s", str(full_path))
      continue

    logging.info("Formatting: %s", str(full_path))
    try:
      FORMATTERS[full_path.suffix](full_path)
    except subprocess.CalledProcessError as e:
      msg = e.stderr.decode(encoding="utf-8")
      logging.error("Failed to format file (%s): %s", str(full_path), msg)


if __name__ == "__main__":
  format_files(sys.argv[1:])

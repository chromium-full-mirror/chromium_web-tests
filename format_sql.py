#!/usr/bin/env vpython3

# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import subprocess
import sys
from pathlib import Path


def format_sql() -> None:
  logging.getLogger().setLevel(logging.INFO)

  logging.warning("This script will format *every* sql file in web-tests "
                  "and does not scope changes to the current commit.")
  do_format = input("To continue, type 'CONTINUE'\n")
  if do_format != "CONTINUE":
    sys.exit()

  web_tests_root = Path(__file__).resolve().parent

  for sql_file in (web_tests_root / "cuj").rglob("*.sql"):
    try:
      subprocess.run([
          str(web_tests_root / "third_party" / "perfetto" / "tools" /
              "format-sql-sources"),
          str(sql_file)
      ],
                     cwd=web_tests_root / "third_party" / "perfetto",
                     check=True)
    except subprocess.CalledProcessError as e:
      error = e.stderr.decode(encoding="utf=8")
      logging.error("Failed to parse SQL file (%s): %s", str(sql_file), error)
      continue


if __name__ == "__main__":
  format_sql()

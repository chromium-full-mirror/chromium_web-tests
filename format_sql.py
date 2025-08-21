#!/usr/bin/env vpython3

# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import sys
from pathlib import Path

import sqlparse


def format_sql() -> None:
  logging.getLogger().setLevel(logging.INFO)

  logging.warning("This script will format *every* sql file in web-tests "
                  "and does not scope changes to the current commit.")
  do_format = input("To continue, type 'CONTINUE'\n")
  if do_format != "CONTINUE":
    sys.exit()

  web_tests_root = Path(__file__).resolve().parent

  for sql_file in web_tests_root.glob("cuj/**/*.sql"):
    formatted = sqlparse.format(
        sql_file.read_text(), reindent=False, keyword_case="upper")
    sql_file.write_text(formatted, encoding="utf-8")


if __name__ == "__main__":
  format_sql()

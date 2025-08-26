#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import platform
import subprocess
from pathlib import Path


USE_PYTHON3 = True


def CheckChange(input_api, output_api):
  tests = []
  results = []
  modified_hjson_files: list[str] | None = ModifiedFiles(
      input_api, False, filename_pattern="*.hjson")
  modified_sql_files: list[str] | None = ModifiedFiles(
      input_api, False, filename_pattern="*.sql")
  # ---------------------------------------------------------------------------
  # Validate the vpython spec:
  # ---------------------------------------------------------------------------
  if platform.system() in ("Linux", "Darwin"):
    tests += input_api.canned_checks.CheckVPythonSpec(input_api, output_api)

  # ---------------------------------------------------------------------------
  # License header checks:
  # ---------------------------------------------------------------------------
  files_to_check = list(input_api.DEFAULT_FILES_TO_CHECK) + [
      r".+\.hjson$",
      r".+\.sql$",
  ]

  results += input_api.canned_checks.CheckLicense(
      input_api,
      output_api,
      source_file_filter=lambda x: input_api.FilterSourceFile(
          x, files_to_check=files_to_check))

  # ---------------------------------------------------------------------------
  # hjson:
  # ---------------------------------------------------------------------------
  FormatFiles(input_api, output_api, results, modified_hjson_files,
              FormatHjsonFile)

  # ---------------------------------------------------------------------------
  # sql:
  # ---------------------------------------------------------------------------
  FormatFiles(input_api, output_api, results, modified_sql_files, FormatSqlFile)

  # ---------------------------------------------------------------------------
  # crossbench:
  # ---------------------------------------------------------------------------
  dry_run_py_path = str(
      Path(input_api.change.RepositoryRoot()) / "cuj" / "crossbench" /
      "runner" / "run.py")
  tests.append(
      input_api.Command(
          name="crossbench dry run",
          cmd=[
              input_api.python3_executable, dry_run_py_path, "--platform=local",
              "--dry-run"
          ],
          message=output_api.PresubmitError,
          kwargs={},
          python3=True,
      ))

  # ---------------------------------------------------------------------------
  # Pylint:
  # ---------------------------------------------------------------------------
  tests += input_api.canned_checks.GetPylint(
      input_api,
      output_api,
      files_to_check=[r"^[^\.]+\.py$"],
      pylintrc=".pylintrc",
      version="3.2")

  # ---------------------------------------------------------------------------
  # Run all test
  # ---------------------------------------------------------------------------
  results += input_api.RunTests(tests)
  return results


def ModifiedFiles(input_api, on_commit: bool,
                  filename_pattern: str) -> list[str] | None:
  if on_commit:
    return None
  files = [file.AbsoluteLocalPath() for file in input_api.AffectedFiles()]
  files_to_check = []
  for file_path in files:
    if not input_api.fnmatch.fnmatch(file_path, filename_pattern):
      continue
    if not input_api.os_path.exists(file_path):
      continue
    file_path = input_api.os_path.relpath(file_path,
                                          input_api.PresubmitLocalPath())
    files_to_check.append(file_path)
  return files_to_check


def FormatFiles(input_api, output_api, results, modified_files, format_func):
  for file in (modified_files or []):
    full_path = Path(input_api.change.RepositoryRoot()) / file

    original_contents = input_api.ReadFile(str(full_path), "r")

    try:
      format_func(input_api, full_path)
      formatted_contents = input_api.ReadFile(str(full_path), "r")
    except ValueError as e:
      results.append(
          output_api.PresubmitPromptWarning(
              "Malformed file:", items=[str(full_path)], long_text=str(e)))
      continue

    if original_contents != formatted_contents:
      results.append(
          output_api.PresubmitPromptWarning(
              "Unformatted file:",
              items=[str(full_path)],
              long_text="Please update your commit with the formatted file."))


def FormatHjsonFile(input_api, hjson_file: Path) -> None:
  node_bin = str(
      Path(input_api.change.RepositoryRoot()) /
      "third_party/node/linux/node-linux-x64/bin/node")

  hjson_js_bin = str(
      Path(input_api.change.RepositoryRoot()) / "third_party" / "hjson_js" /
      "bin" / "hjson")

  try:
    formatted = subprocess.run(
        [
            node_bin, hjson_js_bin, "-rt", "-sl", "-nocol", "-cond=0",
            str(hjson_file)
        ],
        check=True,
        capture_output=True).stdout.decode(encoding="utf-8")
    hjson_file.write_text(formatted)
  except subprocess.CalledProcessError as e:
    error = e.stderr.decode(encoding="utf=8")
    raise ValueError(f"Failed to parse hjson file: {error}") from e


def FormatSqlFile(input_api, sql_file: Path) -> None:
  perfetto_sql_formatter = str(
      Path(input_api.change.RepositoryRoot()) / "third_party" / "perfetto" /
      "tools" / "format-sql-sources")
  try:
    subprocess.run(
        [perfetto_sql_formatter, str(sql_file)],
        check=True,
        capture_output=True,
        cwd=(Path(input_api.change.RepositoryRoot()) / "third_party" /
             "perfetto"))
  except subprocess.CalledProcessError as e:
    error = e.stderr.decode(encoding="utf=8")
    raise ValueError(f"Failed to parse sql file: {error}") from e


def CheckChangeOnUpload(input_api, output_api):
  return CheckChange(input_api, output_api)


def CheckChangeOnCommit(input_api, output_api):
  return CheckChange(input_api, output_api)

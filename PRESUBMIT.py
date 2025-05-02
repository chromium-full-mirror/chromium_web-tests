#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import platform

import hjson

USE_PYTHON3 = True


def CheckChange(input_api, output_api):
  tests = []
  results = []
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
  bad_hjson_files = []

  for hjson_file in input_api.AffectedSourceFiles(
      lambda x: input_api.FilterSourceFile(x, files_to_check=[r".+\.hjson$"])):
    try:
      contents = input_api.ReadFile(hjson_file, "r")
      hjson.loads(contents)
    except ValueError:
      bad_hjson_files.append(hjson_file)

  if bad_hjson_files:
    results.append(
        output_api.PresubmitPromptWarning(
            "Invalid hjson files:", items=bad_hjson_files))

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


def CheckChangeOnUpload(input_api, output_api):
  return CheckChange(input_api, output_api)


def CheckChangeOnCommit(input_api, output_api):
  return CheckChange(input_api, output_api)

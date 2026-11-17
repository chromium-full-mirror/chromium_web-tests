#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

USE_PYTHON3 = True

SOURCE_SKIP_RE = [r"^protoc/gen.*", r"^third_party/.*"]


def GlobalSkipChecks(input_api, file_path: str):
  if input_api.fnmatch.fnmatch(file_path, "*protoc/gen/*"):
    return True
  if input_api.fnmatch.fnmatch(file_path, "*third_party/*"):
    return True
  return False


def CheckChange(input_api, output_api):
  tests = []
  results = []
  modified_py_files: list[str] | None = ModifiedFiles(
      input_api, filename_pattern="*.py")
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
      r".+\.css$",
      r".+\.html$",
  ]

  results += input_api.canned_checks.CheckLicense(
      input_api,
      output_api,
      source_file_filter=lambda x: input_api.FilterSourceFile(
          x, files_to_check=files_to_check))

  # ---------------------------------------------------------------------------
  # Pylint:
  # ---------------------------------------------------------------------------
  tests += input_api.canned_checks.GetPylint(
      input_api,
      output_api,
      files_to_check=[r"^[^\.]+\.py$"],
      files_to_skip=SOURCE_SKIP_RE,
      pylintrc=".pylintrc",
      version="3.2")

  # ---------------------------------------------------------------------------
  # Pyrefly:
  # ---------------------------------------------------------------------------
  typer_files_to_check: list[str] = TyperFilesToCheck(input_api,
                                                      modified_py_files)
  if typer_files_to_check and (platform.system() != "Linux" or
                               platform.machine() == "x86_64"):
    repo_root = Path(input_api.change.RepositoryRoot())
    tests.append(
        input_api.Command(
            name="pyrefly",
            cmd=[
                input_api.python3_executable,
                "-m",
                "pyrefly",
                "check",
                f"--python-interpreter-path={input_api.python3_executable}",
                f"--search-path={repo_root / 'third_party' / 'crossbench'}",
                f"--search-path={repo_root / 'protoc' / 'gen'}",
            ] + typer_files_to_check,
            message=output_api.PresubmitError,
            kwargs={},
            python3=True,
        ))

  # ---------------------------------------------------------------------------
  # JS eslint:
  # ---------------------------------------------------------------------------
  modified_js_files: list[str] | None = ModifiedFiles(
      input_api, filename_pattern="*.js")
  tests.append(
      input_api.Command(
          name="eslint",
          cmd=[
              input_api.python3_executable,
              str(
                  Path(input_api.change.RepositoryRoot()) / "tools" /
                  "eslint.py"),
          ] + (modified_js_files if modified_js_files else []),
          message=output_api.PresubmitError,
          kwargs={},
          python3=True,
      ))

  # ---------------------------------------------------------------------------
  # Web Tests Analyzer Unit Tests:
  # ---------------------------------------------------------------------------
  tests.append(
      input_api.Command(
          name="analysis-tool tests",
          cmd=[
              str(
                  Path(input_api.change.RepositoryRoot()) / "third_party" /
                  "crossbench" / "third_party" / "node" / "linux" /
                  "node-linux-x64" / "bin" / "node"),
              "--test",
              "analysis/**/*.test.js",
          ],
          message=output_api.PresubmitError,
          kwargs={},
          python3=False,
      ))

  # ---------------------------------------------------------------------------
  # isort:
  # ---------------------------------------------------------------------------
  SortImports(input_api, output_api, results, modified_py_files)

  # ---------------------------------------------------------------------------
  # format all supported files:
  # ---------------------------------------------------------------------------
  FormatFiles(input_api, output_api, results,
              ModifiedFiles(input_api, filename_pattern="*"))

  # ---------------------------------------------------------------------------
  # CUJ README sync checks:
  # ---------------------------------------------------------------------------
  CheckCujReadmeModified(input_api, output_api, results)
  tests.append(
      input_api.Command(
          name="check-cuj-readmes unit tests",
          cmd=[
              input_api.python3_executable,
              "-m",
              "pytest",
              str(
                  Path(input_api.change.RepositoryRoot()) / "tools" /
                  "check_cuj_readmes_test.py"),
          ],
          message=output_api.PresubmitError,
          kwargs={},
          python3=True,
      ))
  tests.append(
      input_api.Command(
          name="cuj-readme-sync",
          cmd=[
              input_api.python3_executable,
              str(
                  Path(input_api.change.RepositoryRoot()) / "tools" /
                  "check_cuj_readmes.py"),
          ],
          message=output_api.PresubmitError,
          kwargs={},
          python3=True,
      ))

  # ---------------------------------------------------------------------------
  # crossbench:
  # ---------------------------------------------------------------------------
  runner_path = str(
      Path(input_api.change.RepositoryRoot()) / "cuj" / "crossbench" /
      "runner" / "run.py")
  tests.append(
      input_api.Command(
          name="crossbench dry run",
          cmd=[
              input_api.python3_executable,
              runner_path,
              "--platform=local",
              "--dry-run",
              "--out-dir",
              "/tmp",
              # TODO(b/531933642): Loadline and Web power are incompatible with
              # --dry-run, as they run with multiple browser sessions.
              # alice has no page-config.hjson and requires --page-config.
              "--tests",
              "^(?!.*loadline|web-power|alice).*$"
          ],
          message=output_api.PresubmitError,
          kwargs={},
          python3=True,
      ))

  # ---------------------------------------------------------------------------
  # Run all test
  # ---------------------------------------------------------------------------
  results += input_api.RunTests(tests)
  return results


def ModifiedFiles(input_api, filename_pattern: str) -> list[str] | None:
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


def TyperFilesToCheck(input_api,
                      modified_py_files: list[str] | None) -> list[str]:
  typer_files_to_check = {"PRESUBMIT.py"}
  if modified_py_files:
    typer_files_to_check.update(modified_py_files)

  result = []
  for file in typer_files_to_check:
    if GlobalSkipChecks(input_api, file):
      continue
    result.append(file)
  return result


def SortImports(input_api, output_api, results, modified_py_files):
  for py_file in (modified_py_files or []):
    full_py_path = Path(input_api.change.RepositoryRoot()) / py_file
    original_contents = input_api.ReadFile(str(full_py_path), "r")
    subprocess.run([input_api.python_executable, "-m", "isort", full_py_path],
                   check=True)
    formatted_contents = input_api.ReadFile(str(full_py_path), "r")
    if original_contents != formatted_contents:
      results.append(
          output_api.PresubmitPromptWarning(
              "Unsorted python imports in file:",
              items=[str(full_py_path)],
              long_text="Please update your commit with the formatted file."))


def FormatFiles(input_api, output_api, results, modified_files):
  repo_root = Path(input_api.change.RepositoryRoot())
  formatter = repo_root / "tools" / "format_files.py"

  for file in (modified_files or []):
    full_path = repo_root / file
    original_contents = input_api.ReadFile(str(full_path), "r")

    try:
      subprocess.run(
          [input_api.python_executable,
           str(formatter),
           str(full_path)],
          check=True,
          capture_output=True)
      formatted_contents = input_api.ReadFile(str(full_path), "r")
    except subprocess.CalledProcessError as e:
      results.append(
          output_api.PresubmitPromptWarning(
              "Failed to format file:",
              items=[str(full_path)],
              long_text=str(e)))
      continue

    if original_contents != formatted_contents:
      results.append(
          output_api.PresubmitPromptWarning(
              "Unformatted file:",
              items=[str(full_path)],
              long_text="Please update your commit with the formatted file."))


def CheckCujReadmeModified(input_api, output_api, results) -> None:
  repo_root = Path(input_api.change.RepositoryRoot())
  cujs_with_test_changes: set[str] = set()
  cujs_with_readme_changes: set[str] = set()

  for affected_file in input_api.AffectedFiles(include_deletes=True):
    parts = Path(affected_file.LocalPath()).parts
    if len(parts) < 4 or parts[:3] != ("cuj", "crossbench", "cujs"):
      continue
    cuj_name = parts[3]
    if not (repo_root / "cuj" / "crossbench" / "cujs" / cuj_name).is_dir():
      continue
    if len(parts) == 5 and parts[4] == "README.md":
      cujs_with_readme_changes.add(cuj_name)
    else:
      cujs_with_test_changes.add(cuj_name)

  unupdated_cujs = sorted(cujs_with_test_changes - cujs_with_readme_changes)
  if unupdated_cujs:
    results.append(
        output_api.PresubmitPromptWarning(
            "CUJ files were modified without updating their README.md:",
            items=[
                f"cuj/crossbench/cujs/{cuj}/README.md" for cuj in unupdated_cujs
            ],
            long_text=(
                "Please verify that each affected CUJ's README.md still "
                "accurately describes its variants, workflow, and metrics/"
                "invariants (if this change only heals selectors without "
                "changing test behavior, you may proceed)."),
        ))


def CheckChangeOnUpload(input_api, output_api):
  return CheckChange(input_api, output_api)


def CheckChangeOnCommit(input_api, output_api):
  return CheckChange(input_api, output_api)

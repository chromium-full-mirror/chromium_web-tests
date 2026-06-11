# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import logging
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime as dt
from pathlib import Path
from typing import Callable, Type, TypeVar

import debugpy
from runner.config import (Benchmark, CliConfig, Cuj, RunConfig, Test,
                           TestGroup, TestGroupConfig, TestInvocation)
from runner.logging import setup_logging
from runner.paths import BENCHMARKS, CUJS, RESULTS, WEB_TESTS_ROOT
from runner.runner import run_test


def is_probe_config(file: Path) -> bool:
  return file.name.endswith("probe-config.hjson")


def is_page_config(file: Path) -> bool:
  return file.name.endswith("page-config.hjson")


def get_test_variant(config_file: Path) -> str:
  name_sections: list[str] = config_file.name.split(".")

  if len(name_sections) <= 2:
    return ""

  return name_sections[0]


def get_test_variants(test_path: Path,
                      defines_variant: Callable[[Path], bool]) -> set[str]:
  variants: set[str] = set()

  for config_file in test_path.iterdir():
    if not defines_variant(config_file):
      continue

    variant: str = get_test_variant(config_file)
    variants.add(variant)

  if not variants:
    variants.add("")

  return variants


def get_variant_config_file(test_path: Path, config_file_basename: str,
                            variant: str) -> Path | None:
  config_file = test_path / f"{variant}.{config_file_basename}"

  if config_file.is_file():
    return config_file

  config_file = test_path / config_file_basename

  if config_file.is_file():
    return config_file

  return None


TestClass = TypeVar("TestClass", bound=Test)


def enumerate_tests(test_base_path: Path, defines_variant: Callable[[Path],
                                                                    bool],
                    test_class: Type[TestClass]) -> list[TestClass]:
  tests: list[TestClass] = []
  for test_path in test_base_path.iterdir():
    if not test_path.is_dir():
      continue

    variants: set[str] = get_test_variants(test_path, defines_variant)

    for variant in variants:
      page_config = get_variant_config_file(test_path, "page-config.hjson",
                                            variant)
      probe_config = get_variant_config_file(test_path, "probe-config.hjson",
                                             variant)
      browser_flags = get_variant_config_file(test_path, "browser-flags.hjson",
                                              variant)
      if browser_flags is None:
        raise ValueError(f"Missing browser flags for test: {test_path}")

      extensions = get_variant_config_file(test_path, "extensions.hjson",
                                           variant)
      cb_args_file = get_variant_config_file(test_path, "cb-args", variant)
      cb_args = ""

      if cb_args_file and cb_args_file.is_file():
        cb_args = cb_args_file.read_text()

      cb_args = cb_args.replace("$[WEB_TESTS]", str(WEB_TESTS_ROOT))

      tests.append(
          test_class(
              name=test_path.name,
              variant=variant,
              path=test_path,
              probe_config=probe_config,
              browser_flags=browser_flags,
              extensions=extensions,
              crossbench_args=cb_args,
              page_config=page_config))

  return tests


def enumerate_all_tests() -> list[Test]:
  tests: list[Test] = []
  tests.extend(enumerate_tests(CUJS, is_page_config, Cuj))
  tests.extend(enumerate_tests(BENCHMARKS, is_probe_config, Benchmark))
  return tests


def generate_test_invocations(groups: list[TestGroup],
                              all_tests: list[Test]) -> list[TestInvocation]:
  test_invocations: list[TestInvocation] = []

  for group in groups:
    test_match = any(
        re.fullmatch(group.filter_regex, test.name) for test in all_tests)
    variant_match = any(
        re.fullmatch(group.variants_filter_regex, test.variant)
        for test in all_tests)

    if not test_match:
      logging.warning("No test found matching filter '%s'", group.filter_regex)

    if not variant_match:
      logging.warning("No test found matching variant filter '%s'",
                      group.variants_filter_regex)

  for test in all_tests:
    for group in groups:
      if re.fullmatch(group.filter_regex, test.name) and re.fullmatch(
          group.variants_filter_regex, test.variant):
        test_invocations.append(
            TestInvocation(test, group.min_successes,
                           group.max_consecutive_failures, group.playback,
                           group.setup_delay, group.startup_delay))

  return test_invocations


def _print_tests_tree(filter_test_name: str | None = None) -> bool:
  tests_by_name = defaultdict(list)
  for test in enumerate_all_tests():
    if filter_test_name and test.name != filter_test_name:
      continue
    tests_by_name[test.name].append(
        test.variant if test.variant else "<default>")

  if not tests_by_name:
    if filter_test_name:
      logging.error("No test found matching: %s", filter_test_name)
    else:
      logging.error("No tests found.")
    return False

  logging.info("Available tests and variants:")
  logging.info("")
  for name, variants in tests_by_name.items():
    logging.info(name)
    for i, variant in enumerate(variants):
      prefix = "├── " if i < len(variants) - 1 else "└── "
      logging.info("  %s%s", prefix, variant)

  return True


def _print_usage_and_available_tests() -> None:
  logging.error("Usage:")
  logging.error("  --tests <test_regex> : Specify which tests to run.")
  logging.error("  --variants <variant_regex> : Specify which variants to run.")
  logging.error("")
  _print_tests_tree()
  sys.exit(1)


def _print_scheduled_tests(tests: list[TestInvocation]) -> None:
  if not tests:
    return

  logging.info("=" * 80)
  logging.info("Scheduled Test Invocations:")
  logging.info("=" * 80)
  for test_invocation in tests:
    name = test_invocation.test.name
    variant = test_invocation.test.variant or "<default>"
    if test_invocation.min_successes:
      logging.info(" - %s (variant: %s) -> %s successful runs", name, variant,
                   test_invocation.min_successes)
    else:
      logging.info(" - %s (variant: %s)", name, variant)
  logging.info("=" * 80)


def generate_run_config(argv: list[str]) -> RunConfig:

  cli_config = CliConfig.from_cmdline(argv)

  if not cli_config.tests:
    _print_usage_and_available_tests()

  if cli_config.wait_for_debugger:
    debug_port = 5678
    debugpy.listen(("localhost", debug_port))
    logging.info("Waiting for python debugger on port %d...", debug_port)
    debugpy.wait_for_client()

  results_prefix = (f"{cli_config.results_prefix}_"
                    if cli_config.results_prefix else "")

  out_dir = cli_config.out_dir if cli_config.out_dir else RESULTS
  results_root: Path = out_dir / dt.now().strftime(
      f"{results_prefix}%Y-%m-%d_%H%M%S")
  results_root.mkdir(parents=True, exist_ok=True)

  latest_results = out_dir / "latest"
  if not cli_config.no_symlinks:
    latest_results.unlink(missing_ok=True)
    latest_results.symlink_to(results_root, target_is_directory=True)

  groups = []
  for test_str, variant_str in cli_config.tests:
    if Path(test_str).is_file():
      groups.extend(TestGroupConfig.parse(test_str).groups)
    else:
      groups.extend(
          TestGroupConfig.from_cmdline_flags(
              tests=test_str,
              variants=variant_str,
              playback=cli_config.playback,
              setup_delay=cli_config.setup_delay,
              startup_delay=cli_config.startup_delay).groups)
  test_group_config = TestGroupConfig(groups=groups)

  tests: list[TestInvocation] = generate_test_invocations(
      test_group_config.groups, enumerate_all_tests())

  return RunConfig(
      platform=cli_config.platform,
      device=cli_config.device,
      adb_bin=cli_config.adb_bin,
      browser=cli_config.browser,
      secrets=cli_config.secrets,
      results_root=results_root,
      debug=cli_config.debug,
      dry_run=cli_config.dry_run,
      no_symlinks=cli_config.no_symlinks,
      run_tast_analyzer=cli_config.run_tast_analyzer,
      tests=tests)


def check_submodules_status():
  try:
    # Fetch the status of all submodules (including nested ones)
    result = subprocess.run(["git", "submodule", "status"],
                            capture_output=True,
                            text=True,
                            check=True)

    for line in result.stdout.splitlines():
      if not line:
        continue

      # In 'git submodule status', a leading space means everything is
      # perfectly synced.
      # A '+', '-', or 'U' prefix indicates a mismatch or issue.
      status_prefix = line[0]

      if status_prefix != " ":
        # Parse the path.
        # Standard output format: <prefix><sha> <path> (<describe>)
        parts = line[1:].strip().split()
        submodule_path = parts[1] if len(parts) > 1 else "unknown_path"

        logging.warning(
            "Git submodule '%s' does not match the committed version."
            "Did you forget to run 'gclient sync'?", submodule_path)

  except subprocess.CalledProcessError:
    logging.error(
        "Git command failed. Is this a git repository?"
    )
  except FileNotFoundError:
    logging.error("Git executable not found in PATH.")


def runner_cli(argv: list[str]) -> None:
  setup_logging()
  check_submodules_status()

  if argv and argv[0] == "list":
    filter_test_name = argv[1] if len(argv) > 1 else None
    if not _print_tests_tree(filter_test_name):
      sys.exit(1)
    sys.exit(0)

  run_config = generate_run_config(argv)

  _print_scheduled_tests(run_config.tests)

  failed_tests: list[TestInvocation] = []
  for test_invocation in run_config.tests:
    successes, _ = run_test(test_invocation, run_config)
    if not successes or (test_invocation.min_successes and
                         successes != test_invocation.min_successes):
      failed_tests.append(test_invocation)

  for failed_test in failed_tests:
    logging.error("Test failed: %s", failed_test.test.full_name)

  if run_config.run_tast_analyzer:
    # Call tast-analyzer via wrapper script to merge results
    results_root = run_config.results_root
    helper_script = WEB_TESTS_ROOT / "run_tast_analyzer.py"

    try:
      subprocess.run([
          sys.executable,
          str(helper_script), "--output-path",
          str(results_root / "tast_analyzer_results.json"),
          "--unspecified-direction", "DOWN",
          str(results_root)
      ],
                     check=True,
                     capture_output=True,
                     text=True)
    except subprocess.CalledProcessError as e:
      logging.error("Failed to run tast-analyzer wrapper: %s", e)
      logging.error("Stdout:\n%s", e.stdout)
      logging.error("Stderr:\n%s", e.stderr)

  if failed_tests:
    sys.exit(1)

  sys.exit(0)

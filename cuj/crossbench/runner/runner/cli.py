# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import contextlib
import json
import logging
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt
from pathlib import Path
from typing import Any, Callable, Type, TypeVar

import debugpy
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from runner.config import (Benchmark, CliConfig, Cuj, RunConfig, Test,
                           TestGroup, TestGroupConfig, TestInvocationConfig,
                           TestInvocationState)
from runner.logging import (DirectLogCapture, LogCapture, NullLogCapture,
                            setup_logging)
from runner.paths import BENCHMARKS, CUJS, RESULTS, WEB_TESTS_ROOT
from runner.runner import run_test


def is_probe_config(file: Path) -> bool:
  return file.name.endswith("probe-config.hjson")


def is_page_config(file: Path) -> bool:
  return file.name.endswith("page-config.hjson")


def is_cb_args(file: Path) -> bool:
  return file.name.endswith("cb-args")


def is_probe_config_or_cb_args(file: Path) -> bool:
  return is_probe_config(file) or is_cb_args(file)


def get_test_variant(config_file: Path) -> str:
  name_sections: list[str] = config_file.name.split(".")

  if len(name_sections) == 2 and name_sections[1] == "cb-args":
    return name_sections[0]

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
  tests.extend(
      enumerate_tests(BENCHMARKS, is_probe_config_or_cb_args, Benchmark))
  return tests


def generate_test_invocations(
    groups: list[TestGroup],
    all_tests: list[Test]) -> list[TestInvocationConfig]:
  test_invocations: list[TestInvocationConfig] = []

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
            TestInvocationConfig(test, group.min_successes,
                                 group.max_consecutive_failures, group.playback,
                                 group.setup_delay, group.startup_delay))

  return test_invocations


def _print_usage_and_available_tests() -> None:
  logging.error("Usage:")
  logging.error("  --tests <test_regex> : Specify which tests to run.")
  logging.error("  --variants <variant_regex> : Specify which variants to run.")
  logging.error("")
  logging.error("Run 'run.py list' to see all available tests and variants.")
  sys.exit(1)


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

  tests: list[TestInvocationConfig] = generate_test_invocations(
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

  is_list_command = False
  if argv and argv[0] == "list":
    is_list_command = True
    argv = argv[1:]
    if "--tests" not in argv:
      argv.extend(["--tests", ".*"])

  run_config = generate_run_config(argv)

  if is_list_command:
    _print_selected_tests(run_config)
    sys.exit(0)

  all_passed = _run_scheduled_tests(run_config)
  sys.exit(0 if all_passed else 1)


def _print_selected_tests(run_config: RunConfig) -> None:
  console = Console()
  table = Table(title="Selected Tests and Variants", box=None, show_edge=False)
  table.add_column("Test")
  table.add_column("Variant")

  for inv in run_config.tests:
    benchmark = inv.test.name
    variant = inv.test.variant or "<default>"
    table.add_row(benchmark, variant)

  console.print(table)


def _run_scheduled_tests(run_config: RunConfig) -> bool:
  all_passed, tests_state = run_tests(run_config.tests, run_config)

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

  _write_results_json(tests_state, run_config)

  logging.info("Web tests results: %s", run_config.results_root)

  return all_passed


def _write_results_json(tests_state: list[TestInvocationState],
                        run_config: RunConfig) -> None:
  results_summary = {
      "tests": [inv.to_json() for inv in tests_state],
      "passes": sum(inv.successes for inv in tests_state),
      "failures": sum(inv.total_failures for inv in tests_state),
  }

  results_json_path = run_config.results_root / "web_tests_results.json"
  with results_json_path.open("w", encoding="utf-8") as f:
    json.dump(results_summary, f, indent=2)


def _generate_table_layout(tests: list[TestInvocationState],
                           log_capture: LogCapture) -> Group:
  table = Table(title="Crossbench Test Queue", box=None, show_edge=False)
  table.add_column("State", width=6)
  table.add_column("Test")
  table.add_column("Variant")
  table.add_column("Passes", justify="right")
  table.add_column("Fails", justify="right")

  for inv in tests:
    status: Any
    is_success = inv.successes >= (inv.config.min_successes or 1)
    if inv.invocation_result.done():
      status = "[green]DONE[/green]" if is_success else "[red]FAIL[/red]"
    elif inv.invocation_result.running():
      status = inv.spinner
    else:
      status = "[dim]WAIT[/dim]"

    benchmark = inv.config.test.name
    variant = inv.config.test.variant or "<default>"

    min_succ = inv.config.min_successes or 1
    passes = f"{inv.successes}/{min_succ}"

    if inv.config.max_consecutive_failures:
      fails = f"{inv.failures}/{inv.config.max_consecutive_failures}"
    else:
      fails = f"{inv.failures}"

    if inv.total_failures > 0:
      fails += f" ({inv.total_failures} total)"

    table.add_row(status, benchmark, variant, passes, fails)

  log_panel = Panel(log_capture.get_text(), title="Crossbench Logs", height=17)
  return Group(table, log_panel)


def run_tests(tests_config: list[TestInvocationConfig],
              run_config: RunConfig) -> tuple[bool, list[TestInvocationState]]:
  tests = [TestInvocationState(config=inv) for inv in tests_config]
  all_passed = True
  use_live_ui = sys.stdout.isatty() and not run_config.debug

  log_capture: LogCapture | DirectLogCapture | NullLogCapture
  live_ctx: Any

  if use_live_ui:
    log_capture = LogCapture(max_lines=15)
    live_ctx = Live(
        _generate_table_layout(tests, log_capture), refresh_per_second=10)
  else:
    log_capture = NullLogCapture() if (
        run_config.dry_run and not run_config.debug) else DirectLogCapture()
    live_ctx = contextlib.nullcontext()

  with live_ctx as live:
    max_workers = None if run_config.dry_run else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
      for inv in tests:
        inv.invocation_result = executor.submit(
            run_test, inv, run_config, log_buffer=log_capture)

      while any(not inv.invocation_result.done() for inv in tests):
        time.sleep(0.1)
        if use_live_ui:
          assert isinstance(log_capture, LogCapture)
          live.update(_generate_table_layout(tests, log_capture))

        _write_results_json(tests, run_config)

      for inv in tests:
        if not inv.invocation_result.result():
          all_passed = False

  if not all_passed and run_config.dry_run:
    logging.error("")
    logging.error(
        "======================================================================"
    )
    logging.error("The following tests failed:")
    for inv in tests:
      if not inv.successes:
        test_name = inv.config.test.name
        variant = inv.config.test.variant
        variant_arg = f" {variant}" if variant else ""
        logging.error("  - %s%s", test_name, variant_arg)
    logging.error("")
    logging.error(
        "Run 'vpython3 run.py --platform local --dry-run "
        "--tests <test_name> <variant_args>' to debug."
    )
    logging.error(
        "======================================================================"
    )

  return all_passed, tests

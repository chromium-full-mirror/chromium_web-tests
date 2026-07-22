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
from typing import Any, NoReturn

import debugpy
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from runner.config import (CliConfig, RunConfig, Test, TestGroup,
                           TestGroupConfig, TestInvocationConfig,
                           TestInvocationState)
from runner.gather_metrics import generate_metrics_json
from runner.logging import (DirectLogCapture, LogCapture, NullLogCapture,
                            setup_logging)
from runner.paths import RESULTS
from runner.runner import run_test
from runner.test_discovery import enumerate_all_tests
from runner.upload import do_upload

LOG_MAX_VISIBLE_LINES = 15
LOG_PANEL_HEIGHT = LOG_MAX_VISIBLE_LINES + 2


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


def _print_usage_and_available_tests() -> NoReturn:
  logging.error("Usage:")
  logging.error("  --tests <test_regex> : Specify which tests to run.")
  logging.error("  --variants <variant_regex> : Specify which variants to run.")
  logging.error("")
  logging.error("Run 'run.py list' to see all available tests and variants.")
  sys.exit(1)


def generate_run_config(argv: list[str]) -> RunConfig:

  cli_config = CliConfig.from_cmdline(argv)

  if cli_config.wait_for_debugger:
    debug_port = 5678
    debugpy.listen(("localhost", debug_port))
    logging.info("Waiting for python debugger on port %d...", debug_port)
    debugpy.wait_for_client()

  tests: list[TestInvocationConfig] = []

  if (not cli_config.tests and not cli_config.list_tests and
      not cli_config.out_dir):
    _print_usage_and_available_tests()

  if not cli_config.tests and not cli_config.list_tests:
    assert cli_config.out_dir is not None
    results_root = cli_config.out_dir
  else:
    tag_prefix = f"{cli_config.tag}_" if cli_config.tag else ""
    results_prefix = (f"{cli_config.results_prefix}_"
                      if cli_config.results_prefix else "")

    out_dir = cli_config.out_dir if cli_config.out_dir else RESULTS
    results_root = out_dir / dt.now().strftime(
        f"{results_prefix}{tag_prefix}%Y-%m-%d_%H%M%S")

    if not cli_config.list_tests:
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

    tests = generate_test_invocations(test_group_config.groups,
                                      enumerate_all_tests())

  return RunConfig(
      platform=cli_config.platform,
      device=cli_config.device,
      adb_bin=cli_config.adb_bin,
      browser=cli_config.browser,
      secrets=cli_config.secrets,
      upload=cli_config.upload,
      results_root=results_root,
      tag=cli_config.tag,
      debug=cli_config.debug,
      dry_run=cli_config.dry_run,
      no_symlinks=cli_config.no_symlinks,
      list_tests=cli_config.list_tests,
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

  run_config = generate_run_config(argv)

  if run_config.list_tests:
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
  all_passed = True
  if run_config.tests:
    all_passed, tests_state = run_tests(run_config.tests, run_config)
    _write_results_json(tests_state, run_config)

  generate_metrics_json(run_config.results_root)

  logging.info("Web tests results: %s", run_config.results_root)

  if run_config.upload:
    do_upload(run_config.results_root, run_config.tag)

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
                           log_capture: LogCapture, console: Console) -> Group:
  table = Table(title="Crossbench Test Queue", box=None, show_edge=False)
  table.add_column("State", width=6)
  table.add_column("Test")
  table.add_column("Variant")
  table.add_column("Passes", justify="right")
  table.add_column("Fails", justify="right")

  table_header_height = len(console.render_lines(table, console.options)) + 1

  finished_tests = [t for t in tests if t.invocation_result.done()]
  running_tests = [t for t in tests if t.invocation_result.running()]
  waiting_tests = [
      t for t in tests
      if not t.invocation_result.done() and not t.invocation_result.running()
  ]

  term_height = console.size.height
  available_rows = term_height - LOG_PANEL_HEIGHT - table_header_height

  if finished_tests:
    table.add_row("", f"[dim]{len(finished_tests)} Finished[/dim]", "", "", "")
    available_rows -= 1

  total_pending = len(running_tests) + len(waiting_tests)
  if total_pending > available_rows:
    available_rows -= 1  # leave space for "... and X more" row

  available_rows = max(1, available_rows)

  visible_running = running_tests[:available_rows]
  visible_waiting = waiting_tests[:max(0, available_rows -
                                       len(visible_running))]
  hidden = total_pending - len(visible_running) - len(visible_waiting)

  for inv in visible_running + visible_waiting:
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

  if hidden > 0:
    table.add_row("", f"[dim]... and {hidden} more[/dim]", "", "", "")

  log_text = log_capture.get_text()
  log_lines = log_text.split("\n")

  sanitized_lines = []
  for line in log_lines[-LOG_MAX_VISIBLE_LINES:]:
    if "\r" in line:
      line = line.split("\r")[-1]
    # Strip emojis and non-ascii characters to avoid
    # rich/terminal wcwidth mismatches
    line = line.encode("ascii", "ignore").decode("ascii")
    sanitized_lines.append(line)

  visible_log = "\n".join(sanitized_lines)

  log_panel = Panel(
      Text.from_ansi(visible_log, no_wrap=True),
      title="Crossbench Logs",
      height=LOG_PANEL_HEIGHT)
  return Group(table, log_panel)


def run_tests(tests_config: list[TestInvocationConfig],
              run_config: RunConfig) -> tuple[bool, list[TestInvocationState]]:
  tests = [TestInvocationState(config=inv) for inv in tests_config]
  all_passed = True
  use_live_ui = sys.stdout.isatty() and not run_config.debug

  log_capture: LogCapture | DirectLogCapture | NullLogCapture
  live_ctx: Any

  if use_live_ui:
    console = Console()
    log_capture = LogCapture(max_lines=LOG_MAX_VISIBLE_LINES)
    live_ctx = Live(
        _generate_table_layout(tests, log_capture, console),
        console=console,
        refresh_per_second=10)
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
          live.update(_generate_table_layout(tests, log_capture, console))

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

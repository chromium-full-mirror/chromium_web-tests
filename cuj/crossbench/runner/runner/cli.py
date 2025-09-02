# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import logging
import re
import sys
from datetime import datetime as dt
from pathlib import Path

import debugpy
from runner.config import (Benchmark, BenchmarkGroup, BenchmarkInvocation,
                           CliConfig, Cuj, CujGroup, CujInvocation, RunConfig,
                           TestGroupConfig, TestInvocation, Tests)
from runner.paths import (BENCHMARKS, CUJS, LATEST_RESULTS, RESULTS,
                          WEB_TESTS_ROOT)
from runner.runner import run_test


def is_page_config(file: Path) -> bool:
  return file.name.endswith("page-config.hjson")


def get_test_variant(page_config: Path) -> str:
  name_sections: list[str] = page_config.name.split(".")

  if len(name_sections) <= 2:
    return ""

  return name_sections[0]


def enumerate_all_tests() -> Tests:
  tests: Tests = Tests(cujs=[], benchmarks=[])

  for benchmark_path in BENCHMARKS.iterdir():
    if not benchmark_path.is_dir():
      continue

    maybe_extensions: Path = benchmark_path / "extensions.hjson"
    maybe_probe_config: Path = benchmark_path / "probe-config.hjson"

    cb_args = ""
    cb_args_file = benchmark_path / "cb-args"
    if cb_args_file.is_file():
      cb_args = cb_args_file.read_text()

    benchmark = Benchmark(
        name=benchmark_path.name,
        path=benchmark_path,
        probe_config=(maybe_probe_config
                      if maybe_probe_config.is_file() else None),
        browser_flags=(benchmark_path / "browser-flags.hjson"),
        extensions=(maybe_extensions if maybe_extensions.is_file() else None),
        crossbench_args=cb_args)

    tests.benchmarks.append(benchmark)

  for cuj_path in CUJS.iterdir():

    if not cuj_path.is_dir():
      continue

    for page_config in cuj_path.iterdir():
      if not is_page_config(page_config):
        continue

      variant: str = get_test_variant(page_config)

      probe_config = cuj_path / f"{variant}.probe-config.hjson"

      if not probe_config.is_file():
        probe_config = cuj_path / "probe-config.hjson"

      browser_flags = cuj_path / f"{variant}.browser-flags.hjson"

      if not browser_flags.is_file():
        browser_flags = cuj_path / "browser-flags.hjson"

      extensions = cuj_path / f"{variant}.extensions.hjson"

      if not extensions.is_file():
        extensions = cuj_path / "extensions.hjson"

      cb_args_file = cuj_path / f"{variant}.cb-args"

      if not cb_args_file.is_file():
        cb_args_file = cuj_path / "cb-args"

      if not cb_args_file.is_file():
        cb_args = ""
      else:
        cb_args = cb_args_file.read_text()

      cb_args = cb_args.replace("$[WEB_TESTS]", str(WEB_TESTS_ROOT))

      tests.cujs.append(
          Cuj(name=cuj_path.name,
              variant=variant,
              path=cuj_path,
              page_config=page_config,
              probe_config=probe_config,
              browser_flags=browser_flags,
              extensions=(extensions if extensions.is_file() else None),
              crossbench_args=cb_args))

  return tests


def generate_benchmark_invocations(
    benchmark_groups: list[BenchmarkGroup],
    potential_benchmarks: list[Benchmark]) -> list[BenchmarkInvocation]:
  benchmark_invocations: list[BenchmarkInvocation] = []

  for potential_benchmark in potential_benchmarks:
    for benchmark_group in benchmark_groups:
      if re.fullmatch(benchmark_group.filter_regex, potential_benchmark.name):
        benchmark_invocations.append(
            BenchmarkInvocation.from_benchmark(
                potential_benchmark, benchmark_group.min_successes,
                benchmark_group.max_consecutive_failures))

  return benchmark_invocations


def generate_cuj_invocations(cuj_groups: list[CujGroup],
                             potential_cujs: list[Cuj]) -> list[CujInvocation]:
  cuj_invocations: list[CujInvocation] = []

  for potential_cuj in potential_cujs:
    for cuj_group in cuj_groups:
      if re.fullmatch(
          cuj_group.filter_regex, potential_cuj.name) and re.fullmatch(
              cuj_group.variants_filter_regex, potential_cuj.variant):
        cuj_invocations.append(
            CujInvocation.from_cuj(potential_cuj, cuj_group.min_successes,
                                   cuj_group.max_consecutive_failures,
                                   cuj_group.playback))

  return cuj_invocations


def generate_run_config(argv: list[str]) -> RunConfig:

  cli_config = CliConfig.from_cmdline(argv)

  if cli_config.wait_for_debugger:
    debug_port = 5678
    debugpy.listen(("localhost", debug_port))
    logging.info("Waiting for python debugger on port %d...", debug_port)
    debugpy.wait_for_client()

  results_prefix = (f"{cli_config.results_prefix}_"
                    if cli_config.results_prefix else "")
  results_root: Path = RESULTS / dt.now().strftime(
      f"{results_prefix}%Y-%m-%d_%H%M%S")
  results_root.mkdir(parents=True)

  LATEST_RESULTS.unlink(missing_ok=True)
  LATEST_RESULTS.symlink_to(results_root, target_is_directory=True)

  if Path(cli_config.tests).is_file():
    test_group_config = TestGroupConfig.parse(cli_config.tests)
  else:
    test_group_config = TestGroupConfig.from_cmdline_flags(
        tests=cli_config.tests,
        variants=cli_config.variants,
        playback=cli_config.playback)

  all_tests = enumerate_all_tests()

  tests: tuple[BenchmarkInvocation | CujInvocation, ...] = tuple(
      generate_benchmark_invocations(
          test_group_config.benchmark_groups, all_tests.benchmarks)) + tuple(
              generate_cuj_invocations(test_group_config.cuj_groups,
                                       all_tests.cujs))

  return RunConfig(
      platform=cli_config.platform,
      device=cli_config.device,
      browser=cli_config.browser,
      secrets=cli_config.secrets,
      results_root=results_root,
      debug=cli_config.debug,
      dry_run=cli_config.dry_run,
      tests=tests)


def runner_cli(argv: list[str]) -> None:
  logging.getLogger().setLevel(logging.INFO)

  run_config = generate_run_config(argv)

  failed_tests: list[TestInvocation] = []
  for test_invocation in run_config.tests:
    successes, _ = run_test(test_invocation, run_config)
    if not successes or (test_invocation.min_successes and
                         successes != test_invocation.min_successes):
      failed_tests.append(test_invocation)

  for failed_test in failed_tests:
    logging.error("Test failed: %s", failed_test.full_name)

  if failed_tests:
    sys.exit(1)

  sys.exit(0)

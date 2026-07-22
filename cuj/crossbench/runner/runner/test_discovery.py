# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

from pathlib import Path
from typing import Callable, Type, TypeVar

from runner.config import Benchmark, Cuj, Test
from runner.paths import BENCHMARKS, CUJS, WEB_TESTS_ROOT


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

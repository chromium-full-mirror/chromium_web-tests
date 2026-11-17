#!/usr/bin/env vpython3
# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Unit tests for tools/check_cuj_readmes.py."""

from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import check_cuj_readmes


def _build_readme(
    title: str = "# `sample` CUJ",
    overview: str = "Benchmarks sample user interactions.",
    variants_table: str = (
        "| Variant | Config File | Key Differences |\n"
        "| :--- | :--- | :--- |\n"
        "| `default` | `page-config.hjson` | "
        "Base run (`./action-blocks/main.hjson`). |\n"
        "| `fast` | `fast.page-config.hjson` | Fast run. |"),
    workflow: str = "- **Main Actions**: Executes main block.",
    invariants: str = "- Preserve native touch input.",
    invariants_heading: str = "## Metrics & Invariants (Preserve When Healing)",
) -> str:
  parts: list[str] = []
  if title:
    parts.append(title)
  if overview is not None:
    parts.append(f"## Overview\n{overview}")
  if variants_table is not None:
    parts.append(f"## Variants\n{variants_table}")
  if workflow is not None:
    parts.append(f"## Workflow\n{workflow}")
  if invariants_heading:
    parts.append(f"{invariants_heading}\n{invariants}")
  return "\n\n".join(parts) + "\n"


class CheckCujReadmesTest(unittest.TestCase):
  """Tests CUJ README validation rules in check_cuj_readmes."""

  def setUp(self) -> None:
    super().setUp()
    tmp_dir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, tmp_dir)
    self.repo_root = Path(tmp_dir)
    self.cujs_dir = self.repo_root / "cuj" / "crossbench" / "cujs"
    self.cujs_dir.mkdir(parents=True)

  def _create_sample_cuj(self, name: str = "sample") -> Path:
    cuj_dir = self.cujs_dir / name
    (cuj_dir / "action-blocks").mkdir(parents=True)
    (cuj_dir / "action-blocks" / "main.hjson").write_text(
        "{}", encoding="utf-8")
    (cuj_dir / "page-config.hjson").write_text("{}", encoding="utf-8")
    (cuj_dir / "fast.page-config.hjson").write_text("{}", encoding="utf-8")
    (cuj_dir / "README.md").write_text(_build_readme(), encoding="utf-8")
    return cuj_dir

  def test_valid_multi_variant_cuj_passes(self) -> None:
    self._create_sample_cuj()
    self.assertEqual(
        check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root), [])

  def test_reordered_columns_and_page_config_file_header_pass(self) -> None:
    cuj_dir = self._create_sample_cuj()
    table = ("| Notes | Page Config File | Variant |\n"
             "| :--- | :--- | :--- |\n"
             "| Base | `page-config.hjson` | `default` |\n"
             "| Fast | `fast.page-config.hjson` | `fast` |")
    (cuj_dir / "README.md").write_text(
        _build_readme(variants_table=table), encoding="utf-8")
    self.assertEqual(
        check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root), [])

  def test_cuj_without_static_page_configs(self) -> None:
    cuj_dir = self.cujs_dir / "dynamic-cuj"
    cuj_dir.mkdir(parents=True)
    dynamic_table = (
        "| Variant | Config File | Key Differences |\n"
        "| :--- | :--- | :--- |\n"
        "| `default` | None on disk (`--page-config`) | Runtime config. |")
    (cuj_dir / "README.md").write_text(
        _build_readme(variants_table=dynamic_table), encoding="utf-8")
    self.assertEqual(
        check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root), [])

    bad_table = ("| Variant | Config File | Key Differences |\n"
                 "| :--- | :--- | :--- |\n"
                 "| `default` | `page-config.hjson` | Missing on disk. |")
    (cuj_dir / "README.md").write_text(
        _build_readme(variants_table=bad_table), encoding="utf-8")
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertEqual(len(errors), 1)
    self.assertIn("has no *page-config.hjson on disk", errors[0])

  def test_missing_or_empty_readme_fails(self) -> None:
    cuj_dir = self.cujs_dir / "missing-readme"
    cuj_dir.mkdir(parents=True)
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertEqual(len(errors), 1)
    self.assertIn("Missing required CUJ README.md file", errors[0])

    (cuj_dir / "README.md").write_text("   \n\t\n", encoding="utf-8")
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertEqual(len(errors), 1)
    self.assertIn("README.md is empty", errors[0])

  def test_missing_title_or_required_sections_fails(self) -> None:
    cuj_dir = self._create_sample_cuj()

    # Missing top-level '# ' title and empty Workflow body.
    (cuj_dir / "README.md").write_text(
        _build_readme(title="", workflow=""), encoding="utf-8")
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertTrue(any("Missing top-level" in e for e in errors))
    self.assertTrue(any("Section '## Workflow' is empty" in e for e in errors))

    # Missing Metrics & Invariants heading entirely.
    (cuj_dir / "README.md").write_text(
        _build_readme(invariants_heading=""), encoding="utf-8")
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertTrue(
        any("Missing required '## Metrics & Invariants'" in e for e in errors))

  def test_added_variant_missing_from_readme_fails(self) -> None:
    cuj_dir = self._create_sample_cuj()
    (cuj_dir / "4k-60fps.page-config.hjson").write_text("{}", encoding="utf-8")

    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertEqual(len(errors), 1)
    self.assertIn("4k-60fps", errors[0])
    self.assertIn("4k-60fps.page-config.hjson", errors[0])
    self.assertIn("missing or mismatched", errors[0])

  def test_removed_variant_stale_in_readme_fails(self) -> None:
    cuj_dir = self._create_sample_cuj()
    (cuj_dir / "fast.page-config.hjson").unlink()

    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertEqual(len(errors), 1)
    self.assertIn("fast.page-config.hjson", errors[0])
    self.assertIn("does not match any variant on disk", errors[0])

  def test_mismatched_variant_name_or_missing_config_span_fails(self) -> None:
    cuj_dir = self._create_sample_cuj()
    table = ("| Variant | Config File | Key Differences |\n"
             "| :--- | :--- | :--- |\n"
             "| `default` | None listed | Base |\n"
             "| `wrong-name` | `fast.page-config.hjson` | Fast |")
    (cuj_dir / "README.md").write_text(
        _build_readme(variants_table=table), encoding="utf-8")

    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertTrue(
        any("missing a backticked '*page-config.hjson'" in e for e in errors))
    self.assertTrue(
        any("'wrong-name' ('fast.page-config.hjson')" in e for e in errors))
    self.assertTrue(
        any("'fast' ('fast.page-config.hjson')" in e for e in errors))

  def test_malformed_duplicate_and_empty_cell_tables_fail(self) -> None:
    cuj_dir = self._create_sample_cuj()

    # Missing required columns.
    bad_cols = ("| Name | File |\n"
                "| :--- | :--- |\n"
                "| `default` | `page-config.hjson` |")
    (cuj_dir / "README.md").write_text(
        _build_readme(variants_table=bad_cols), encoding="utf-8")
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertTrue(
        any("must include 'Variant' and 'Config File' columns" in e
            for e in errors))

    # Duplicate variant/config, empty cell, wrong cell count, multi-config cell.
    dup_table = (
        "| Variant | Config File | Key Differences |\n"
        "| :--- | :--- | :--- |\n"
        "| `default` | `page-config.hjson` | |\n"
        "| `default` | `page-config.hjson` | Duplicate row. |\n"
        "| `fast` | `fast.page-config.hjson` `b.page-config.hjson` | Two |\n"
        "| `extra` | `only-two-cells.page-config.hjson` |")
    (cuj_dir / "README.md").write_text(
        _build_readme(variants_table=dup_table), encoding="utf-8")
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertTrue(any("has an empty cell" in e for e in errors))
    self.assertTrue(any("Duplicate variant 'default'" in e for e in errors))
    self.assertTrue(
        any("Duplicate config file 'page-config.hjson'" in e for e in errors))
    self.assertTrue(
        any("Multiple page-config filenames" in e for e in errors))
    self.assertTrue(any("has 2 cells; expected 3" in e for e in errors))

  def test_local_path_validation(self) -> None:
    cuj_dir = self._create_sample_cuj()
    shared_block = (
        self.repo_root / "cuj" / "crossbench" / "common-action-blocks" /
        "basic" / "scroll.hjson")
    shared_block.parent.mkdir(parents=True)
    shared_block.write_text("{}", encoding="utf-8")

    # Existing paths, URLs, and elided ".../" snippets pass.
    workflow = (
        "- Uses `./action-blocks/main.hjson` and `basic/scroll.hjson`.\n"
        "- Ignores `https://example.com/test.html` and `.../clip/test.html`.")
    (cuj_dir / "README.md").write_text(
        _build_readme(workflow=workflow), encoding="utf-8")
    self.assertEqual(
        check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root), [])

    # Deleted action-block file fails.
    (cuj_dir / "action-blocks" / "main.hjson").unlink()
    errors = check_cuj_readmes.check_all_cujs(self.cujs_dir, self.repo_root)
    self.assertEqual(len(errors), 1)
    self.assertIn("Referenced path './action-blocks/main.hjson'", errors[0])

  def test_main_cli_exit_codes(self) -> None:
    cuj_dir = self._create_sample_cuj()
    stderr_ok = io.StringIO()
    with contextlib.redirect_stderr(stderr_ok):
      rc_ok = check_cuj_readmes.main([
          f"--cujs-dir={self.cujs_dir}",
          f"--repo-root={self.repo_root}",
      ])
    self.assertEqual(rc_ok, 0)
    self.assertEqual(stderr_ok.getvalue(), "")

    (cuj_dir / "unlisted.page-config.hjson").write_text("{}", encoding="utf-8")
    stderr_err = io.StringIO()
    with contextlib.redirect_stderr(stderr_err):
      rc_err = check_cuj_readmes.main([
          f"--cujs-dir={self.cujs_dir}",
          f"--repo-root={self.repo_root}",
      ])
    self.assertEqual(rc_err, 1)
    self.assertIn("unlisted.page-config.hjson", stderr_err.getvalue())


if __name__ == "__main__":
  unittest.main()

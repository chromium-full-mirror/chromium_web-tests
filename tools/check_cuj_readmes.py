#!/usr/bin/env vpython3
# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Validates that every CUJ directory has an up-to-date README.md.

Checks for each subdirectory under cuj/crossbench/cujs/:
1. A non-empty README.md exists with required sections (Overview, Variants,
   Workflow, and Metrics & Invariants).
2. The Markdown table under '## Variants' has an exact 1-to-1 match with the
   *page-config.hjson variant files present on disk (or documents a single
   dynamic 'default' entry when no static page-config.hjson exists, e.g. alice).
3. Relative repository file paths referenced in backticks inside README.md
   resolve to existing files on disk.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WEB_TESTS_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CUJS_DIR = WEB_TESTS_ROOT / "cuj" / "crossbench" / "cujs"

REQUIRED_SECTION_PREFIXES: tuple[str, ...] = (
    "Overview",
    "Variants",
    "Workflow",
    "Metrics & Invariants",
)

CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
PAGE_CONFIG_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]*page-config\.hjson$")
SLASH_PATH_RE = re.compile(
    r"^(?:\.\.?/|[A-Za-z0-9_-]+/)[A-Za-z0-9_./-]+"
    r"(?:\.(?:hjson|js|sql|textproto|pbtxt|py|md|html)|cb-args)$")


def discover_disk_variants(cuj_dir: Path) -> list[tuple[str, str]]:
  """Returns sorted (variant_name, filename) pairs for a CUJ directory."""
  variants: list[tuple[str, str]] = []
  for entry in sorted(cuj_dir.iterdir(), key=lambda p: p.name):
    if not entry.is_file() or not entry.name.endswith("page-config.hjson"):
      continue
    name_sections = entry.name.split(".")
    variant_name = "default" if len(name_sections) <= 2 else name_sections[0]
    variants.append((variant_name, entry.name))
  return sorted(variants)


def extract_h2_sections(markdown_text: str) -> dict[str, str]:
  """Maps each '## <Heading>' line (without '## ') to its body text."""
  sections: dict[str, str] = {}
  matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown_text, re.MULTILINE))
  for idx, match in enumerate(matches):
    heading = match.group(1).strip()
    body_start = match.end()
    body_end = (
        matches[idx + 1].start() if idx + 1 < len(matches) else len(
            markdown_text))
    sections[heading] = markdown_text[body_start:body_end].strip()
  return sections


def split_markdown_row(row_line: str) -> list[str]:
  """Splits a pipe-delimited Markdown table row into stripped cell strings."""
  stripped = row_line.strip()
  if stripped.startswith("|"):
    stripped = stripped[1:]
  if stripped.endswith("|"):
    stripped = stripped[:-1]
  return [cell.strip() for cell in stripped.split("|")]


def is_separator_row(cells: list[str]) -> bool:
  return bool(cells) and all(
      bool(re.fullmatch(r":?-{2,}:?", cell)) for cell in cells)


def parse_variants_table(
    readme_rel: Path,
    variants_body: str,
) -> tuple[list[tuple[str, str | None]], list[str]]:
  """Parses (variant_name, config_filename) pairs from the Variants table."""
  errors: list[str] = []
  table_lines = [
      line.strip()
      for line in variants_body.splitlines()
      if line.strip().startswith("|")
  ]
  if len(table_lines) < 3:
    errors.append(
        f"{readme_rel}: '## Variants' must contain a Markdown table with a "
        "header row, separator row, and at least one variant row.")
    return [], errors

  headers = [h.lower() for h in split_markdown_row(table_lines[0])]
  separator = split_markdown_row(table_lines[1])
  if len(separator) != len(headers) or not is_separator_row(separator):
    errors.append(
        f"{readme_rel}: Malformed Markdown table separator under "
        "'## Variants'.")
    return [], errors

  variant_col = next(
      (i for i, h in enumerate(headers) if h == "variant"),
      None,
  )
  config_col = next(
      (i for i, h in enumerate(headers)
       if h in ("config file", "page config file")),
      None,
  )
  if variant_col is None or config_col is None:
    errors.append(
        f"{readme_rel}: '## Variants' table must include 'Variant' and "
        "'Config File' columns.")
    return [], errors

  parsed_rows: list[tuple[str, str | None]] = []
  seen_variants: set[str] = set()
  seen_configs: set[str] = set()

  for row_num, raw_line in enumerate(table_lines[2:], start=1):
    cells = split_markdown_row(raw_line)
    if len(cells) != len(headers):
      errors.append(
          f"{readme_rel}: Row {row_num} in '## Variants' table has "
          f"{len(cells)} cells; expected {len(headers)}.")
      continue
    if any(not cell for cell in cells):
      errors.append(
          f"{readme_rel}: Row {row_num} in '## Variants' table has an empty "
          "cell.")

    variant_spans = CODE_SPAN_RE.findall(cells[variant_col])
    variant_name = (
        variant_spans[0].strip() if variant_spans else cells[variant_col])
    if variant_name in seen_variants:
      errors.append(
          f"{readme_rel}: Duplicate variant '{variant_name}' in "
          "'## Variants' table.")
    seen_variants.add(variant_name)

    config_spans = [
        span.strip()
        for span in CODE_SPAN_RE.findall(cells[config_col])
        if PAGE_CONFIG_NAME_RE.fullmatch(span.strip())
    ]
    if len(config_spans) > 1:
      errors.append(
          f"{readme_rel}: Multiple page-config filenames in single row for "
          f"variant '{variant_name}': {config_spans}.")
    config_name = config_spans[0] if config_spans else None
    if config_name is not None:
      if config_name in seen_configs:
        errors.append(
            f"{readme_rel}: Duplicate config file '{config_name}' in "
            "'## Variants' table.")
      seen_configs.add(config_name)

    parsed_rows.append((variant_name, config_name))

  return parsed_rows, errors


def check_local_paths(
    cuj_dir: Path,
    repo_root: Path,
    readme_rel: Path,
    markdown_text: str,
) -> list[str]:
  """Verifies that slash-containing relative repo paths in backticks exist."""
  errors: list[str] = []
  cuj_crossbench = cuj_dir.parent.parent
  search_roots = (
      cuj_dir,
      cuj_dir / "action-blocks",
      cuj_crossbench,
      cuj_dir.parent,
      cuj_crossbench / "common-action-blocks",
      cuj_crossbench / "runner",
      repo_root,
  )

  checked: set[str] = set()
  for token in CODE_SPAN_RE.findall(markdown_text):
    candidate = token.strip()
    if candidate in checked:
      continue
    checked.add(candidate)

    if (not SLASH_PATH_RE.fullmatch(candidate) or
        candidate.startswith(".../") or "://" in candidate):
      continue

    if not any((root / candidate).is_file() for root in search_roots):
      errors.append(
          f"{readme_rel}: Referenced path '{candidate}' does not exist on "
          "disk.")

  return errors


def check_cuj_directory(cuj_dir: Path, repo_root: Path) -> list[str]:
  """Runs all README sync checks for a single CUJ directory."""
  errors: list[str] = []
  readme_path = cuj_dir / "README.md"
  try:
    readme_rel = readme_path.relative_to(repo_root)
  except ValueError:
    readme_rel = readme_path

  if not readme_path.is_file():
    return [f"{readme_rel}: Missing required CUJ README.md file."]

  text = readme_path.read_text(encoding="utf-8")
  if not text.strip():
    return [f"{readme_rel}: README.md is empty."]

  if not re.search(r"^#\s+\S+", text, re.MULTILINE):
    errors.append(f"{readme_rel}: Missing top-level '# <cuj>' title heading.")

  sections = extract_h2_sections(text)
  matched_bodies: dict[str, str] = {}
  for prefix in REQUIRED_SECTION_PREFIXES:
    matching_heading = next(
        (h for h in sections if h == prefix or h.startswith(f"{prefix} ")),
        None,
    )
    if matching_heading is None:
      errors.append(f"{readme_rel}: Missing required '## {prefix}' section.")
    elif not sections[matching_heading]:
      errors.append(f"{readme_rel}: Section '## {matching_heading}' is empty.")
    else:
      matched_bodies[prefix] = sections[matching_heading]

  if "Variants" in matched_bodies:
    doc_rows, table_errors = parse_variants_table(readme_rel,
                                                  matched_bodies["Variants"])
    errors.extend(table_errors)
    if not table_errors:
      disk_variants = discover_disk_variants(cuj_dir)
      if disk_variants:
        for variant_name, config_name in doc_rows:
          if config_name is None:
            errors.append(
                f"{readme_rel}: Variant '{variant_name}' in '## Variants' "
                "table is missing a backticked '*page-config.hjson' filename.")
        doc_pairs = {
            (variant_name, config_name)
            for variant_name, config_name in doc_rows
            if config_name is not None
        }
        disk_pairs = set(disk_variants)

        for variant_name, config_name in sorted(disk_pairs - doc_pairs):
          errors.append(
              f"{readme_rel}: Variant '{variant_name}' ('{config_name}') "
              "exists on disk in "
              f"'{cuj_dir.name}/' but is missing or mismatched in "
              "'## Variants' table.")
        for variant_name, config_name in sorted(doc_pairs - disk_pairs):
          errors.append(
              f"{readme_rel}: '## Variants' table lists '{variant_name}' "
              f"('{config_name}'), which does not match any variant on disk in "
              f"'{cuj_dir.name}/'.")
      elif doc_rows != [("default", None)]:
        errors.append(
            f"{readme_rel}: CUJ '{cuj_dir.name}' has no *page-config.hjson "
            "on disk and must document a single 'default' row without a "
            f"config filename until static variants are added (found: "
            f"{doc_rows}).")

  errors.extend(check_local_paths(cuj_dir, repo_root, readme_rel, text))
  return errors


def check_all_cujs(cujs_dir: Path, repo_root: Path) -> list[str]:
  """Checks README.md files across all CUJ directories under cujs_dir."""
  if not cujs_dir.is_dir():
    return [f"CUJs directory does not exist: {cujs_dir}"]

  errors: list[str] = []
  cuj_dirs = sorted(
      (entry for entry in cujs_dir.iterdir() if entry.is_dir()),
      key=lambda p: p.name,
  )
  for cuj_dir in cuj_dirs:
    errors.extend(check_cuj_directory(cuj_dir, repo_root))
  return errors


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--cujs-dir",
      type=Path,
      default=DEFAULT_CUJS_DIR,
      help="Path to the cuj/crossbench/cujs directory.",
  )
  parser.add_argument(
      "--repo-root",
      type=Path,
      default=WEB_TESTS_ROOT,
      help="Path to the web-tests repository root.",
  )
  args = parser.parse_args(argv)

  errors = check_all_cujs(args.cujs_dir.resolve(), args.repo_root.resolve())
  if errors:
    for err in errors:
      print(err, file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  sys.exit(main())

-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS browser_info;

CREATE PERFETTO TABLE browser_info AS
WITH
  metadata_args AS (
    SELECT
      arg_set_id
    FROM __intrinsic_chrome_raw
    WHERE
      name = "chrome_event.metadata"
  )
SELECT
  1 AS dummy_value,
  max(CASE WHEN key = 'os-name' THEN display_value END) AS cr_os_name,
  max(CASE WHEN key = 'os-version' THEN display_value END) AS cr_os_version,
  max(CASE WHEN key = 'product-version' THEN display_value END) AS cr_version,
  max(CASE WHEN key = 'revision' THEN display_value END) AS cr_revision
FROM metadata_args
JOIN args
  ON metadata_args.arg_set_id = args.arg_set_id;

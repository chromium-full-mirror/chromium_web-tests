-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE sql_packages.web_tests_common.iterations;

DROP TABLE IF EXISTS dom_complete_output;

CREATE PERFETTO TABLE dom_complete_output AS
SELECT
  iterations.id AS it_id,
  ROW_NUMBER() OVER (ORDER BY ts) AS id,
  CAST(json_extract(EXTRACT_ARG(arg_set_id, 'debug.data.detail'), '$.domComplete') AS FLOAT) dom_complete,
  CAST(json_extract(EXTRACT_ARG(arg_set_id, 'debug.data.detail'), '$.domInteractive') AS FLOAT) dom_interactive
FROM slice JOIN iterations
  ON slice.ts >= iterations.start AND slice.ts <= iterations.end
WHERE
  category = 'blink.user_timing'
  AND name = 'page-loaded';
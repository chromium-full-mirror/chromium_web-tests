-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE sql_packages.web_tests_common.iterations;

DROP VIEW IF EXISTS lmk_kill_events;

CREATE VIEW lmk_kill_events AS
SELECT
  ts,
  extract_arg(arg_set_id, 'lmk_kill_occurred.process_name') AS process_name
FROM slice
WHERE
  name = 'lmk_kill_occurred';

DROP TABLE IF EXISTS lmk_kill_count_output;

CREATE PERFETTO TABLE lmk_kill_count_output AS
SELECT
  iterations.id AS it_id,
  count(lmk_kill_events.ts) AS kill_count,
  sum(CASE WHEN lmk_kill_events.process_name LIKE '%chrome%' THEN 1 ELSE 0 END) AS chrome_kill_count
FROM iterations
LEFT JOIN lmk_kill_events
  ON lmk_kill_events.ts >= iterations.start
  AND lmk_kill_events.ts <= iterations.end
GROUP BY
  iterations.id;

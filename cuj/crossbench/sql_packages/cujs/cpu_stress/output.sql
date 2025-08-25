-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP VIEW IF EXISTS all_started;
CREATE VIEW all_started AS
SELECT  -- The last of the first compress events
  MAX(ts) AS ts,
  COUNT(*) AS workers
FROM (
  SELECT  -- The first compress event on every track
    track_id,
    MIN(ts) AS ts
  FROM slice
  WHERE
    category = 'blink.user_timing'
    AND name = 'compress'
  GROUP BY track_id
);

DROP TABLE IF EXISTS cpu_stress_output;
CREATE PERFETTO TABLE cpu_stress_output AS
SELECT
  SUM(CASE WHEN ever_hidden = 0 THEN SIZE END)  / 1048576.0 AS foreground_size,
  AVG(CASE WHEN ever_hidden = 0 THEN SIZE / duration END) / 1048576.0 AS foreground_throughput,
  SUM(CASE WHEN ever_hidden = 1 THEN SIZE END)  / 1048576.0 AS background_size,
  AVG(CASE WHEN ever_hidden = 1 THEN SIZE / duration END) / 1048576.0 AS background_throughput,
  MIN(workers) AS workers
FROM (
  SELECT
    json_extract(detail, '$.everHidden') AS ever_hidden,
    json_extract(detail, '$.size') AS [size],
    json_extract(detail, '$.time') AS duration,
    workers
  FROM (
    SELECT
      extract_arg (arg_set_id, 'debug.data.detail') AS detail,
      all_started.workers AS workers
    FROM slice JOIN all_started
    WHERE
      slice.ts > all_started.ts
      AND category = 'blink.user_timing'
      AND name = 'compress'
  )
);
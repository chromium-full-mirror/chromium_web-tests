-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.

DROP TABLE IF EXISTS meminfo_output;

CREATE PERFETTO TABLE meminfo_output
AS
WITH meminfo_events AS (
  -- crossbench-meminfo event's detail field is a JSON blob of type:
  --  {
  --    pid: number
  --    pss_total: number
  --    rss_total: number
  --    swap_total: number
  --  }[]
  SELECT
    ts,
    EXTRACT_ARG(arg_set_id, 'debug.data.detail') AS json
  FROM slice
  WHERE
    category = 'blink.user_timing'
    AND name = 'crossbench-meminfo'
)
SELECT
  -- We have a row per process per meminfo event, sum up the meminfo counters
  -- for each meminfo event.
  meminfo_events.ts AS ts,
  SUM(CAST(json_extract(per_process_meminfo_json.value, '$.pss_total') AS FLOAT) / 1024.0) AS pss_total_mb,
  SUM(CAST(json_extract(per_process_meminfo_json.value, '$.rss_total') AS FLOAT) / 1024.0) AS rss_total_mb,
  SUM(CAST(json_extract(per_process_meminfo_json.value, '$.swap_total') AS FLOAT) / 1024.0) AS swap_total_mb
FROM
  meminfo_events,
  -- Extract the per-process objects and join them to their meminfo rows, to get
  -- a row per process per meminfo event.
  json_each(meminfo_events.json) AS per_process_meminfo_json
GROUP BY
  meminfo_events.ts
ORDER by
  meminfo_events.ts;

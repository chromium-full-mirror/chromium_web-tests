-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS video_seek_output;

CREATE PERFETTO TABLE video_seek_output AS
WITH
  AverageSeekTime AS (
    SELECT
      (SUM(dur) / COUNT(name)) / 1000000000.0 AS avg_seek_time_s -- Convert nanoseconds to seconds
    FROM
      slice
    WHERE
      name GLOB 'randomSeek-*-duration'
  ),

  TargetSeeks AS (
    SELECT
      CAST(json_extract(extract_arg(arg_set_id, 'debug.data.detail'), '$.numTargetSeeks') AS REAL) AS num_target_seeks
    FROM
      slice AS s
    WHERE
      s.name = 'test-config'
    LIMIT 1 -- Assuming only one 'test-config' mark with this detail
  ),

  CompletedSeeks AS (
    SELECT
      COUNT(name) AS completed_count
    FROM
      slice
    WHERE
      name GLOB 'randomSeek-*-duration'
  )

SELECT
  ast.avg_seek_time_s,
  (cs.completed_count * 100.0 / ts.num_target_seeks) AS seek_completion_percentage
FROM
  AverageSeekTime AS ast,
  TargetSeeks AS ts,
  CompletedSeeks AS cs;
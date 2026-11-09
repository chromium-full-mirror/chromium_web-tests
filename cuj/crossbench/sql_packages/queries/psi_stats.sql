-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS psi_stats_output;

CREATE PERFETTO TABLE psi_stats_output AS
WITH
  psi_samples AS (
    SELECT
      t.name AS resource,
      c.ts AS ts,
      c.value AS value,
      lag(c.ts) OVER (PARTITION BY c.track_id ORDER BY c.ts) AS prev_ts,
      lag(c.value) OVER (PARTITION BY c.track_id ORDER BY c.ts) AS prev_value
    FROM counter AS c
    JOIN counter_track AS t ON c.track_id = t.id
    WHERE
      t.type = 'psi'
  ),
  psi_windows AS (
    SELECT
      resource,
      ts,
      value,
      CASE
        WHEN prev_ts IS NOT NULL
        AND ts > prev_ts THEN max(
          0.0,
          min(
            100.0,
            (CAST((value - prev_value) AS DOUBLE) * 100.0) / (ts - prev_ts)
          )
        )
        ELSE NULL
      END AS window_stall_pct
    FROM psi_samples
  )
SELECT
  resource,
  (max(value) - min(value)) / 1000000.0 AS total_stall_ms,
  CASE
    WHEN max(ts) > min(ts) THEN max(
      0.0,
      min(
        100.0,
        (CAST((max(value) - min(value)) AS DOUBLE) * 100.0)
        / (max(ts) - min(ts))
      )
    )
    ELSE 0.0
  END AS avg_stall_pct,
  COALESCE(max(window_stall_pct), 0.0) AS max_window_stall_pct,
  COALESCE(percentile(window_stall_pct, 90), 0.0) AS p90_window_stall_pct
FROM psi_windows
GROUP BY
  resource;

-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS d_state_stalls_output;

CREATE PERFETTO TABLE d_state_stalls_output AS
WITH
  groups(process_group) AS (
    VALUES
      ('all'),
      ('chrome'),
      ('surfaceflinger'),
      ('hwc'),
      ('xe'),
      ('jbd2'),
      ('kswapd'),
      ('kworker')
  ),
  d_events AS (
    SELECT
      ts.dur AS dur,
      CASE
        WHEN p.name LIKE '%chrome%'
        OR t.name LIKE 'CrBrowser%'
        OR t.name LIKE 'CrRenderer%'
        OR t.name LIKE 'VizCompositor%' THEN 'chrome'
        WHEN p.name LIKE '%surfaceflinger%'
        OR t.name = 'surfaceflinger' THEN 'surfaceflinger'
        WHEN p.name LIKE '%hardware.composer%'
        OR p.name LIKE '%graphics.composer%'
        OR p.name LIKE '%hwcomposer%'
        OR p.name LIKE '%/hwc%'
        OR t.name LIKE 'hwcomposer%' THEN 'hwc'
        WHEN t.name GLOB 'xe-*'
        OR t.name GLOB 'xe_*'
        OR t.name GLOB 'kworker/*-xe*'
        OR t.name GLOB 'kworker/*xe_*'
        OR t.name GLOB 'irq/*-xe*'
        OR t.name GLOB 'card*-crtc*' THEN 'xe'
        WHEN t.name LIKE 'jbd2%' THEN 'jbd2'
        WHEN t.name LIKE 'kswapd%' THEN 'kswapd'
        WHEN t.name GLOB 'kworker/*' THEN 'kworker'
        ELSE 'other'
      END AS specific_group
    FROM thread_state AS ts
    LEFT JOIN thread AS t USING (utid)
    LEFT JOIN process AS p USING (upid)
    WHERE
      ts.state = 'D'
      AND ts.dur > 0
  ),
  expanded_events AS (
    SELECT 'all' AS process_group, dur FROM d_events
    UNION ALL
    SELECT specific_group AS process_group, dur
    FROM d_events
    WHERE
      specific_group != 'other'
  )
SELECT
  g.process_group,
  count(e.dur) AS stall_count,
  COALESCE(sum(e.dur) / 1000000.0, 0.0) AS total_ms,
  COALESCE(max(e.dur) / 1000000.0, 0.0) AS max_ms,
  COALESCE(sum(CASE WHEN e.dur > 10000000 THEN 1 ELSE 0 END), 0) AS over_10ms_count,
  COALESCE(sum(CASE WHEN e.dur > 50000000 THEN 1 ELSE 0 END), 0) AS over_50ms_count,
  COALESCE(sum(CASE WHEN e.dur > 100000000 THEN 1 ELSE 0 END), 0) AS over_100ms_count
FROM groups AS g
LEFT JOIN expanded_events AS e ON g.process_group = e.process_group
GROUP BY
  g.process_group;

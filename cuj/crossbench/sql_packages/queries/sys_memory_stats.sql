-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS sys_memory_stats_output;

CREATE PERFETTO TABLE sys_memory_stats_output AS
SELECT
  min(CASE WHEN t.type = 'meminfo' AND t.name = 'MemFree' THEN c.value END)
  / 1048576.0 AS mem_free_min_mb,
  avg(CASE WHEN t.type = 'meminfo' AND t.name = 'MemFree' THEN c.value END)
  / 1048576.0 AS mem_free_avg_mb,
  min(CASE WHEN t.type = 'meminfo' AND t.name = 'MemAvailable' THEN c.value END)
  / 1048576.0 AS mem_available_min_mb,
  avg(CASE WHEN t.type = 'meminfo' AND t.name = 'MemAvailable' THEN c.value END)
  / 1048576.0 AS mem_available_avg_mb,
  (max(CASE WHEN t.type = 'meminfo' AND t.name = 'SwapTotal' THEN c.value END)
  - min(CASE WHEN t.type = 'meminfo' AND t.name = 'SwapFree' THEN c.value END))
  / 1048576.0 AS swap_used_max_mb,
  (max(CASE WHEN t.type = 'meminfo' AND t.name = 'SwapTotal' THEN c.value END)
  - avg(CASE WHEN t.type = 'meminfo' AND t.name = 'SwapFree' THEN c.value END))
  / 1048576.0 AS swap_used_avg_mb,
  max(CASE WHEN t.type = 'meminfo' AND t.name = 'Dirty' THEN c.value END)
  / 1048576.0 AS dirty_max_mb,
  max(CASE WHEN t.type = 'meminfo' AND t.name = 'Writeback' THEN c.value END)
  / 1048576.0 AS writeback_max_mb,
  max(CASE WHEN t.type = 'gpu_memory' THEN c.value END) / 1048576.0 AS gpu_memory_max_mb,
  max(CASE WHEN t.type = 'vmstat' AND t.name = 'pswpin' THEN c.value END)
  - min(CASE WHEN t.type = 'vmstat' AND t.name = 'pswpin' THEN c.value END) AS pswpin_pages,
  max(CASE WHEN t.type = 'vmstat' AND t.name = 'pswpout' THEN c.value END)
  - min(CASE WHEN t.type = 'vmstat' AND t.name = 'pswpout' THEN c.value END) AS pswpout_pages,
  max(CASE WHEN t.type = 'vmstat' AND t.name = 'pgpgin' THEN c.value END)
  - min(CASE WHEN t.type = 'vmstat' AND t.name = 'pgpgin' THEN c.value END) AS pgpgin_kb,
  max(CASE WHEN t.type = 'vmstat' AND t.name = 'pgpgout' THEN c.value END)
  - min(CASE WHEN t.type = 'vmstat' AND t.name = 'pgpgout' THEN c.value END) AS pgpgout_kb,
  max(CASE WHEN t.type = 'vmstat' AND t.name = 'pgfault' THEN c.value END)
  - min(CASE WHEN t.type = 'vmstat' AND t.name = 'pgfault' THEN c.value END) AS pgfault_count
FROM counter AS c
JOIN counter_track AS t ON c.track_id = t.id
WHERE
  t.type IN ('meminfo', 'vmstat', 'gpu_memory');

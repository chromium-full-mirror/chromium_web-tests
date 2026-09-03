-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE chrome.histograms;

DROP TABLE IF EXISTS slow_input_thresholds;

DROP TABLE IF EXISTS slow_inputs_output;

-- Defines threshold constants for slow input latency classification.
-- Latency values in Chrome EventLatency histograms are in microseconds (us).
CREATE PERFETTO TABLE slow_input_thresholds(
  threshold_name STRING,
  threshold_ms LONG,
  threshold_us LONG
)
AS
SELECT
  column1 AS threshold_name,
  column2 AS threshold_ms,
  column3 AS threshold_us
FROM (
  VALUES
    ('100ms', 100, 100000), ('110ms', 110, 110000), ('120ms', 120, 120000),
    (
      '130ms',
      130,
      130000
    ), ('140ms', 140, 140000), ('150ms', 150, 150000), ('160ms', 160, 160000),
    (
      '170ms',
      170,
      170000
    ), ('180ms', 180, 180000), ('190ms', 190, 190000), ('200ms', 200, 200000)
);

-- Tracks slow input events across EventLatency.TotalLatency (combined) and all
-- specific event subtypes (EventLatency.*.TotalLatency, e.g. KeyPressed, MousePressed).
-- Calculates the percentage of events exceeding each latency threshold (100ms to 200ms in 10ms increments).
-- EventLatency histograms in Chrome record sample values in microseconds.
CREATE PERFETTO TABLE slow_inputs_output AS
WITH
  input_events AS (
    SELECT
      CASE
        WHEN name = 'EventLatency.TotalLatency' THEN 'all'
        WHEN name LIKE 'EventLatency.%.TotalLatency' THEN substr(
          name,
          14,
          length(name) - 26
        )
        ELSE name
      END AS event_type,
      value
    FROM chrome_histograms
    WHERE
      name LIKE 'EventLatency.%TotalLatency'
  ),
  threshold_counts AS (
    SELECT
      e.event_type,
      t.threshold_name,
      t.threshold_ms,
      t.threshold_us,
      count(*) AS total_count,
      sum(CASE WHEN e.value > t.threshold_us THEN 1 ELSE 0 END) AS slow_count
    FROM slow_input_thresholds AS t
    CROSS JOIN input_events AS e
    GROUP BY
      e.event_type,
      t.threshold_name,
      t.threshold_ms,
      t.threshold_us
  )
SELECT
  event_type,
  threshold_name,
  threshold_ms,
  threshold_us,
  slow_count,
  total_count,
  (CAST(slow_count AS DOUBLE) * 100.0) / total_count AS slow_percent
FROM threshold_counts
WHERE
  total_count > 0;

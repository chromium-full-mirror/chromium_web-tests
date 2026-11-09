-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS scroll_duration_output;

CREATE PERFETTO TABLE scroll_duration_output AS
SELECT
  COALESCE(
    (SELECT (dur / 1000000) FROM slice WHERE slice.name = 'scroll'),
    (
      SELECT
        (max(CASE WHEN slice.name = 'scroll-end' THEN slice.ts END)
        - min(CASE WHEN slice.name = 'scroll-begin' THEN slice.ts END))
        / 1000000
      FROM slice
      WHERE
        slice.category = 'blink.user_timing'
        AND slice.name IN ('scroll-begin', 'scroll-end')
    )
  ) AS "duration_ms";

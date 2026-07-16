-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS enum_table;

CREATE PERFETTO TABLE enum_table(
  histogram_name STRING,
  enum_name STRING,
  enum_value LONG
)
AS
SELECT column1 AS histogram_name, column2 AS enum_name, column3 AS enum_value
FROM (
  VALUES
    ('Viz.DisplayCompositor.OverlayStrategy', 'kUnknown', 0),
    ('Viz.DisplayCompositor.OverlayStrategy', 'kNoStrategyUsed', 1),
    ('Viz.DisplayCompositor.OverlayStrategy', 'kFullscreen', 2),
    ('Viz.DisplayCompositor.OverlayStrategy', 'kSingleOnTop', 3)
);

DROP TABLE IF EXISTS histogram_polarities;

CREATE PERFETTO TABLE histogram_polarities(
  histogram_prefix STRING,
  polarity STRING
)
AS
SELECT column1 AS histogram_prefix, column2 AS polarity
FROM (
  VALUES
    ('Graphics.Smoothness.Jank3.', 'LOWER_IS_BETTER'),
    ('Graphics.Smoothness.PercentDroppedFrames3.', 'LOWER_IS_BETTER'),
    ('Browser.Tabs.TotalSwitchDuration3', 'LOWER_IS_BETTER'),
    ('PageLoad.PaintTiming.', 'LOWER_IS_BETTER'),
    ('EventLatency.', 'LOWER_IS_BETTER'),
    ('PageLoad.InteractiveTiming.InputDelay3', 'LOWER_IS_BETTER'),
    ('Event.ScrollJank.', 'LOWER_IS_BETTER'),
    ('WebRTC.Video.DroppedFrames.', 'LOWER_IS_BETTER')
);

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
    ('Graphics.Smoothness.PercentDroppedFrames4.', 'LOWER_IS_BETTER'),
    ('Graphics.Smoothness.Checkerboarding3.', 'LOWER_IS_BETTER'),
    ('Graphics.Smoothness.Checkerboarding4.', 'LOWER_IS_BETTER'),
    ('Browser.Tabs.TotalSwitchDuration3', 'LOWER_IS_BETTER'),
    ('Browser.Tabs.TotalIncompleteSwitchDuration3', 'LOWER_IS_BETTER'),
    ('Compositing.Display.DrawToSwapUs', 'LOWER_IS_BETTER'),
    ('Compositing.Display.SwapStartToSwapEnd', 'LOWER_IS_BETTER'),
    (
      'Compositing.Display.OverlayProcessorUsingStrategy.NumOverlaysPromoted',
      'HIGHER_IS_BETTER'
    ),
    (
      'Compositing.Display.OverlayProcessorUsingStrategy.NumOverlaysFailed',
      'LOWER_IS_BETTER'
    ),
    ('Discarding.DiscardLatency', 'LOWER_IS_BETTER'),
    ('Memory.Browser.PrivateMemoryFootprint', 'LOWER_IS_BETTER'),
    ('Memory.Gpu.PrivateMemoryFootprint', 'LOWER_IS_BETTER'),
    ('Memory.Renderer.PrivateMemoryFootprint', 'LOWER_IS_BETTER'),
    ('Memory.Total.PrivateMemoryFootprint', 'LOWER_IS_BETTER'),
    ('PageLoad.Experimental.NavigationTiming.', 'LOWER_IS_BETTER'),
    ('PageLoad.PaintTiming.', 'LOWER_IS_BETTER'),
    ('EventLatency.', 'LOWER_IS_BETTER'),
    ('PageLoad.InteractiveTiming.FirstInputDelay4', 'LOWER_IS_BETTER'),
    ('PageLoad.InteractiveTiming.InputDelay3', 'LOWER_IS_BETTER'),
    ('PageLoad.InteractiveTiming.ProcessingTime', 'LOWER_IS_BETTER'),
    ('PageLoad.InteractiveTiming.TimeToNextPaint', 'LOWER_IS_BETTER'),
    ('PageLoad.InteractiveTiming.UserInteractionLatency.', 'LOWER_IS_BETTER'),
    (
      'PageLoad.InteractiveTiming.WorstUserInteractionLatency.',
      'LOWER_IS_BETTER'
    ),
    ('Startup.', 'LOWER_IS_BETTER'),
    ('Viz.FrameSink.GpuBusyDuration', 'LOWER_IS_BETTER'),
    ('Event.ScrollJank.', 'LOWER_IS_BETTER'),
    ('WebRTC.Video.DroppedFrames.', 'LOWER_IS_BETTER'),
    ('WebRTC.Video.DecodedFramesPerSecond', 'HIGHER_IS_BETTER'),
    ('WebRTC.Video.HarmonicFrameRate', 'HIGHER_IS_BETTER'),
    ('WebRTC.Video.RenderFramesPerSecond', 'HIGHER_IS_BETTER')
);

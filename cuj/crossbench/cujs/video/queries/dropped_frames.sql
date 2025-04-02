INCLUDE PERFETTO MODULE chrome.histograms;

select
  AVG(value) as 'avg_percent_dropped'
from
  chrome_histograms
where
  name = 'Graphics.Smoothness.PercentDroppedFrames3.AllSequences'
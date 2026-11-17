# `typing-input-latency` CUJ

## Overview
Benchmarks browser keyboard input-pipeline latency while typing prose into a simple local web page's text area. Variants compare a casual typing pace (20 WPM) against a fast typing pace (100 WPM) across idle, background CPU contention, and secondary-window video playback conditions to measure how competing workloads affect foreground keystroke responsiveness.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `20wpm` | `20wpm.page-config.hjson` | Casual 20 WPM typing pace with no background workload. |
| `20wpm-with-background-cpu` | `20wpm-with-background-cpu.page-config.hjson` | Casual 20 WPM typing pace while a hidden background tab runs spinning Web Workers to saturate CPU cores. |
| `20wpm-with-background-video` | `20wpm-with-background-video.page-config.hjson` | Casual 20 WPM typing pace while a secondary browser window plays a looping 1080p60 VP9 video. |
| `100wpm` | `100wpm.page-config.hjson` | Fast 100 WPM typing pace with no background workload. |
| `100wpm-with-background-cpu` | `100wpm-with-background-cpu.page-config.hjson` | Fast 100 WPM typing pace while a hidden background tab runs spinning Web Workers to saturate CPU cores. |
| `100wpm-with-background-video` | `100wpm-with-background-video.page-config.hjson` | Fast 100 WPM typing pace while a secondary browser window plays a looping 1080p60 VP9 video. |

## Workflow
- **Prerequisites & Setup**: Crossbench starts a local HTTP file server hosting the static typing-tracker page so the foreground workload runs offline without network variance (no Google account login is needed). Background-load variants first open a secondary browser window: CPU-load variants launch a multi-worker CPU spin page and cover it with a second tab (`example.com`) so the worker tab is occluded, while video-load variants start looping 1080p60 VP9 playback (requiring internet access to the video host and unmuted/gestureless autoplay support) before returning focus to the primary tab.
- **Main Actions**: Navigates the primary tab to the local typing-tracker page, clicks the text area with native mouse input to focus it, types five 100-character sentences (500 characters total) via native keyboard input paced at either 20 WPM or 100 WPM, and validates via JavaScript that the page's live character counter equals 500.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Native input dispatch**: Always focus the text area with native mouse input and type via native keyboard keystrokes rather than JavaScript-synthesized events; `EventLatency` slow-input histograms depend on real OS/WebDriver input routing.
- **Exact character count and pacing**: Preserve the five 100-character sentences (500 characters total), the per-variant WPM pacing, and the post-typing character-count assertion so dropped keystrokes fail the run and keystroke sample counts stay comparable.
- **Background-load window visibility**: In background-CPU variants, keep the CPU-worker tab covered by a real web page (not `about:blank`) in the secondary window so Chrome demotes it to background priority. In background-video variants, keep the secondary video window visible/unoccluded so media decoding is not background-throttled, while keeping typing focus on the primary tab.

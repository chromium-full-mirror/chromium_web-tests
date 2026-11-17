# `meet-note` CUJ

## Overview
Benchmarks dual-window collaborative note-taking in Google Docs alongside an active Google Meet call with live participant screen-sharing. By running an active Meet conference (with participant tiles and a bot presentation feed) in one window while typing continuously into a Google Doc in a second window, this CUJ stresses multi-window compositing, WebRTC media pipelines, and interactive typing responsiveness simultaneously.

## Variants
Variants span **call size** (3, 8, or 48 synthetic Bond bots plus 1 local user = 4, 9, or 49 total participants in tiled layouts, with one bot screen-sharing) and **camera background blur** (disabled vs enabled).

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `4p` | `4p.page-config.hjson` | 4 total participants (3 Bond bots + 1 user, tiled layout + bot screen-share); camera background blur disabled. |
| `4p-background-blur` | `4p-background-blur.page-config.hjson` | 4 total participants (3 Bond bots + 1 user, tiled layout + bot screen-share); camera background blur enabled. |
| `9p` | `9p.page-config.hjson` | 9 total participants (8 Bond bots + 1 user, 4x4 tiled layout + bot screen-share); camera background blur disabled. |
| `9p-background-blur` | `9p-background-blur.page-config.hjson` | 9 total participants (8 Bond bots + 1 user, 4x4 tiled layout + bot screen-share); camera background blur enabled. |
| `49p` | `49p.page-config.hjson` | 49 total participants (48 Bond bots + 1 user, 7x7 tiled layout + bot screen-share); camera background blur disabled. |
| `49p-background-blur` | `49p-background-blur.page-config.hjson` | 49 total participants (48 Bond bots + 1 user, 7x7 tiled layout + bot screen-share); camera background blur enabled. |

## Workflow
- **Prerequisites & Setup**: Requires Google test account credentials and Bond API service-account secrets. Unlike standalone `meet`, media permissions are not auto-granted by browser flags—setup explicitly accepts in-page and OS camera/microphone permission prompts, sets 720p send / 1080p receive video caps and the variant's background-blur state, joins the call, and marks `'meet-joined'` once participant videos render. Setup then opens a new blank Google Doc in a second browser window, triggers a Bond bot to begin presenting in the Meet call, and focuses the Docs editor canvas.
- **Main Actions**: Types a pangram sentence repeatedly into the Google Docs canvas using paced native keyboard input for 2 minutes total while the Meet conference and bot presentation stream render concurrently in the other window.
- **Teardown**: Moves the newly created Google Doc to Drive Trash via the Docs File menu so test accounts do not accumulate untitled documents, and removes all provisioned Bond bots from the Meet call.

## Metrics & Invariants (Preserve When Healing)
- **True Dual-Window Concurrency**: Keep Google Docs in a separate browser window (not a background tab in the Meet window) so both the live Meet video/presentation compositor and the Docs canvas editor remain active concurrently.
- **Media Permission Prompt Handling**: Preserve explicit handling for in-page and system camera/microphone permission dialogs since this CUJ runs without auto-granted media-stream flags.
- **`'meet-joined'` Gate, Bot Screen-Share & Blur State**: Preserve `'meet-joined'` (which gates post-join Meet smoothness and jank metrics), active bot screen-sharing, participant bot counts, 720p/1080p resolution caps, and verified background-blur state.
- **Native Input & Docs Trash Cleanup**: Use native touch clicks and paced native keyboard typing throughout, and preserve the end-of-run Docs trash cleanup flow to prevent Google Drive clutter.

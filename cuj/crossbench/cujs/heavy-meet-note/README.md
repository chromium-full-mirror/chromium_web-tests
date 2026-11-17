# `heavy-meet-note` CUJ

## Overview
Benchmarks heavy 3-window Google Workspace multitasking across a large Google Slides presentation, a large Google Sheets spreadsheet, and an active Google Meet conference with live bot screen-sharing. Across multiple cross-window collaboration cycles, it stresses multi-window graphics compositing, DOM/canvas scrolling, Workspace comment anchoring, and WebRTC video processing under sustained memory and CPU pressure.

## Variants
Variants span **call size** (3, 8, or 48 synthetic Bond bots plus 1 local user = 4, 9, or 49 total participants in tiled layouts, with one bot presenting) and **camera background blur** (disabled vs enabled), all executing a 5-iteration cross-window Workspace collaboration loop.

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `4p` | `4p.page-config.hjson` | 4 total participants (3 Bond bots + 1 user, tiled layout + bot screen-share), background blur disabled, 5 collaboration iterations. |
| `4p-background-blur` | `4p-background-blur.page-config.hjson` | 4 total participants (3 Bond bots + 1 user, tiled layout + bot screen-share), background blur enabled, 5 collaboration iterations. |
| `9p` | `9p.page-config.hjson` | 9 total participants (8 Bond bots + 1 user, 4x4 tiled layout + bot screen-share), background blur disabled, 5 collaboration iterations. |
| `9p-background-blur` | `9p-background-blur.page-config.hjson` | 9 total participants (8 Bond bots + 1 user, 4x4 tiled layout + bot screen-share), background blur enabled, 5 collaboration iterations. |
| `49p` | `49p.page-config.hjson` | 49 total participants (48 Bond bots + 1 user, 7x7 tiled layout + bot screen-share), background blur disabled, 5 collaboration iterations. |
| `49p-background-blur` | `49p-background-blur.page-config.hjson` | 49 total participants (48 Bond bots + 1 user, 7x7 tiled layout + bot screen-share), background blur enabled, 5 collaboration iterations. |

## Workflow
- **Prerequisites & Setup**: Requires Google test account login, Bond API service-account secrets, and Google Workspace Shared Drive service-account secrets (with auto-granted browser media permissions). One-time setup creates isolated Shared Drive copies of a heavy template Slides deck in Window 1 and a heavy template Sheets workbook in Window 2, then opens Window 3 to provision and join a Bond-backed Meet call (720p send / 1080p receive, verified background-blur state, and a bot actively presenting) and marks `'meet-joined'`.
- **Main Actions**: Executes 5 back-to-back collaboration iterations cycling across all three windows:
  1. **Slides**: Switches to Slides, touch-scrolls the slide filmstrip, selects slide 25, and inserts and posts a typed comment.
  2. **Sheets**: Switches to Sheets, touch-scrolls the spreadsheet grid, selects a cell, and inserts and posts a typed comment.
  3. **Meet**: Switches to Meet, sends a thumbs-up emoji reaction, opens the in-call chat panel, and types and sends a chat message.
- **Teardown**: Bond bots are automatically removed from the conference on exit, and the copied Slides and Sheets files in the Shared Drive carry a 4-hour TTL metadata tag for automated expiration.

## Metrics & Invariants (Preserve When Healing)
- **3-Window Topology & One-Time Setup Isolation**: Keep Slides, Sheets, and Meet in three separate browser windows, and keep template file copying and meeting creation strictly in one-time setup so the 5-iteration playback loop only repeats cross-window user interactions.
- **Shared Drive Copy Isolation & Loop-Idempotent Controls**: Always operate on fresh Shared Drive copies rather than shared template files, and keep Meet reaction/chat tray and Workspace comment interactions state-aware (opening panels only if not already open and confirming comment submission finishes) so all 5 iterations succeed cleanly.
- **User Timing Marks (`'meet-joined'` & Comment Latency)**: Preserve `'meet-joined'` (gating post-join Meet smoothness/jank metrics) and the comment-creation observer marks (`'comment-click'`, `'comment-opened'`, and `'comment-type'`).
- **Bot/Blur Configuration & Native Input**: Preserve Bond bot counts, bot screen-sharing, 720p/1080p caps, verified background-blur state, and native touch clicks/scrolls plus native keyboard typing.

# `meet` CUJ

## Overview
Benchmarks steady-state Google Meet video conferencing performance—covering live multi-stream WebRTC decode/encode, participant tile compositing, graphics smoothness, and optional camera background blur—in a single maximized browser tab. Real Meet client code paths are exercised at controlled call sizes using dynamically provisioned conference rooms and synthetic bot participants.

## Variants
Variants span two axes: **call size** (3, 8, or 48 synthetic Bond bots plus 1 local user = 4, 9, or 49 total participants in tiled layouts) and **camera background blur** (disabled for baseline conferencing vs enabled to stress real-time ML segmentation and GPU blur shaders).

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `4p` | `4p.page-config.hjson` | 4 total participants (3 Bond bots + 1 user) in a tiled layout; camera background blur disabled. |
| `4p-background-blur` | `4p-background-blur.page-config.hjson` | 4 total participants (3 Bond bots + 1 user) in a tiled layout; camera background blur enabled. |
| `9p` | `9p.page-config.hjson` | 9 total participants (8 Bond bots + 1 user) in a 4x4 tiled layout; camera background blur disabled. |
| `9p-background-blur` | `9p-background-blur.page-config.hjson` | 9 total participants (8 Bond bots + 1 user) in a 4x4 tiled layout; camera background blur enabled. |
| `49p` | `49p.page-config.hjson` | 49 total participants (48 Bond bots + 1 user) in a 7x7 tiled layout; camera background blur disabled. |
| `49p-background-blur` | `49p-background-blur.page-config.hjson` | 49 total participants (48 Bond bots + 1 user) in a 7x7 tiled layout; camera background blur enabled. |

## Workflow
- **Prerequisites & Setup**: Requires Google test account credentials for sign-in and Bond API service-account secrets to create a live Meet room populated with video- and audio-streaming bots; camera and microphone permissions are auto-granted by the browser configuration. In the pre-join green room, setup dismisses optional notification prompts, caps maximum video send resolution to 720p and receive resolution to 1080p, explicitly configures and verifies the variant's background-blur toggle state, joins the call, and waits until self and bot video feeds are visibly rendering before marking `'meet-joined'`.
- **Main Actions**: Remains in the active Meet call in a single maximized tab for 60 seconds of steady-state multi-participant video rendering and local camera encoding.
- **Teardown**: Crossbench's Bond integration automatically removes all provisioned bots from the conference when the run ends.

## Metrics & Invariants (Preserve When Healing)
- **`'meet-joined'` User Timing Gate**: Preserve the check that multiple non-PiP participant video feeds are visible before emitting `'meet-joined'` (along with `'meet-created'`, `'camera-start'`, and `'camera-ready'`), as post-join Meet smoothness and frame-jank metrics filter strictly to samples recorded after `'meet-joined'`.
- **Participant Grid & Resolution Standardization**: Keep the exact Bond bot counts, tiled multi-participant layouts, and 720p send / 1080p receive resolution settings so WebRTC codec and compositor workloads do not drift.
- **Explicit Background-Blur State Verification**: Always verify the actual toggled state of background blur in the green room rather than blindly clicking, preventing persisted Google account preferences from inverting blur vs non-blur variants.
- **Native Touch Input**: Use native touch input (never synthetic JS clicks) when interacting with Meet menus, settings, and join controls.

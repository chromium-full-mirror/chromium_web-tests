# `meet-share-note` CUJ

## Overview
Benchmarks collaborative note-taking in Google Docs alongside a multi-party Google Meet video call while the local device actively shares its screen into the meeting. Unlike Meet CUJs where a remote bot presents (`meet-note`, `heavy-meet-note`), `meet-share-note` drives the local client to capture and stream its own browser tab, application window, or entire display. This simultaneously stresses multi-window compositing, OS and browser screen capture, real-time WebRTC video encoding and decoding (optionally with camera background blur), and live typing responsiveness.

## Variants
The 18 variants span three orthogonal axes:
- **Participants**: `4p` (3 bots + user), `9p` (8 bots + user), or `49p` (48 bots + user), automatically arranged in a tiled Meet layout scaled to the call size.
- **Capture Surface**: Single browser tab (Google Docs, no infix), application window (`-window`, Chrome), or entire display (`-display`).
- **Camera Background Blur**: Disabled (no suffix) or enabled (`-background-blur`) on the outgoing self-camera stream.

| Variant | Config File | Participants | Capture Surface | Background Blur |
| :--- | :--- | :--- | :--- | :--- |
| `4p` | `4p.page-config.hjson` | 4 (3 bots + user) | Browser tab (Google Docs) | Off |
| `4p-background-blur` | `4p-background-blur.page-config.hjson` | 4 (3 bots + user) | Browser tab (Google Docs) | On |
| `4p-window` | `4p-window.page-config.hjson` | 4 (3 bots + user) | Application window (Chrome) | Off |
| `4p-window-background-blur` | `4p-window-background-blur.page-config.hjson` | 4 (3 bots + user) | Application window (Chrome) | On |
| `4p-display` | `4p-display.page-config.hjson` | 4 (3 bots + user) | Entire display | Off |
| `4p-display-background-blur` | `4p-display-background-blur.page-config.hjson` | 4 (3 bots + user) | Entire display | On |
| `9p` | `9p.page-config.hjson` | 9 (8 bots + user) | Browser tab (Google Docs) | Off |
| `9p-background-blur` | `9p-background-blur.page-config.hjson` | 9 (8 bots + user) | Browser tab (Google Docs) | On |
| `9p-window` | `9p-window.page-config.hjson` | 9 (8 bots + user) | Application window (Chrome) | Off |
| `9p-window-background-blur` | `9p-window-background-blur.page-config.hjson` | 9 (8 bots + user) | Application window (Chrome) | On |
| `9p-display` | `9p-display.page-config.hjson` | 9 (8 bots + user) | Entire display | Off |
| `9p-display-background-blur` | `9p-display-background-blur.page-config.hjson` | 9 (8 bots + user) | Entire display | On |
| `49p` | `49p.page-config.hjson` | 49 (48 bots + user) | Browser tab (Google Docs) | Off |
| `49p-background-blur` | `49p-background-blur.page-config.hjson` | 49 (48 bots + user) | Browser tab (Google Docs) | On |
| `49p-window` | `49p-window.page-config.hjson` | 49 (48 bots + user) | Application window (Chrome) | Off |
| `49p-window-background-blur` | `49p-window-background-blur.page-config.hjson` | 49 (48 bots + user) | Application window (Chrome) | On |
| `49p-display` | `49p-display.page-config.hjson` | 49 (48 bots + user) | Entire display | Off |
| `49p-display-background-blur` | `49p-display-background-blur.page-config.hjson` | 49 (48 bots + user) | Entire display | On |

## Workflow
- **Prerequisites & Setup**: Requires an Android target providing the native system screen-share (MediaProjection) picker, active camera and microphone access, a Google test account with Docs/Drive access, and Bond API credentials in `--secrets` to provision remote Meet bots.
- **Main Actions**: Creates a Meet call populated with remote Bond bots, configures 720p send / 1080p receive video quality and the variant's camera background-blur state, joins the call, and confirms active video playback. Opens a new Google Doc in a second browser window, switches back to Meet to start presenting and select the variant's target surface (Docs tab, Chrome window, or entire display) through the Android OS screen-share picker, then refocuses the Google Docs window and types notes continuously via paced keyboard input while presenting.
- **Teardown**: Moves the created Google Doc to Trash so untitled documents do not accumulate in Google Drive, and tears down all provisioned Bond bots from the conference.

## Metrics & Invariants (Preserve When Healing)
- **Real OS Permission & Screen-Share UI**: Drive the real camera/microphone permission prompts and the native Android OS screen-share picker; never bypass them with fake-media-UI or auto-capture browser flags.
- **Capture Surface Fidelity**: Preserve each variant's exact screen-share target (Google Docs browser tab vs. Chrome application window vs. entire display), as each exercises a distinct browser and OS MediaProjection capture and compositing path.
- **Call Load & Visual Effects**: Maintain each variant's participant count (and tiled grid scale), 720p send / 1080p receive video caps, verified active video playback before measurement, and explicitly verified camera background-blur state (`On` vs. `Off`) prior to joining.
- **Dual-Window Layout & Native Input**: Keep Google Docs in a separate browser window from Google Meet, and perform all interactions via native touch clicks and paced native keyboard typing rather than synthetic JavaScript clicks or instant text injection.
- **`'meet-joined'` Timing Anchor**: Preserve the `'meet-joined'` User Timing mark emitted once the call and video feeds are active, as trace-based Meet jank and smoothness metrics scope histogram samples strictly after `'meet-joined'`.

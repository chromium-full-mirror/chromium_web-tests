# `local-conference` CUJ

## Overview
Benchmarks deterministic local WebRTC multi-party video conferencing encode, decode, and video-grid compositing performance without external network variance. A single local VP9 camera encode stream is cloned across loopback peer connections to drive multiple concurrent VP9 decoders rendered on a local conference page, isolating media codec and compositor scaling from 4 to 49 participants.

## Variants
Variants scale total simulated call size (1 local camera encoder feeding *N* - 1 loopback VP9 decoders) along with the outgoing stream resolution, scalability mode, and video-grid layout.

| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `4p` | `4p.page-config.hjson` | 4 total participants (1 encoder + 3 loopback decoders at 640x360 k-SVC); renders the local self-preview inside a 2x2 grid alongside the 3 remote video tiles. |
| `16p` | `16p.page-config.hjson` | 16 total participants (1 encoder + 15 loopback decoders at 480x270 k-SVC); renders 15 remote video tiles in a 4x4 grid with a floating bottom-right self-preview overlay. |
| `49p` | `49p.page-config.hjson` | 49 total participants (1 encoder + 48 loopback decoders at 240x135 temporal SVC); renders 48 remote video tiles in a 7x7 grid with a floating bottom-right self-preview overlay. |

## Workflow
- **Prerequisites & Setup**: Crossbench serves the local WebRTC conference test app over a local HTTP server and launches Chrome with auto-granted media capture and WebRTC Encoded Transform metadata support enabled. No Google account login, external network access, or service-account secrets are required.
- **Main Actions**: Opens the local conference page, starts camera and microphone capture with self-preview, and establishes loopback VP9 peer connections for the target participant count by cloning encoded video frames across receivers. Once the outbound codec, resolution, and scalability mode stabilize, the page waits through a post-connection cooldown period before sampling WebRTC encode/decode statistics and recording User Timing marks.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Single-Encoder Fan-Out & Scaling**: Preserve the exact participant count, VP9 codec/scalability configuration, and single-encoder SSRC frame-cloning design so hardware/software encode and multi-stream decode load remain comparable across variants.
- **Zero-Prompt Local Media Execution**: Keep local HTTP serving, auto-granted camera/microphone access, and WebRTC Encoded Transform metadata capabilities intact so peer connections initialize deterministically without permission prompts.
- **Stabilization, Cooldown & User Timing Marks**: Preserve the stream-stabilization check and post-startup cooldown before measurement, as well as the User Timing marks (`'tx.encode_time_camera_enc'`, `'tx.frames_per_second_camera_enc'`, `'rx.decode_time_median_dec'`, and `'rx.dropped_frames_percentage_median_dec'`) alongside system CPU, GPU, memory, and smoothness metrics.

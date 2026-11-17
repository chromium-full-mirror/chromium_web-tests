# `rtc-peer-connection` CUJ

## Overview
The `rtc-peer-connection` CUJ benchmarks WebRTC loopback video encoding and decoding performance—tracking frame rate, per-frame encode and decode latency, and dropped-frame ratio. Across 36 variants, it evaluates AV1, H.264, VP8, and VP9 codecs under single-stream, temporal/spatial SVC, and multi-layer simulcast configurations using synthetic fake-webcam or live physical camera feeds, with configurable hardware acceleration verification.

## Variants
Variants span four primary dimensions:
- **Codec**: AV1 (6 variants), H.264 (4 variants), VP8 (10 variants), and VP9 (16 variants).
- **Scalability & Simulcast Mode**: Single-stream non-SVC, single-stream temporal SVC (`L1T2`, `L1T3`), 3-layer simulcast (`L1T1` for VP8; `L1T3` per layer for VP9), and 3-spatial-layer VP9 SVC using either key-frame inter-layer dependency (`L3T3_KEY` k-SVC) or independent spatial layers (`S3T3` S-mode).
- **Capture Source & Resolution**: Synthetic fake webcam input (33 variants) vs. live physical device camera input (3 `*-cam-*` variants), captured at 720p (`1280x720`, 34 variants) or 1080p (`1920x1080`, 2 `vp9-1080p-*` variants).
- **Hardware Acceleration Verification**: Enforces hardware encoding (`*-verify-hw-enc`), enforces hardware decoding (`*-verify-hw-dec`), or permits software codec fallback (`*-no-verify-hw`).

| Variant | Config File | Codec & Mode | Source & Resolution | HW Verification |
| :--- | :--- | :--- | :--- | :--- |
| `av1-no-verify-hw` | `av1-no-verify-hw.page-config.hjson` | AV1 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | None (SW fallback allowed) |
| `av1-svc-l1t2-verify-hw-enc` | `av1-svc-l1t2-verify-hw-enc.page-config.hjson` | AV1 · Temporal SVC (`L1T2`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `av1-svc-l1t3-verify-hw-dec` | `av1-svc-l1t3-verify-hw-dec.page-config.hjson` | AV1 · Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `av1-svc-l1t3-verify-hw-enc` | `av1-svc-l1t3-verify-hw-enc.page-config.hjson` | AV1 · Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `av1-verify-hw-dec` | `av1-verify-hw-dec.page-config.hjson` | AV1 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `av1-verify-hw-enc` | `av1-verify-hw-enc.page-config.hjson` | AV1 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `h264-cam-verify-hw-enc` | `h264-cam-verify-hw-enc.page-config.hjson` | H.264 · Single-stream | Physical device camera · 720p (`1280x720`) | Hardware encoder required |
| `h264-no-verify-hw` | `h264-no-verify-hw.page-config.hjson` | H.264 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | None (SW fallback allowed) |
| `h264-verify-hw-dec` | `h264-verify-hw-dec.page-config.hjson` | H.264 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `h264-verify-hw-enc` | `h264-verify-hw-enc.page-config.hjson` | H.264 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp8-cam-verify-hw-enc` | `vp8-cam-verify-hw-enc.page-config.hjson` | VP8 · Single-stream | Physical device camera · 720p (`1280x720`) | Hardware encoder required |
| `vp8-no-verify-hw` | `vp8-no-verify-hw.page-config.hjson` | VP8 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | None (SW fallback allowed) |
| `vp8-simulcast-no-verify-hw` | `vp8-simulcast-no-verify-hw.page-config.hjson` | VP8 · 3-layer Simulcast (`L1T1`) | Synthetic fake webcam · 720p (`1280x720`) | None (SW fallback allowed) |
| `vp8-simulcast-verify-hw-enc` | `vp8-simulcast-verify-hw-enc.page-config.hjson` | VP8 · 3-layer Simulcast (`L1T1`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp8-svc-l1t2-verify-hw-dec` | `vp8-svc-l1t2-verify-hw-dec.page-config.hjson` | VP8 · Temporal SVC (`L1T2`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp8-svc-l1t2-verify-hw-enc` | `vp8-svc-l1t2-verify-hw-enc.page-config.hjson` | VP8 · Temporal SVC (`L1T2`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp8-svc-l1t3-verify-hw-dec` | `vp8-svc-l1t3-verify-hw-dec.page-config.hjson` | VP8 · Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp8-svc-l1t3-verify-hw-enc` | `vp8-svc-l1t3-verify-hw-enc.page-config.hjson` | VP8 · Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp8-verify-hw-dec` | `vp8-verify-hw-dec.page-config.hjson` | VP8 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp8-verify-hw-enc` | `vp8-verify-hw-enc.page-config.hjson` | VP8 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp9-1080p-verify-hw-dec` | `vp9-1080p-verify-hw-dec.page-config.hjson` | VP9 · Single-stream | Synthetic fake webcam · 1080p (`1920x1080`) | Hardware decoder required |
| `vp9-1080p-verify-hw-enc` | `vp9-1080p-verify-hw-enc.page-config.hjson` | VP9 · Single-stream | Synthetic fake webcam · 1080p (`1920x1080`) | Hardware encoder required |
| `vp9-cam-verify-hw-enc` | `vp9-cam-verify-hw-enc.page-config.hjson` | VP9 · Single-stream | Physical device camera · 720p (`1280x720`) | Hardware encoder required |
| `vp9-no-verify-hw` | `vp9-no-verify-hw.page-config.hjson` | VP9 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | None (SW fallback allowed) |
| `vp9-simulcast-l1t3-no-verify-hw` | `vp9-simulcast-l1t3-no-verify-hw.page-config.hjson` | VP9 · 3-layer Simulcast + Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | None (SW fallback allowed) |
| `vp9-simulcast-l1t3-verify-hw-enc` | `vp9-simulcast-l1t3-verify-hw-enc.page-config.hjson` | VP9 · 3-layer Simulcast + Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp9-svc-l1t2-verify-hw-dec` | `vp9-svc-l1t2-verify-hw-dec.page-config.hjson` | VP9 · Temporal SVC (`L1T2`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp9-svc-l1t2-verify-hw-enc` | `vp9-svc-l1t2-verify-hw-enc.page-config.hjson` | VP9 · Temporal SVC (`L1T2`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp9-svc-l1t3-verify-hw-dec` | `vp9-svc-l1t3-verify-hw-dec.page-config.hjson` | VP9 · Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp9-svc-l1t3-verify-hw-enc` | `vp9-svc-l1t3-verify-hw-enc.page-config.hjson` | VP9 · Temporal SVC (`L1T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp9-svc-l3t3-key-verify-hw-dec` | `vp9-svc-l3t3-key-verify-hw-dec.page-config.hjson` | VP9 · Spatial k-SVC (`L3T3_KEY`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp9-svc-l3t3-key-verify-hw-enc` | `vp9-svc-l3t3-key-verify-hw-enc.page-config.hjson` | VP9 · Spatial k-SVC (`L3T3_KEY`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp9-svc-s3t3-verify-hw-dec` | `vp9-svc-s3t3-verify-hw-dec.page-config.hjson` | VP9 · Spatial S-mode SVC (`S3T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp9-svc-s3t3-verify-hw-enc` | `vp9-svc-s3t3-verify-hw-enc.page-config.hjson` | VP9 · Spatial S-mode SVC (`S3T3`) | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |
| `vp9-verify-hw-dec` | `vp9-verify-hw-dec.page-config.hjson` | VP9 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware decoder required |
| `vp9-verify-hw-enc` | `vp9-verify-hw-enc.page-config.hjson` | VP9 · Single-stream | Synthetic fake webcam · 720p (`1280x720`) | Hardware encoder required |

## Workflow
- **Prerequisites & Setup**:
  - Requires live network access to the public ChromiumOS WebRTC loopback test page hosted on `storage.googleapis.com` (no user login, credentials, or WPR archive is used).
  - Standard variants rely on Chrome's synthetic fake webcam feed with auto-granted media permissions, whereas `*-cam-*` variants require an operational physical camera on the target device.
  - `*-verify-hw-enc` and `*-verify-hw-dec` variants require hardware video encoder or decoder support on the target device for the configured codec, resolution, and SVC/simulcast profile; `*-no-verify-hw` variants can execute on devices that fall back to software codecs.
- **Main Actions**:
  1. Navigates to the hosted WebRTC loopback test harness.
  2. Captures camera media and establishes a local WebRTC loopback call configured for the variant's target codec, resolution, and single-stream, multi-layer simulcast, or temporal/spatial SVC mode (cloning spatial SVC layers across parallel loopback receivers via WebRTC Encoded Transform).
  3. Allows the loopback video stream to warm up and stabilize playback.
  4. Queries WebRTC peer-connection stats to assert that video frames are actively encoded and decoded, and checks hardware encoder or decoder engagement when required by the variant.
  5. Samples outbound and inbound WebRTC RTP statistics across a steady-state measurement window and records frame rate, encode/decode frame times, and dropped-frame ratio via a User Timing mark.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Codec, Resolution, & Layer Topology**: Preserve each variant's exact video codec, capture resolution (720p vs. 1080p), resolution-preserving degradation preference, and stream structure—single-stream, 3-layer simulcast, temporal SVC (`L1T2`, `L1T3`), or 3-spatial-layer k-SVC/S-mode (`L3T3_KEY`, `S3T3`).
- **Physical Camera vs. Synthetic Capture**: Keep `*-cam-*` variants bound to live physical device camera capture and keep all other variants on the synthetic fake webcam feed; never substitute synthetic media into physical-camera variants or vice versa.
- **Hardware Acceleration Assertions**: Never weaken or bypass mandatory hardware encoder (`powerEfficientEncoder`) or hardware decoder (`powerEfficientDecoder`) assertions on `*-verify-hw-enc` and `*-verify-hw-dec` variants to mask software codec fallback, and retain active frame encode/decode liveness checks across all variants.
- **`'rtc-perf'` User Timing Metric Contract**: Maintain active loopback RTP video transmission and continue emitting the `'rtc-perf'` User Timing mark containing `fps`, `encode_time_ms`, `decode_time_ms`, and `dropped_frames_ratio` for downstream trace metric extraction.

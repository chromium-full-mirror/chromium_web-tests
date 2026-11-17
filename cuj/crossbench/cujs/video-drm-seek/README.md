# `video-drm-seek` CUJ

## Overview
The `video-drm-seek` CUJ benchmarks seek latency (`cuj.video-seek.avg_seek_time_s`) and seek completion rate (`cuj.video-seek.seek_completion_percentage`) during Widevine L1 hardware-secure (`HW_SECURE_ALL`) encrypted DASH video playback in Shaka Player. It evaluates deterministic random seeking across `cenc` (AES-CTR) and `cbcs` (AES-CBC) encryption schemes, AV1, H.264, HEVC, and VP9 codecs, and adaptive bitrate (ABR), HD-only, and static DASH manifests.

## Variants
All variants perform 10 deterministic pseudo-random seeks while varying three media axes:
- **Encryption Scheme**: CENC `cenc` (AES-CTR in MP4, or WebM subsample CTR for VP9) vs. CENC v3 `cbcs` (AES-CBC pattern encryption in MP4).
- **Codec**: 8-bit AV1, H.264, and HEVC (MP4 video + encrypted AAC audio), plus 8-bit VP9 (WebM video + encrypted Opus audio).
- **Stream Mode**: `adaptive` manifests expose full SD-to-HD/UHD ABR ladders (allowing resolution switches across seeks), `hd` manifests restrict the ABR ladder to 720p and 1080p tiers, and `static` (`av1_cenc_static`) uses a single fixed 240p representation to isolate DRM seek overhead without ABR switching.

| Variant | Config File | Encryption Scheme | Codec & Container | Stream Mode & Resolution Ladder |
| :--- | :--- | :--- | :--- | :--- |
| `av1_cbcs_adaptive` | `av1_cbcs_adaptive.page-config.hjson` | CENC v3 `cbcs` (AES-CBC) | 8-bit AV1 Main (MP4 + AAC, 30fps) | Adaptive ABR (5 tiers: 240p to 4K UHD) |
| `av1_cbcs_hd` | `av1_cbcs_hd.page-config.hjson` | CENC v3 `cbcs` (AES-CBC) | 8-bit AV1 Main (MP4 + AAC, 30fps) | HD-only ABR (2 tiers: 720p, 1080p) |
| `av1_cenc_adaptive` | `av1_cenc_adaptive.page-config.hjson` | CENC `cenc` (AES-CTR) | 8-bit AV1 Main (MP4 + AAC, 24fps) | Adaptive ABR (3 tiers: 240p to 720p) |
| `av1_cenc_static` | `av1_cenc_static.page-config.hjson` | CENC `cenc` (AES-CTR) | 8-bit AV1 Main (MP4 + AAC, 24fps) | Static single-representation (240p) |
| `h264_cbcs_adaptive` | `h264_cbcs_adaptive.page-config.hjson` | CENC v3 `cbcs` (AES-CBC) | 8-bit H.264 Base/Main/High (MP4 + AAC, 30fps) | Adaptive ABR (4 tiers: 240p to 1080p) |
| `h264_cbcs_hd` | `h264_cbcs_hd.page-config.hjson` | CENC v3 `cbcs` (AES-CBC) | 8-bit H.264 Main/High (MP4 + AAC, 30fps) | HD-only ABR (2 tiers: 720p, 1080p) |
| `h264_cenc_adaptive` | `h264_cenc_adaptive.page-config.hjson` | CENC `cenc` (AES-CTR) | 8-bit H.264 Base/Main/High (MP4 + AAC, 30fps) | Adaptive ABR (4 tiers: 240p to 1080p) |
| `h264_cenc_hd` | `h264_cenc_hd.page-config.hjson` | CENC `cenc` (AES-CTR) | 8-bit H.264 Main/High (MP4 + AAC, 30fps) | HD-only ABR (2 tiers: 720p, 1080p) |
| `hevc_cbcs_adaptive` | `hevc_cbcs_adaptive.page-config.hjson` | CENC v3 `cbcs` (AES-CBC) | 8-bit HEVC Main (MP4 + AAC, 30fps) | Adaptive ABR (6 tiers: 240p to 4K UHD) |
| `hevc_cbcs_hd` | `hevc_cbcs_hd.page-config.hjson` | CENC v3 `cbcs` (AES-CBC) | 8-bit HEVC Main (MP4 + AAC, 30fps) | HD-only ABR (2 tiers: 720p, 1080p) |
| `hevc_cenc_adaptive` | `hevc_cenc_adaptive.page-config.hjson` | CENC `cenc` (AES-CTR) | 8-bit HEVC Main (MP4 + AAC, 30fps) | Adaptive ABR (6 tiers: 240p to 4K UHD) |
| `hevc_cenc_hd` | `hevc_cenc_hd.page-config.hjson` | CENC `cenc` (AES-CTR) | 8-bit HEVC Main (MP4 + AAC, 30fps) | HD-only ABR (2 tiers: 720p, 1080p) |
| `vp9_cenc_adaptive` | `vp9_cenc_adaptive.page-config.hjson` | CENC `cenc` (WebM subsample CTR) | 8-bit VP9 + Opus (WebM, ~30fps) | Adaptive ABR (4 tiers: 240p to 1080p) |

## Workflow
- **Prerequisites & Setup**:
  - Target device must be provisioned with a **Widevine L1 hardware-secure CDM** supporting hardware-backed decryption and decoding for the tested codec/scheme.
  - Requires live network access to `storage.googleapis.com` (hosting the Shaka Player test page and Widevine encrypted DASH streams) and `proxy.uat.widevine.com` (Widevine UAT license proxy); no Google account login or Web Page Replay (WPR) archive is used.
- **Main Actions**:
  1. Open `chrome://media-internals` and verify that a `Hardware Secure` Widevine L1 CDM is registered.
  2. Load the hosted Shaka Player DRM harness, acquire a Widevine L1 license (`HW_SECURE_ALL` video robustness), start encrypted playback, and let playback stabilize briefly.
  3. Execute 10 deterministic seeded pseudo-random seeks across the stream duration, awaiting seek completion on each step while recording User Timing seek duration marks, and assert that all 10 seeks completed.
  4. Re-check `chrome://media-internals` to confirm `Hardware Secure` CDM status persisted after seeking.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Widevine L1 Hardware Security**: Preserve `HW_SECURE_ALL` video robustness against the Widevine UAT license flow and both pre- and post-seek `Hardware Secure` CDM assertions on `chrome://media-internals`; never downgrade to software DRM or bypass L1 verification.
- **Variant Codec, Encryption & Manifest Mode**: Keep each variant pointed at an encrypted stream matching its designated encryption scheme (`cenc` vs. `cbcs`), codec (`av1`, `h264`, `hevc`, `vp9`), and DASH manifest mode (`adaptive` multi-tier ABR vs. `hd` 720p/1080p-only vs. `static` single-representation).
- **100% Seek Completion & Deterministic Seek Telemetry**: Preserve the deterministic seeded 10-seek sequence, the post-loop assertion verifying 100% seek completion, and the `test-config` (`numTargetSeeks`) and `randomSeek-*-duration` User Timing marks that back `cuj.video-seek.avg_seek_time_s` and `cuj.video-seek.seek_completion_percentage`.

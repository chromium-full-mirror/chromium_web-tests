# `video-drm` CUJ

## Overview
The `video-drm` CUJ validates and benchmarks end-to-end Widevine L1 hardware-secure (`HW_SECURE_ALL`) encrypted DASH video playback in Shaka Player using Encrypted Media Extensions (EME). It verifies that a hardware-backed Content Decryption Module (CDM) is active before and after playback while exercising encrypted stream decoding across CENC v1 and v3, AES-CTR (`cenc`) and AES-CBC (`cbcs`) schemes, and H.264, HEVC, VP9, and AV1 codecs.

## Variants
Variants span four media axes:
- **CENC Version & Encryption Scheme**: CENC v1 (`cenc` AES-CTR) and CENC v3 (`cenc` AES-CTR / WebM subsample CTR, `cbcs` AES-CBC pattern encryption, and a two-period `cbcs`-to-`cenc` mid-stream scheme transition).
- **Codec, Bit Depth & Slice Structure**: H.264 Main (8-bit, single-slice and multi-slice NAL layouts), HEVC Main (8-bit) and Main 10 (10-bit), VP9 Profile 0 (8-bit) and Profile 2 (10-bit), and AV1 Main (8-bit and 10-bit).
- **Resolution & Stream Mode**: Single-representation static 480p streams (with one 4K UHD HEVC 10-bit variant and one two-period 480p encryption-transition variant).

| Variant | Config File | CENC & Encryption Scheme | Codec, Bit Depth & Container | Resolution & Stream Mode |
| :--- | :--- | :--- | :--- | :--- |
| `cencv1_h264_ctr` | `cencv1_h264_ctr.page-config.hjson` | CENC v1, `cenc` (AES-CTR) | 8-bit H.264 Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv1_h264_multislice_ctr` | `cencv1_h264_multislice_ctr.page-config.hjson` | CENC v1, `cenc` (AES-CTR) | 8-bit multi-slice H.264 Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_av1_10bit_cbc` | `cencv3_av1_10bit_cbc.page-config.hjson` | CENC v3, `cbcs` (AES-CBC) | 10-bit AV1 Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_av1_10bit_ctr` | `cencv3_av1_10bit_ctr.page-config.hjson` | CENC v3, `cenc` (WebM subsample CTR) | 10-bit AV1 Main (WebM + AAC) | 480p (854x480), static single-period |
| `cencv3_av1_cbc` | `cencv3_av1_cbc.page-config.hjson` | CENC v3, `cbcs` (WebM CBC) | 8-bit AV1 Main (WebM + AAC) | 480p (854x480), static single-period |
| `cencv3_av1_ctr` | `cencv3_av1_ctr.page-config.hjson` | CENC v3, `cenc` (WebM subsample CTR) | 8-bit AV1 Main (WebM + AAC) | 480p (854x480), static single-period |
| `cencv3_h264_cbc` | `cencv3_h264_cbc.page-config.hjson` | CENC v3, `cbcs` (AES-CBC) | 8-bit H.264 Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_h264_cbc_then_ctr` | `cencv3_h264_cbc_then_ctr.page-config.hjson` | CENC v3, `cbcs` -> `cenc` transition | 8-bit H.264 Main (MP4 + AAC) | 480p (854x480), two-period static (`cbcs` then `cenc`) |
| `cencv3_h264_ctr` | `cencv3_h264_ctr.page-config.hjson` | CENC v3, `cenc` (AES-CTR) | 8-bit H.264 Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_hevc10_4k_ctr` | `cencv3_hevc10_4k_ctr.page-config.hjson` | CENC v3, `cenc` (AES-CTR) | 10-bit HEVC Main 10 (MP4 + AAC) | 4K UHD (3840x2160), static single-period |
| `cencv3_hevc10_cbc` | `cencv3_hevc10_cbc.page-config.hjson` | CENC v3, `cbcs` (AES-CBC) | 10-bit HEVC Main 10 (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_hevc10_ctr` | `cencv3_hevc10_ctr.page-config.hjson` | CENC v3, `cenc` (AES-CTR) | 10-bit HEVC Main 10 (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_hevc_cbc` | `cencv3_hevc_cbc.page-config.hjson` | CENC v3, `cbcs` (AES-CBC) | 8-bit HEVC Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_hevc_ctr` | `cencv3_hevc_ctr.page-config.hjson` | CENC v3, `cenc` (AES-CTR) | 8-bit HEVC Main (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_vp92_ctr` | `cencv3_vp92_ctr.page-config.hjson` | CENC v3, `cenc` (AES-CTR) | 10-bit VP9 Profile 2 (MP4 + AAC) | 480p (854x480), static single-period |
| `cencv3_vp9_ctr` | `cencv3_vp9_ctr.page-config.hjson` | CENC v3, `cenc` (AES-CTR) | 8-bit VP9 Profile 0 (MP4 + AAC) | 480p (854x480), static single-period |

## Workflow
- **Prerequisites & Setup**:
  - Target device must be provisioned with a **Widevine L1 hardware-secure CDM** supporting hardware-backed decryption and decoding for the tested codec/scheme.
  - Requires live network access to `storage.googleapis.com` (hosting the Shaka Player test page and encrypted DASH media) and `proxy.uat.widevine.com` (Widevine UAT license proxy); no Google account login or Web Page Replay (WPR) archive is used.
- **Main Actions**:
  1. Open `chrome://media-internals` and verify that a `Hardware Secure` Widevine L1 CDM is registered.
  2. Load the hosted Shaka Player DRM harness, acquire a Widevine L1 license (`HW_SECURE_ALL` video robustness), and play the variant's encrypted DASH stream through to natural completion while recording system and graphics smoothness telemetry.
  3. Re-check `chrome://media-internals` to confirm `Hardware Secure` CDM status persisted after playback.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Widevine L1 Hardware Security**: Preserve `HW_SECURE_ALL` video robustness against the Widevine UAT license flow and both pre- and post-playback `Hardware Secure` CDM assertions on `chrome://media-internals`; never downgrade to software DRM or bypass L1 verification.
- **Variant Codec & Encryption Coverage**: Keep each variant pointed at an encrypted stream matching its designated CENC version (`v1` vs. `v3`), encryption scheme (`cenc`, `cbcs`, or two-period `cbcs`-to-`cenc` transition), codec/profile, bit depth, slice structure, and resolution.
- **Full Playback Completion**: Every variant—including the longer two-period `cencv3_h264_cbc_then_ctr` transition stream—must play uninterrupted from playback start through the media ended event without Shaka Player or media element errors.

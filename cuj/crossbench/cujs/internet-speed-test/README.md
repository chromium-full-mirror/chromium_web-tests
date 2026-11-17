# `internet-speed-test` CUJ

## Overview
Benchmarks Chrome's HTTP `fetch()` network stack download throughput, upload throughput, and request-to-headers latency against live Cloudflare speed-test endpoints (`speed.cloudflare.com`). It runs an in-page JavaScript speed test directly in the initial tab and reports averaged download/upload rates (Mbps) and latency (ms) via a User-Timing mark.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Executes a single pass of 10 uncached 1 MB downloads followed by 10 uncached 1 MiB random-payload uploads against `https://speed.cloudflare.com`. |

## Workflow
- **Prerequisites & Setup**: Requires live outbound internet access to `https://speed.cloudflare.com` (CORS-enabled; no login, WPR archive, local server, or explicit page navigation).
- **Main Actions**: Runs a single JavaScript workload in the initial tab that:
  1. Performs 10 sequential uncached `GET` downloads of 1 MB, measuring response-header latency (ms) and payload download throughput (Mbps).
  2. Generates a 1 MiB cryptographically random payload and performs 10 sequential uncached `POST` uploads, measuring upload throughput (Mbps).
  3. Emits a `speed-test-result` User-Timing mark containing the averaged `{ download, upload, latency }` results.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Preserve the `speed-test-result` User-Timing contract**: Custom CUJ metrics (`cuj.internet-speed-test.download`, `upload`, `latency`) extract `download`, `upload`, and `latency` directly from the `speed-test-result` `performance.mark` detail object—never rename the mark or alter its detail keys or units (Mbps and ms).
- **Uncached, incompressible methodology**: Keep `cache: 'no-store'`, 10 sequential iterations per direction, and cryptographically random upload bytes (so transport compression cannot artificially inflate upload throughput).
- **Live network execution**: Never replay this CUJ against a WPR archive, which would benchmark local proxy loopback rather than real network throughput and latency.

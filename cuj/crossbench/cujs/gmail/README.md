# `gmail` CUJ

## Overview
Benchmarks core Gmail web client responsiveness: loading the inbox, opening a new email compose dialog, typing a subject line and message body, and discarding the draft. Captures compose-dialog creation User Timing alongside native touch and keyboard input latency.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Standard Gmail inbox load, compose dialog creation, subject/body typing, and draft discard workflow. |

## Workflow
- **Prerequisites & Setup**: Requires logging into a Google test account with Gmail enabled.
- **Main Actions**: Loads the Gmail inbox, dismisses optional mobile or desktop notification banners if they appear, opens a new Compose dialog, types sample text into both the Subject field and Message Body via native keyboard input, briefly pauses to allow draft auto-save activity to settle, and clicks Discard draft.
- **Teardown**: Each iteration discards the composed draft inline and verifies the compose editor has closed so no unsent drafts remain open.

## Metrics & Invariants (Preserve When Healing)
- **Compose-dialog User Timing marks**: Preserve `compose-dialog-open`, `compose-dialog-loaded`, and the `compose-dialog-ready` measure tightly bracketing the Compose button click and the compose dialog becoming visible.
- **Mandatory draft cleanup**: Always discard the draft and verify the compose body disappears before ending the iteration; Gmail persists open drafts across reloads and playback loops, which otherwise leaves multiple subject/body fields in the DOM and breaks subsequent selector targeting.
- **Native input and optional banner resilience**: Preserve native touch clicks and native keyboard typing (never JavaScript-injected input) so `EventLatency` histograms stay accurate, and keep notification-banner dismissals optional so runs succeed whether or not prompts appear.

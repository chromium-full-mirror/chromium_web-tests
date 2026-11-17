# `drive-cleanup` CUJ

## Overview
Benchmarks Google One Storage Manager's batch deletion workflow while permanently purging up to 32 large Google Drive files and up to 32 trashed Google Drive files. Beyond measuring touch interaction responsiveness and SPA transitions on Google One, this CUJ provides automated storage hygiene so shared test accounts do not run out of Drive quota.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Standard Google One Storage Manager permanent cleanup of large Drive files and trashed Drive files. |

## Workflow
- **Prerequisites & Setup**: Requires logging into a dedicated Google test account whose personal Drive storage only holds disposable test artifacts—this workflow **permanently and irrecoverably deletes** files. Canonical Workspace templates used by other CUJs must live in protected Shared Drives or separate owner accounts so they cannot be purged here.
- **Main Actions**: Opens Google One Storage Manager, navigates to the Large Drive Files view, selects the displayed batch of items (up to 32), opens the deletion modal, checks the irreversible-deletion acknowledgment box, confirms permanent deletion, and navigates back to the Storage Manager overview; then navigates to the Drive Trash view and repeats the same select-all and permanent-deletion sequence.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Permanent-deletion blast-radius safety**: Never broaden navigation targets beyond Google One's Drive Large Files and Drive Trash views, never target Shared Drives containing canonical CUJ templates, and never run against non-dedicated user accounts.
- **Graceful empty-state handling**: All selection, deletion, and modal-close steps are intentionally optional so the CUJ completes cleanly even when Large Files or Trash currently contains zero items (or when the confirmation dialog closes automatically); preserve this empty-list resilience while keeping post-click verifications intact when items exist.
- **Transition-overlay synchronization and native touch input**: Wait for Google One's transition overlay layers (`trans-layer`) to clear after page navigation before clicking list controls, and preserve native touch clicks for `EventLatency` tracking.

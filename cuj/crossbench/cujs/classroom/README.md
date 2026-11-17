# `classroom` CUJ

## Overview
Benchmarks an end-to-end Google Classroom student workflow: opening a course stream, navigating into an assignment, previewing an attached Google Drive file, popping that preview out into a full Google Drive tab, and downloading a compressed archive attachment. Measures touch interaction responsiveness, download initiation User Timing, and browser/system trace metrics across cross-app navigation.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Standard Google Classroom assignment navigation, Drive attachment pop-out, and `.gz` file download workflow. |

## Workflow
- **Prerequisites & Setup**: Requires a Google test account login with access to the target Google Classroom course (either already enrolled or able to self-enroll via the course invite link) and permission to view and download the course's Google Drive attachment.
- **Main Actions**: Opens the Classroom course page, dismisses first-run class enrollment or onboarding prompts if shown, opens the first assignment, selects its first attachment to open the embedded Drive preview, uses the preview's "Open in new tab" menu option to launch Google Drive in a new tab, switches to that Drive tab, clicks Download, and waits until the `.gz` archive download completes.
- **Teardown**: None.

## Metrics & Invariants (Preserve When Healing)
- **Native touch input**: Preserve native touch clicks across interactive steps rather than JavaScript-triggered clicks so browser `EventLatency` touch metrics remain valid.
- **Idempotent onboarding tolerance**: Keep class-join and onboarding tooltip dismissals optional so the test succeeds regardless of whether the account has previously joined the course or dismissed promos.
- **Active SPA view scoping**: Google Classroom keeps prior route views hidden in the DOM (`aria-hidden="true"`); ensure assignment and attachment queries stay scoped to the active, visible view rather than matching stale hidden views.
- **Iframe-to-tab handoff**: The Classroom attachment preview renders inside an embedded Google Drive iframe; preserve switching WebDriver context into that iframe to trigger "Open in new tab" and then switching browser tabs to the newly opened Drive tab.
- **Download timing and completion**: Preserve the pre-click User Timing instrumentation (`download-click-start`, `download-click-end`, and `download-click-duration`) immediately before clicking Download, and keep waiting for the `.gz` file download to finish.

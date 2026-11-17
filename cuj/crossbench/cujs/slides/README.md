# `slides` CUJ

## Overview
Benchmarks interactive Google Slides workflows on a 50-slide presentation deck: scrolling the left filmstrip, selecting slide text to post a comment, and appending, editing, and deleting a slide at the end of the deck. Measures filmstrip scroll distance and duration, comment-box open latency (`default`), slide/text editing User Timing marks (`new-slide`), and native touch/keyboard input latency.

## Variants
| Variant | Config File | Key Differences |
| :--- | :--- | :--- |
| `default` | `page-config.hjson` | Scrolls the filmstrip, navigates to slide 25, selects an existing word on the slide canvas, and inserts/posts a comment. |
| `new-slide` | `new-slide.page-config.hjson` | Scrolls the filmstrip all the way to slide 50, inserts a new slide 51, adds a text box and types onto the canvas, then deletes slide 51. |

## Workflow
- **Prerequisites & Setup**: Requires Google test account login plus `google_workspace` service-account and Shared Drive credentials in the secrets config so the `google_workspace` probe can clone the canonical 50-slide presentation via the Google Drive API before each run.
- **Main Actions**: Both variants first clone the 50-slide template into the Shared Drive, open the disposable copy, and touch-scroll the left filmstrip. The `default` variant then selects slide 25, clicks a target word on the slide canvas, dismisses any optional promotional dialog, and opens the Insert menu to type and post a comment. The `new-slide` variant instead scrolls the lazy-loaded filmstrip down until slide 50 is materialized, clicks New Slide to create slide 51, inserts a text box on the canvas and types into it, and deletes slide 51 via the Edit menu.
- **Teardown**: In `new-slide`, deleting slide 51 inline restores the deck to 50 slides so playback loops remain repeatable; across both variants, cloned Shared Drive presentations carry a 4-hour TTL metadata property for external cleanup.

## Metrics & Invariants (Preserve When Healing)
- **Never mutate the canonical template presentation**: Always preserve the `google_workspace` probe's copy-and-redirect step so neither posted comments nor mid-run failures before slide deletion alter the canonical 50-slide deck.
- **SVG rendering and single-word text selection**: Google Slides renders both filmstrip thumbnails and slide canvas text as SVG elements (requiring SVG-aware `local-name()` queries if using XPath). In `default`, keep the selected slide text (`testSlide25` on slide 25) as a single contiguous word because Slides splits multi-word phrases across separate SVG `<text>` nodes.
- **Lazy-loaded filmstrip and 50-slide count (`new-slide`)**: Slides lazy-loads off-screen filmstrip thumbnails, so preserve programmatic filmstrip scrolling to materialize slide 50 before clicking it, and ensure the final delete step verifies the presentation returns to `'50 total slides'`.
- **User Timing and `MutationObserver` hooks**: Preserve filmstrip scroll marks (`scroll-begin`, `scroll-end` with `scrollTop` detail, and `scroll`), `default` variant text-selection and comment observers/marks (`text-click`, `text-being-selected`, `comment-click`, `comment-opened`, `comment-type`), and `new-slide` timing marks (`filmstrip-scroll-start`/`end`/`duration`, `new-slide-created`, `type-text`, `new-slide-deleted`).
- **Native input and exact menu targeting**: Preserve native touch clicks, native keyboard typing, optional promotional-popup dismissal, and exact Workspace menu item labels rather than prefix wildcards (e.g., avoid `[aria-label^='Comment']`).

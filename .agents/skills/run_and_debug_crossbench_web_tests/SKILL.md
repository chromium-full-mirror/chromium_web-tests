---
name: run-and-debug-crossbench-web-tests
description: >-
  Execute, debug, and analyze loading benchmarks and
  Critical User Journeys (CUJs) implemented with Crossbench.
  Use this skill when running web-tests, debugging selectors,
  or analyzing test failures on Android (ADB), ChromeOS, or local.
---

# Running and Debugging Crossbench Web Tests

This skill provides comprehensive instructions for executing, debugging, and analyzing Crossbench-based web-tests (Critical User Journeys and loading benchmarks) in this repository.

---

## Running Web Tests

Always run tests using the repository's pre-configured **`vpython3`** environment. Do **not** source python virtualenvs or run poetry manually unless explicitly requested. Sourcing `vpython3` handles all dependency resolution natively and matches Google developer infrastructure.

### Command Invocation

Before running any test on Android/ADB (especially after a crash or cancellation), always clear the browser's state completely to ensure a 100% fresh, clean out-of-the-box startup:
```bash
adb shell 'for u in $(pm list users | grep -o "{[0-9]*:" | tr -d "{:"); do am force-stop --user $u com.android.chrome; pm clear --user $u com.android.chrome; done' && \
adb shell rm -f /data/local/tmp/chrome-command-line && \
adb shell rm -rf /data/local/tmp/chrome_user_data
```

Then, run tests from the runner directory:
```bash
cd cuj/crossbench/runner
vpython3 run.py --platform adb --tests <test_pattern> --variants <variant_pattern> --secrets ~/secrets.hjson
```

### Common Arguments

| Argument | Description |
| :--- | :--- |
| `--platform` | Target execution environment: `adb` (Android), `cros` (ChromeOS), `local` (Desktop). |
| `--tests` | Python regex matching the test/cuj name (e.g., `heavy-meet-note`, `speedometer.*`). |
| `--variants` | Python regex matching variant page-configs (e.g., `4p`, `9p-background-blur`). |
| `--secrets` | Path to local secrets HJSON file containing testing account credentials (`~/secrets.hjson`). |

---

## Directory Structure

- **CUJ Definitions:** `cuj/crossbench/cujs/<cuj_name>/`
- **Variant Page-Configs:** `cuj/crossbench/cujs/<cuj_name>/<variant_name>.page-config.hjson`
- **Core Action Blocks:** `cuj/crossbench/cujs/<cuj_name>/action-blocks/<cuj_name>.hjson`
- **Test Executable Runner:** `cuj/crossbench/runner/run.py`

---

## Debugging & Troubleshooting Failures

When a test run fails, ChromeDriver generates diagnostic files in the results directory. Use these steps to systematically analyze and debug failures.

### Step 1: Locate the Diagnostic Output

Crossbench outputs results under:
`cuj/crossbench/runner/results/`

To find the latest failure folder:
1. Navigate to the results directory.
2. Locate the directory corresponding to the failure timestamp (e.g. `2026-05-12_100253`).
3. Diagnostic screenshots and HTML are located inside:
   `results/<timestamp>/<test_variant>/fail/<timestamp>/chrome_v<version>_chrome/stories/<story_name>/0/0_default/`

### Step 2: Inspect the Failure Screenshot

View the `playback_0_failure.png` screenshot inside the story run's `screenshot/` subdirectory using the `view_file` tool.
* **Goal:** Confirm the visual state of the browser (e.g., is the correct tab focused? Is the target dropdown menu actually opened?).

### Step 3: Analyze the HTML DOM Dump

If a click or element wait timed out, the browser's complete minified DOM structure is dumped to `dump_html/playback_0_failure.html`.

Because these dumps are extremely large minified single-line files (often 1.5MB+), standard `grep_search` can fail or truncate results. **Always use python one-liners** to target and extract exact context chunks:

```bash
# Extract 500 characters of DOM context around a specific ID
python3 -c "
with open('path/to/playback_0_failure.html') as f:
    content = f.read()
idx = content.find('docs-insert-menu')
if idx != -1:
    print(content[idx-200:idx+500])
"
```

```bash
# Find all matching elements with class goog-menuitem or role menuitem
python3 -c "
import re
with open('path/to/playback_0_failure.html') as f:
    content = f.read()
matches = [m.start() for m in re.finditer('goog-menuitem|menuitem', content, re.IGNORECASE)]
for idx in matches:
    chunk = content[max(0, idx-100):idx+300]
    if 'Comment' in chunk or 'comment' in chunk:
        print(chunk)
"
```

---

## CSS/XPath Selector Guidelines

Web Workspace apps (Docs, Slides, Sheets) are highly dynamic, single-page applications. Follow these rules when authoring HJSON action blocks:

1. **Strict Click Actions:** Never use custom Javascript `JsAction` to trigger clicks (unless absolutely instructed). Rely exclusively on native `click` actions with `scroll_into_view: true`.
2. **Avoid Wildcard Selector Traps:** Wildcard attribute selectors like starts-with `^=` (e.g., `[aria-label^='Comment']`) are risky. In Google Workspace, this can match multiple elements (e.g. both the `Comment` insertion menu item and the `Comments` submenu). If it matches multiple elements, Chromedriver will always pick the first matching element in document order (which might belong to a closed menu), causing the click to fail.
3. **Exact Matching:** Always prefer exact attribute selectors (e.g. `[aria-label='Comment m']`) to uniquely isolate the element.
4. **Comma-Separated Selectors List:** If the exact location of an attribute (like `aria-label` on the `[role='menuitem']` element vs. on a nested span) varies by locale or platform, use a comma-separated CSS selector list:
   ```hjson
   selector: "[role='menuitem'][aria-label='Comment m'], [role='menuitem'] [aria-label='Comment m']"
   ```
5. **Account for Viewport Limits:** On mobile/tablet viewport screens, vertical absolute menus (like `Insert` or `File` dropdowns) will display scrollbars, cutting off lower options. Calling native `click` with `scroll_into_view: true` on the exact menu item is highly robust, as the browser's native layout engine will automatically scroll the menu container to reveal and click the element. Always add a short rendering delay (e.g. `wait: 1s`) after opening a menu to let items fully populate in the DOM.

---

## Crossbench HJSON Action Types & Parameters

When authoring or debugging HJSON action blocks in Crossbench, the following action types, parameters, and options are supported by the underlying action parsers (`third_party/crossbench/action_runner/action/`).

> [!IMPORTANT]
> **Native Input Injection Rule:** You must **always** use a `mouse` or `touch` input source for interactive actions (`click`, `scroll`, `swipe`, `text_input`) unless explicitly instructed to use `js`. All input events must be injected natively through the OS or webdriver rather than simulated via JavaScript.

### 1. Click (`action: "click"`)
* `source`: Input source. Options: `"mouse"`, `"touch"`, `"js"`, `"keyboard"`. **Always use `"mouse"` or `"touch"`** unless explicitly told to use `"js"`.
* `pos` (aliases: `position`, `selector`): (Required) Target location or element. Must specify exactly ONE of:
  * `selector`: DOM selector string (prefix with `xpath/` for XPath) OR object `{ selector: "#id", required: true, scroll_into_view: true, wait: true }`.
  * `coordinates`: Exact screen coordinates object `{ x: 100, y: 200 }`.
  * `ui_selector`: Android BySelector object `{ res: "...", clazz: "...", text: "..." }`.
* `duration`: Duration of the click press (e.g., `"100ms"`). Default: `0s`.
* `attempts`: Positive integer for number of click attempts. Default: `1`.
* `verify`: CSS/XPath selector string to verify after clicking (waits for element to appear).
* `timeout`: Maximum time to wait for the action/element. Default: `"20s"`.
* `index`: Integer index of the action. Default: `0`.

### 2. Text Input (`action: "text_input"`)
* `source`: Input source. Options: `"keyboard"` (native OS/webdriver keystrokes), `"js"`. **Always use `"keyboard"`** unless explicitly told to use `"js"`.
* `text`: String text to type. (Must specify exactly one of `text` or `keyevent`).
* `keyevent`: Android KeyEvent code name (e.g., `"KEYCODE_ENTER"`).
* `duration`: Total duration over which to type the text (pacing keystrokes). Default: `0s`.
* `timeout`: Maximum time to wait for the action. Default: `"20s"`.

### 3. Scroll (`action: "scroll"`)
* `source`: Input source. Options: `"touch"`, `"js"`. **Always use `"touch"`** (or mouse fallback) unless explicitly told to use `"js"`.
* `distance`: Float distance to scroll in pixels. Default: `500`.
* `duration`: Duration over which to scroll (e.g., `"1s"`). Default: `1s`.
* `selector`: Optional CSS/XPath selector of the container element to scroll.
* `required`: Boolean (default: `false`). If true, fails if the `selector` container is not found.
* `timeout`: Maximum time to wait for the action. Default: `"20s"`.

### 4. Swipe (`action: "swipe"`)
* `start_x` / `start_y` (aliases: `startx`, `starty`): (Required) Starting X/Y screen coordinates.
* `end_x` / `end_y` (aliases: `endx`, `endy`): (Required) Ending X/Y screen coordinates.
* `duration`: Duration of the swipe (e.g., `"1s"`). Default: `1s`.
* `timeout`: Maximum time to wait for the action. Default: `"20s"`.

### 5. Navigation & Tabs (`action: "get" | "switch_tab" | "close_tab" | "close_all_tabs"`)
* **Get** (`action: "get"`):
  * `url`: (Required) Target URL string.
  * `duration`: Initial wait duration. Default: `0s`.
  * `ready_state`: Target ReadyState (`"any"`, `"interactive"`, `"complete"`). Default: `"any"`.
  * `target`: Window target (`"_self"`, `"_blank"`). Default: `"_self"`.
* **Switch Tab** (`action: "switch_tab"`) / **Close Tab** (`action: "close_tab"`):
  * Must specify exactly one of: `tab_index` (absolute integer), `relative_tab_index` (relative integer offset), `title` (tab title string), or `url` (tab URL string).
* **Close All Tabs** (`action: "close_all_tabs"`): Closes all open tabs/windows.

### 6. Waits & Verification (`action: "wait" | "wait_for_element" | "wait_for_condition" | "wait_for_ready_state" | "wait_for_download"`)
* **Wait** (`action: "wait"`): `duration` (Required, e.g., `"5s"`).
* **Wait For Element** (`action: "wait_for_element"`):
  * `selector`: (Required) CSS/XPath selector string.
  * `expected_count`: Integer count of elements. Default: `1`.
  * `or_more`: Boolean (default: `false`). Matches `expected_count` or more.
  * `check_rect`: Boolean (default: `false`).
* **Wait For Condition** (`action: "wait_for_condition"`): `condition` (Required JS script string containing `return`).
* **Wait For Ready State** (`action: "wait_for_ready_state"`): `ready_state` (`"any"`, `"interactive"`, `"complete"`). Default: `"complete"`.
* **Wait For Download** (`action: "wait_for_download"`): `pattern` (Required regex string matching downloaded filename).

### 7. Execution & Probes (`action: "js" | "open_devtools" | "inject_new_document_script" | "probe"`)
* **JS** (`action: "js"`): Must specify exactly one of `script` (JS string) or `script_path` (alias `path`, path to JS file). Optional `replacements` (alias `replace`, dict of string replacements).
* **Open DevTools** (`action: "open_devtools"`): `panel_name` (Required string, e.g., `"console"`).
* **Inject Script** (`action: "inject_new_document_script"`): `script` (Required JS string injected on every new document).
* **Probe** (`action: "probe"`): `probe` (Required probe name string, e.g., `"dump_heap"`), optional `kwargs` dict.

---

## Crossbench HJSON Config & Template Schema Guidelines

Follow these rules to implement robust, repeatable loading benchmarks that support the `--playback` repetition loop argument without compiler exceptions:

### 1. Setup/Actions/Teardown Execution Model
To partition execution into setup, loops, and teardown:
* **`setup: [ ... ]`**: A list of action objects executed exactly **once** at the very start of the test run.
* **`actions: [ ... ]` (alias `blocks`)**: A list of action objects executed **multiple times** (looping) based on the `--playback` CLI parameter (e.g., `2x`, `5x`).
* **`teardown: [ ... ]`**: A list of action objects executed exactly **once** at the very end of the entire story run (after all loops conclude).

### 2. Nested Template Block Arguments
When importing an ActionBlock template (like `create-and-join-meeting.hjson`) nested inside `setup` or `teardown`:
* **No `args` in template root:** The resolved template must parse into a clean `ActionBlock` containing **only the `actions` key** (and optional `label`/`index`). If the template has a root `args: { ... }` block, the compiler will preserve it in the resolved state and crash (as compiled ActionBlocks do not support args).
* **Unbound Argument propagation:** Keep all custom parameters (such as `MEET_TARGET` or `BACKGROUND_BLUR`) as clean **unbound variables** in the template HJSON, and let them propagate up to the caller's `unbound_args` and the outermost page-config `args` block to be resolved safely:
  ```hjson
  // Inside outer page-config args block (e.g. heavy-meet-note.hjson):
  args: {
    MEET_TARGET: _new_window
  }
  ```
  ```hjson
  // Inside the template block import inside the page:
  Start-New-Meeting: {
    template: ../../../common-action-blocks/meet/create-and-join-meeting.hjson
    args: {
      TTL_SECS: 300
    }
    unbound_args: [
      NUM_BOTS
      MEET_TARGET
    ]
  }
  ```

### 3. Template Invocations Without Arguments
When importing a template in a page config (e.g., inside `pages: { my-page: { template: ./action-blocks/my-page.hjson } }`), if the template does not require any `args` or `unbound_args`, the Crossbench parser (`_TemplatedConfigParser`) will fail to recognize it as a template invocation unless an empty `args: {}` block is explicitly provided. If `args: {}` is omitted, the parser treats `template` as an unused property and crashes with `GetAction.url is missing`. Always include `args: {}` when invoking parameterless templates.

### 4. Real-User Performance & Browser Flags
To ensure Crossbench loading benchmarks and CUJs match real-user browser performance characteristics as closely as possible:
* **Background Throttling:** Always ensure `--allow-background-interventions` is included in the browser flags (e.g. `common-flags.hjson`). This allows Chrome to throttle background tabs and discard memory exactly like a real user's browser.
* **Finch Experiments:** Include `--enable-field-trial-config` in the browser flags to ensure tests execute with active production A/B experiment code paths rather than unoptimized baseline paths.
* **ChromeDriver Defaults:** By default, ChromeDriver injects several switches that alter performance (`--disable-background-timer-throttling`, `--disable-dev-shm-usage`, `--disable-backgrounding-occluded-windows`). Crossbench's `ChromiumBasedWebDriver` is pre-configured to exclude these switches via `excludeSwitches` to maintain real-user background throttling and fast RAM-backed IPC (`/dev/shm`).

### 5. Android Viewport Maximization
When running tests on Android Desktop / ARC (e.g., ChromeOS freeform floating window mode) with `--viewport=maximized`, Crossbench dynamically calculates the usable desktop work area between the top status bar and bottom taskbar (`dumpsys window displays`), and resizes the freeform task via `am task resize` to fill the screen perfectly while preserving freeform window controls.


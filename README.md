# `web-tests`

`web-tests` contains:
- Definitions for CUJs implemented using crossbench's loading benchmark
- Configuration files for running benchmarks that are built in to crossbench (such as speedometer)
- Metric definitions and queries for CUJs and benchmarks.

# Setup

Install `golang` (required for WPR and presubmit upload checks)

```
sudo apt-get install golang
```

### Google Cloud SDK
You need to have `gcloud storage` installed and authenticated to download WPR archives used in benchmarks.

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
2. Authenticate your account:
```bash
gcloud auth login
```


**Do not `git clone` web-tests**. Use the `fetch` command included with `depot_tools`.

- Install [Chromium depot_tools](https://commondatastorage.googleapis.com/chrome-infra-docs/flat/depot_tools/docs/html/depot_tools_tutorial.html#_setting_up).
- Get the web-tests code with all dependencies:
```
mkdir src
cd src
gcloud auth login
fetch web-tests
cd web-tests
```
Don't forget to run `gclient sync` every time you pull new changes from origin.

## Running Tests

Python dependencies are managed automatically using `vpython3` (included with `depot_tools`).

### Android
Before running a test against an android target, make sure your device is connected through `adb`:
```
adb devices
> List of devices attached
> 192.168.20.194:5555     device
```

Replace `<DEVICE ID>` below with the actual device ID from `adb devices`:
```bash
cd cuj/crossbench/runner
vpython3 run.py --platform adb --device <DEVICE ID>
```

### ChromeOS
Before running a test against a ChromeOS target, make sure passwordless SSH is available to the device. Either an IP address or a SSH host is supported as the device id.

Replace `<DEVICE>` below with the IP address or hostname of your device:
```bash
cd cuj/crossbench/runner
vpython3 run.py --platform cros --device <DEVICE>
```

### Local
*Running against a local browser on linux is minimally supported, but may require manual changes to test configuration.*

```bash
cd cuj/crossbench/runner
vpython3 run.py --platform local
```

### Specifying Tests and Variants
The minimal invocation of the runner will attempt to run all benchmarks, CUJs, and corresponding variants in series.

To run a subset of tests, use the `--tests` flag. `--tests` supports Python regex format for matching the test names.
```bash
vpython3 run.py --platform adb --device <DEVICE ID> --tests speedometer.*
```

To specify only certain variants of a test, you can use the `--variants` flag. `--variants` also supports Python regex format for matching variants.
```bash
vpython3 run.py --platform adb --device <DEVICE ID> --tests local-conference --variants 16p
```

### Specifying Browsers
By default the runner will use 'Chrome' if the `--browser` flag is not specified. The format accepted by the `--browser` flag depends on the platform. For Android, use the package name of the installed browser. For ChromeOS or local, use the path to the browser executable.

### Secrets
Some CUJs require secrets to perform privileged actions (such as a test account username/password, or auth tokens for the Google Meet Bond API). Place your secrets in `secrets.hjson` and pass the file to the runner:

```bash
vpython3 run.py --platform adb --device <DEVICE ID> --secrets /home/me/secrets.hjson --tests docs
```

### Looping Tests
Tests can be repeated for a number of iterations or for a specified amount of time using the `--playback` flag. This flag is supported by crossbench and will iterate the post-setup sections of a CUJ and collect metrics for the entire invocation (instead of splitting metrics by iteration).

```bash
vpython3 run.py --platform adb --device <DEVICE ID> --tests tab-stress --variants blank-tab --playback 50x
```

```bash
vpython3 run.py --platform adb --device <DEVICE ID> --tests tab-stress --variants blank-tab --playback 2h
```

# Contributing

To get started contributing to web-tests, refer to the [docs](./docs/).
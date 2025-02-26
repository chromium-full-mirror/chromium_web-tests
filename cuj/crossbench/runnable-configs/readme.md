# Runnable Configs

This folder defines how all tests and variants are run.

Tests are defined by subfolders with the following contents:
* Page Configs
* Probe Configs
* Args

Described below.

## Page Configs

One page configuration file per runnable test configuration. Page configurations
are named `page-config.hjson` or `<variant>.page-config.hjson`, where variant is
the name of a variant of the test.

Page configs define one configuration of a test. If you want variants of a test
that differ only in probe configs or args, you will need a new page config file
as well.

## Probe Configs

Optional. Probe configurations are named `probe-config.hjson` or
`<variant>.probe-config.hjson`, where variant is the name of a variant of the
test.

When running `<variant>.page-config.hjson`, if `<variant>.probe-config.hjson`
exists it will be used, otherwise if `probe-config.hjson` exists it will be
used.

When running `page-config.hjson`, if `probe-config.hjson` exists it will be
used.

## Args

Args are optional single-line (no trailing newline) files that specify extra
arguments to pass to Crossbench or the browser during a test run. There are two
types of args files: `cb-args` and `browser-flags.hjson`.

`cb-args` and `<variant>.cb-args` files specify extra args to pass to
Crossbench.

`browser-flags.hjson` and `<variant>.browser-flags.hjson` files specify extra args to pass to the browser when running the test. This file should follow the crossbench definition for browser flags.

Like Probe Configs, when running a variant if a variant specific args files
doesn't exist but an unprefixed one does, the unprefixed file will be used.

## Setup

For tests that use wpr the wpr archive must first be download. Run wpr/gsutil-setup.sh to populate the necessary wpr files.
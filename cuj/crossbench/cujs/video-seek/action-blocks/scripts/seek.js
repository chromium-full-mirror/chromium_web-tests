// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

globalThis.seekCount = 0;
// TODO(yycheng): Remove logging once crossbench support exporting browser logs.
globalThis.logs = [];
const numSeeks = NUM_SEEK

globalThis.logs.push(`Starting test, target number of seek: ${numSeeks}`)

performance.mark('test-config', {
    detail: {
      numTargetSeeks: numSeeks
    }
  });

for (let i = 0; i < numSeeks; i++) {
  performance.mark(`randomSeek-${i}-start`);
  globalThis.logs.push(`Starting Seek number: ${i}`)
  try {
    globalThis.seekCount = await randomSeek();
    globalThis.logs.push(`Returned seek count: ${globalThis.seekCount}`)
    performance.mark(`randomSeek-${i}-end`);
    performance.measure(`randomSeek-${i}-duration`, `randomSeek-${i}-start`, `randomSeek-${i}-end`);
  } catch (error) {
    globalThis.logs.push(`Error while seeking: ${error.message}`)
    console.error(`\nError while seeking: ${error.message}`);
    console.error(`Completed ${globalThis.seekCount}/${numSeeks} seeks before failure.`);
    break;
  }

  // If we've completed all seeks, we can stop early.
  // Note: The count from randomSeek is 0-indexed, so we add 1 for comparison.
  if (globalThis.seekCount + 1 >= numSeeks) {
    globalThis.logs.push(`Early exit: ${globalThis.seekCount}`)
    break;
  }
}
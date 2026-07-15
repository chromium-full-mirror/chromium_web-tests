// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

export function mean(arr) {
  if (arr.length === 0) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

// Simple permutation test for difference in means (two-tailed)
export function permutationTest(leftVals, rightVals, resamples = 5000) {
  const obsDiff = Math.abs(mean(leftVals) - mean(rightVals));
  if (obsDiff === 0) return 1.0;

  const combined = [...leftVals, ...rightVals];
  let count = 0;
  const n = combined.length;
  const leftLen = leftVals.length;

  for (let i = 0; i < resamples; i++) {
    // Fisher-Yates shuffle
    const shuffled = [...combined];
    for (let j = n - 1; j > 0; j--) {
      const k = Math.floor(Math.random() * (j + 1));
      const temp = shuffled[j];
      shuffled[j] = shuffled[k];
      shuffled[k] = temp;
    }

    let newLeftSum = 0;
    for (let j = 0; j < leftLen; j++) {
      newLeftSum += shuffled[j];
    }

    let newRightSum = 0;
    for (let j = leftLen; j < n; j++) {
      newRightSum += shuffled[j];
    }

    const newDiff = Math.abs(
        newLeftSum / leftLen - newRightSum / (n - leftLen),
    );

    if (newDiff >= obsDiff) {
      count++;
    }
  }

  return count / resamples;
}

// Holm-Bonferroni correction (FWER)
export function holmBonferroni(results) {
  // Preserve original order
  results.forEach((r, i) => (r.originalIndex = i));

  const valid = results.filter((r) => !r.insufficientData);
  const invalid = results.filter((r) => r.insufficientData);

  // Sort valid by p-value ascending
  valid.sort((a, b) => a.pValue - b.pValue);
  const m = valid.length;

  let rejectNull = true;
  for (let i = 0; i < m; i++) {
    const adjustedAlpha = 0.05 / (m - i);
    if (rejectNull && valid[i].pValue <= adjustedAlpha) {
      valid[i].significant = true;
    } else {
      rejectNull = false;
      valid[i].significant = false;
    }
  }

  // Reconstruct results array
  const combined = [...valid, ...invalid];

  // Restore original order
  combined.sort((a, b) => a.originalIndex - b.originalIndex);
  return combined;
}

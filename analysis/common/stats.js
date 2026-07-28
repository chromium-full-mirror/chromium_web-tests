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
  if (results.length === 0) return results;
  const numVariants = results[0].comparisons ?
    results[0].comparisons.length :
    0;

  for (let v = 0; v < numVariants; v++) {
    const valid = [];
    for (let i = 0; i < results.length; i++) {
      const comp = results[i].comparisons[v];
      if (comp && !comp.insufficientData) {
        valid.push(comp);
      } else if (comp) {
        comp.significant = false;
      }
    }

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
  }

  return results;
}

// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

export function mean(arr) {
  if (arr.length === 0) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

// Number of ways to choose k of n, or Infinity once it exceeds `limit`.
function binomialUpTo(n, k, limit) {
  k = Math.min(k, n - k);
  let c = 1;
  for (let i = 1; i <= k; i++) {
    c = (c * (n - k + i)) / i;
    if (c > limit) return Infinity;
  }
  return Math.round(c);
}

// Simple permutation test for difference in means (two-tailed)
export function permutationTest(leftVals, rightVals, resamples = 5000) {
  const leftLen = leftVals.length;
  const rightLen = rightVals.length;
  const n = leftLen + rightLen;

  // Shift all values by a common offset before summing. Metrics often share
  // a large baseline (e.g. memory in MB) relative to the difference between
  // groups, and the rounding error of sums such as `total - leftSum` scales
  // with the magnitude of the values. Computing everything from the shifted
  // values keeps that error far below the tie tolerance below.
  const offset = leftVals[0];
  const combined = new Float64Array(n);
  let leftSum0 = 0;
  let maxAbs = 0;
  for (let j = 0; j < leftLen; j++) {
    const v = leftVals[j] - offset;
    combined[j] = v;
    leftSum0 += v;
    const av = Math.abs(v);
    if (av > maxAbs) maxAbs = av;
  }
  let rightSum0 = 0;
  for (let j = 0; j < rightLen; j++) {
    const v = rightVals[j] - offset;
    combined[leftLen + j] = v;
    rightSum0 += v;
    const av = Math.abs(v);
    if (av > maxAbs) maxAbs = av;
  }
  const total = leftSum0 + rightSum0;
  // Use the same formula as the permutations below so that the observed
  // split (and its mirror) always count as ties.
  const obsDiff = Math.abs(leftSum0 / leftLen - (total - leftSum0) / rightLen);
  // A difference within rounding noise of the values means "no difference".
  if (obsDiff <= maxAbs * 1e-14) return 1.0;
  // Tolerate rounding differences from summation order so permutations that
  // tie with the observed difference are still counted.
  const threshold = obsDiff * (1 - 1e-12);

  // Exact test: if there are no more possible splits than resamples (e.g. 252
  // for 5 vs 5), enumerate them all. This is exact and much cheaper.
  const numSplits = binomialUpTo(n, leftLen, resamples);
  if (numSplits !== Infinity) {
    const idx = Array.from({length: leftLen}, (_, j) => j);
    let count = 0;
    for (;;) {
      let leftSum = 0;
      for (let j = 0; j < leftLen; j++) leftSum += combined[idx[j]];
      const diff = Math.abs(leftSum / leftLen - (total - leftSum) / rightLen);
      if (diff >= threshold) count++;
      // Advance to the next combination in lexicographic order.
      let j = leftLen - 1;
      while (j >= 0 && idx[j] === n - leftLen + j) j--;
      if (j < 0) break;
      idx[j]++;
      for (let m = j + 1; m < leftLen; m++) idx[m] = idx[m - 1] + 1;
    }
    return count / numSplits;
  }

  // Monte Carlo: reuse a single buffer and shuffle it in place (copying the
  // array on every resample dominated the cost for tens of thousands of
  // metrics).
  let count = 0;
  for (let i = 0; i < resamples; i++) {
    // Partial Fisher-Yates: only the first leftLen slots need to be a uniform
    // random subset; the remaining values form the right group.
    let newLeftSum = 0;
    for (let j = 0; j < leftLen; j++) {
      const k = j + Math.floor(Math.random() * (n - j));
      const temp = combined[j];
      combined[j] = combined[k];
      combined[k] = temp;
      newLeftSum += combined[j];
    }
    const newRightSum = total - newLeftSum;

    const newDiff = Math.abs(newLeftSum / leftLen - newRightSum / rightLen);

    if (newDiff >= threshold) {
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

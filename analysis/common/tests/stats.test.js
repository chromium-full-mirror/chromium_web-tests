// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {describe, it} from 'node:test';
import assert from 'node:assert';
import {mean, permutationTest, holmBonferroni} from '../stats.js';

describe('stats', () => {
  describe('mean()', () => {
    it('should return 0 for an empty array', () => {
      assert.strictEqual(mean([]), 0);
    });

    it('should calculate correct mean for positive integers', () => {
      assert.strictEqual(mean([1, 2, 3]), 2);
      assert.strictEqual(mean([10, 20, 30, 40]), 25);
    });

    it('should calc mean for mixed positive/negative numbers', () => {
      assert.strictEqual(mean([-10, 10]), 0);
      assert.strictEqual(mean([-5, 0, 5, 10]), 2.5);
    });

    it('should calculate correct mean for floating point numbers', () => {
      assert.ok(Math.abs(mean([1.5, 2.5, 3.5]) - 2.5) < 0.0001);
      assert.ok(Math.abs(mean([0.1, 0.2]) - 0.15) < 0.0001);
    });

    it('should handle a single element array', () => {
      assert.strictEqual(mean([42]), 42);
    });
  });

  describe('permutationTest()', () => {
    it('should return 1.0 for identical means', () => {
      const left = [1, 2, 3];
      const right = [3, 2, 1];
      assert.strictEqual(permutationTest(left, right, 100), 1.0);
    });

    it('should return a very low p-value for different distributions', () => {
      // Strongly disjoint distributions
      const left = [1, 2, 1, 2, 1];
      const right = [100, 102, 101, 100, 100];
      const pVal = permutationTest(left, right, 1000);
      // Low probability of random shuffle matching this difference
      assert.ok(pVal < 0.05, `Expected pVal < 0.05, got ${pVal}`);
    });

    it('should return a high p-value for overlapping distributions', () => {
      // Very similar distributions, slight noise
      const left = [10, 11, 12, 10, 11];
      const right = [10.1, 11.2, 11.9, 10.2, 11.1];
      const pVal = permutationTest(left, right, 1000);
      assert.ok(pVal > 0.1, `Expected high pVal (> 0.1), got ${pVal}`);
    });

    it('should return the exact p-value for small samples', () => {
      // 5 vs 5 has C(10, 5) = 252 splits; only the observed split and its
      // mirror are as extreme as fully separated groups.
      const left = [1, 2, 3, 4, 5];
      const right = [11, 12, 13, 14, 15];
      assert.strictEqual(permutationTest(left, right), 2 / 252);
    });

    it('should be robust to a large common offset', () => {
      // Large baseline with tiny differences, e.g. memory in MB.
      const left = [0, 0.01, 0.02, 0.03, 0.04].map((x) => 5000 + x);
      const right = [0.1, 0.11, 0.12, 0.13, 0.14].map((x) => 5000 + x);
      assert.strictEqual(permutationTest(left, right), 2 / 252);
      assert.strictEqual(permutationTest(right, left), 2 / 252);

      const left2 = [0, 1, 2, 3, 4].map((x) => 1e6 + x * 1e-4);
      const right2 = [10, 11, 12, 13, 14].map((x) => 1e6 + x * 1e-4);
      assert.strictEqual(permutationTest(left2, right2), 2 / 252);
    });

    it('should count the observed split for unequal sizes', () => {
      // 4 vs 5 has C(9, 4) = 126 splits and only the observed one is as
      // extreme, so p must be 1/126 (never 0).
      const left = [0, 1, 2, 3].map((x) => 1e6 + x * 1e-4);
      const right = [10, 11, 12, 13, 14].map((x) => 1e6 + x * 1e-4);
      assert.strictEqual(permutationTest(left, right), 1 / 126);
    });

    it('should return 1.0 for the same values in a different order', () => {
      // Summing in a different order can differ by 1 ULP.
      const left = [0.1, 0.2, 0.3, 0.4, 0.7];
      const right = [0.7, 0.4, 0.3, 0.2, 0.1];
      assert.strictEqual(permutationTest(left, right), 1.0);
    });

    it('should return a low p-value via Monte Carlo with an offset', () => {
      // 10 vs 10 has C(20, 10) = 184756 splits, more than the resamples.
      const left = Array.from({length: 10}, (_, i) => 5000 + i * 1e-3);
      const right = Array.from({length: 10}, (_, i) => 5000.1 + i * 1e-3);
      const pVal = permutationTest(left, right, 2000);
      assert.ok(pVal < 0.01, `Expected pVal < 0.01, got ${pVal}`);
    });
  });

  describe('holmBonferroni()', () => {
    it('should correctly adjust p-values and identify significance', () => {
      const results = [
        {comparisons: [{id: 1, pValue: 0.01, insufficientData: false}]}, // 0.01 < 0.0166 -> sig
        {comparisons: [{id: 2, pValue: 0.04, insufficientData: false}]}, // 0.04 > 0.025 -> false
        {comparisons: [{id: 3, pValue: 0.1, insufficientData: false}]}, // sig=false
        {comparisons: [{id: 4, pValue: null, insufficientData: true}]}, // ignored
      ];

      const adjusted = holmBonferroni(results);

      // Order should be preserved!
      assert.strictEqual(adjusted[0].comparisons[0].id, 1);
      assert.strictEqual(adjusted[0].comparisons[0].significant, true);

      assert.strictEqual(adjusted[1].comparisons[0].id, 2);
      assert.strictEqual(adjusted[1].comparisons[0].significant, false);

      assert.strictEqual(adjusted[2].comparisons[0].id, 3);
      assert.strictEqual(adjusted[2].comparisons[0].significant, false);

      assert.strictEqual(adjusted[3].comparisons[0].id, 4);
      assert.strictEqual(adjusted[3].comparisons[0].significant, false);
    });

    it('should stop rejecting null hypothesis when one fails', () => {
      const results = [
        {comparisons: [{id: 'a', pValue: 0.001, insufficientData: false}]}, // sig
        {comparisons: [{id: 'b', pValue: 0.05, insufficientData: false}]}, // NOT sig (breaks)
        {comparisons: [{id: 'c', pValue: 0.02, insufficientData: false}]}, // NOT sig (broken)
        {comparisons: [{id: 'd', pValue: 0.005, insufficientData: false}]}, // sorts before b
      ];

      // After sorting by pValue:
      // a (0.001) -> m-0 = 4, adj 0.0125 -> sig
      // d (0.005) -> m-1 = 3, adj 0.0166 -> sig
      // c (0.02)  -> m-2 = 2, adj 0.025  -> sig
      // b (0.05)  -> m-3 = 1, adj 0.05   -> sig

      const adjusted = holmBonferroni(results);

      // All passed their adjusted thresholds in order
      assert.strictEqual(adjusted[0].comparisons[0].significant, true); // a
      assert.strictEqual(adjusted[1].comparisons[0].significant, true); // b
      assert.strictEqual(adjusted[2].comparisons[0].significant, true); // c
      assert.strictEqual(adjusted[3].comparisons[0].significant, true); // d
    });

    it('should properly break the rejection chain', () => {
      const results = [
        {comparisons: [{id: 'a', pValue: 0.001, insufficientData: false}]}, // sig
        {comparisons: [{id: 'b', pValue: 0.04, insufficientData: false}]}, // breaks chain
        {comparisons: [{id: 'c', pValue: 0.045, insufficientData: false}]}, // chain broken
      ];
      // Sorted: a (0.001) -> sig
      // b (0.04) vs 0.05/2 = 0.025 -> NOT sig
      // c (0.045) -> automatically NOT sig because b failed

      const adjusted = holmBonferroni(results);
      assert.strictEqual(adjusted[0].comparisons[0].significant, true); // a
      assert.strictEqual(adjusted[1].comparisons[0].significant, false); // b
      assert.strictEqual(adjusted[2].comparisons[0].significant, false); // c
    });

    it('should correctly handle multi-group comparisons', () => {
      // 3 metrics, each with 2 comparisons (Variant 1 vs Baseline, Variant 2 vs Baseline)
      const results = [
        {
          comparisons: [
            {id: 'm1_v1', pValue: 0.01, insufficientData: false}, // v1: sig (0.01 <= 0.0166)
            {id: 'm1_v2', pValue: 0.06, insufficientData: false}, // v2: not sig (0.06 > 0.05)
          ],
        },
        {
          comparisons: [
            {id: 'm2_v1', pValue: 0.1, insufficientData: false}, // v1: not sig (chain broken)
            {id: 'm2_v2', pValue: 0.001, insufficientData: false}, // v2: sig (0.001 <= 0.0166)
          ],
        },
        {
          comparisons: [
            {id: 'm3_v1', pValue: 0.03, insufficientData: false}, // v1: not sig (0.03 > 0.025)
            {id: 'm3_v2', pValue: 0.02, insufficientData: false}, // v2: sig (0.02 <= 0.025)
          ],
        },
      ];

      const adjusted = holmBonferroni(results);

      // metric 1
      assert.strictEqual(adjusted[0].comparisons[0].significant, true, 'm1_v1');
      assert.strictEqual(
          adjusted[0].comparisons[1].significant,
          false,
          'm1_v2',
      );

      // metric 2
      assert.strictEqual(
          adjusted[1].comparisons[0].significant,
          false,
          'm2_v1',
      );
      assert.strictEqual(adjusted[1].comparisons[1].significant, true, 'm2_v2');

      // metric 3
      assert.strictEqual(
          adjusted[2].comparisons[0].significant,
          false,
          'm3_v1',
      );
      assert.strictEqual(adjusted[2].comparisons[1].significant, true, 'm3_v2');
    });
  });
});

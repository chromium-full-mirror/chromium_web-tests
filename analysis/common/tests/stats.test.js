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
  });

  describe('holmBonferroni()', () => {
    it('should correctly adjust p-values and identify significance', () => {
      const results = [
        {id: 1, pValue: 0.01, insufficientData: false}, // 0.01 < 0.0166 -> sig
        {id: 2, pValue: 0.04, insufficientData: false}, // 0.04 > 0.025 -> false
        {id: 3, pValue: 0.1, insufficientData: false}, // sig=false
        {id: 4, pValue: null, insufficientData: true}, // ignored
      ];

      const adjusted = holmBonferroni(results);

      // Order should be preserved!
      assert.strictEqual(adjusted[0].id, 1);
      assert.strictEqual(adjusted[0].significant, true);

      assert.strictEqual(adjusted[1].id, 2);
      assert.strictEqual(adjusted[1].significant, false);

      assert.strictEqual(adjusted[2].id, 3);
      assert.strictEqual(adjusted[2].significant, false);

      assert.strictEqual(adjusted[3].id, 4);
      assert.strictEqual(adjusted[3].significant, undefined);
    });

    it('should stop rejecting null hypothesis when one fails', () => {
      const results = [
        {id: 'a', pValue: 0.001, insufficientData: false}, // sig
        {id: 'b', pValue: 0.05, insufficientData: false}, // NOT sig (breaks)
        {id: 'c', pValue: 0.02, insufficientData: false}, // NOT sig (broken)
        {id: 'd', pValue: 0.005, insufficientData: false}, // sorts before b
      ];

      // After sorting by pValue:
      // a (0.001) -> m-0 = 4, adj 0.0125 -> sig
      // d (0.005) -> m-1 = 3, adj 0.0166 -> sig
      // c (0.02)  -> m-2 = 2, adj 0.025  -> sig
      // b (0.05)  -> m-3 = 1, adj 0.05   -> sig

      const adjusted = holmBonferroni(results);

      // All passed their adjusted thresholds in order
      assert.strictEqual(adjusted[0].significant, true); // a
      assert.strictEqual(adjusted[1].significant, true); // b
      assert.strictEqual(adjusted[2].significant, true); // c
      assert.strictEqual(adjusted[3].significant, true); // d
    });

    it('should properly break the rejection chain', () => {
      const results = [
        {id: 'a', pValue: 0.001, insufficientData: false}, // sig
        {id: 'b', pValue: 0.04, insufficientData: false}, // breaks chain
        {id: 'c', pValue: 0.045, insufficientData: false}, // chain broken
      ];
      // Sorted: a (0.001) -> sig
      // b (0.04) vs 0.05/2 = 0.025 -> NOT sig
      // c (0.045) -> automatically NOT sig because b failed

      const adjusted = holmBonferroni(results);
      assert.strictEqual(adjusted[0].significant, true); // a
      assert.strictEqual(adjusted[1].significant, false); // b
      assert.strictEqual(adjusted[2].significant, false); // c
    });
  });
});

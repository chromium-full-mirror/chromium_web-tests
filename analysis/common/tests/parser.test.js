// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {describe, it} from 'node:test';
import assert from 'node:assert';
import {parseDataset} from '../parser.js';

describe('parser', () => {
  it('should parse datasets and aggregate values', () => {
    const sampleJson = {
      metadata: {run_id: 'converted'},
      metrics: [
        {
          test_name: 'jetstream_2.2',
          metric: '3d-cube-SP/Average',
          values: [100],
          units: 'ms',
        },
        {
          test_name: 'jetstream_2.2',
          metric: '3d-cube-SP/Average',
          values: [200],
          units: 'ms',
        },
        {
          test_name: 'speedometer',
          metric: 'Score',
          values: [300, 350],
          units: 'score',
        },
        {metric: 'invalid-json-key', values: [400]},
      ],
    };

    const map = parseDataset(JSON.stringify(sampleJson));

    // Assert 1: Basic test parsing and fallbacks
    assert(map.has('jetstream_2.2'), 'Missing jetstream_2.2');
    assert(map.has('speedometer'), 'Missing speedometer');
    assert(map.has('Unknown_Test'), 'Missing Unknown_Test for invalid key');

    // Assert 2: Values correctly aggregated across runs
    const jetstream = map.get('jetstream_2.2');
    assert(
        jetstream.has('3d-cube-SP/Average'),
        'Missing 3d-cube-SP/Average metric',
    );
    const vals = jetstream.get('3d-cube-SP/Average').values;
    assert.deepStrictEqual(vals, [100, 200], 'Values incorrectly aggregated');

    // Assert 3: Array values correctly aggregated
    const speedometerVals = map.get('speedometer').get('Score').values;
    assert.deepStrictEqual(
        speedometerVals,
        [300, 350],
        'Array values incorrectly aggregated',
    );
  });

  it('should extract metadata from common-metrics keys', () => {
    const sampleJson = {
      metadata: {
        system_ram_bytes: 1024,
        version: '123.0',
      },
      metrics: [],
    };
    const map = parseDataset(JSON.stringify(sampleJson));
    assert.strictEqual(map.metadata['system_ram_bytes'], 1024);
    assert.strictEqual(map.metadata['version'], '123.0');
  });
});

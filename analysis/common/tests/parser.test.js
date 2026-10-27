// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {describe, it} from 'node:test';
import assert from 'node:assert';
import {extractAggMode, parseDataset} from '../parser.js';

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

  it('should extract metadata from common-metrics keys without polluting with performance metrics', () => {
    const sampleJson = {
      metadata: {
        system_ram_bytes: 1024,
        version: '123.0',
      },
      metrics: [
        {
          test_name: 'docs',
          metric: 'cuj.common-metrics.lmk_kill_count-1',
          values: [2],
        },
        {
          test_name: 'docs',
          metric: 'cuj.common-metrics.meminfo.browser_pss_total_mb-1-End',
          values: [512],
        },
      ],
    };
    const map = parseDataset(JSON.stringify(sampleJson));
    assert.strictEqual(map.metadata['system_ram_bytes'], 1024);
    assert.strictEqual(map.metadata['version'], '123.0');
    assert.strictEqual(map.metadata['lmk_kill_count'], undefined);
    assert.strictEqual(map.metadata['browser_pss_total_mb'], undefined);
  });

  it('should accurately extract aggregation modes without mangling raw metric names', () => {
    assert.deepStrictEqual(
        extractAggMode('cuj.uma.lower_is_better-EventLatency.TotalLatency-p90'),
        {displayName: 'EventLatency.TotalLatency', aggMode: 'p90'},
    );
    assert.deepStrictEqual(
        extractAggMode('cuj.docs_tab_switches.tab_switch_latency.p90'),
        {displayName: 'cuj.docs_tab_switches.tab_switch_latency', aggMode: 'p90'},
    );
    assert.deepStrictEqual(
        extractAggMode(
            'cuj.common-metrics.cpu_usage_stat.p50_cputime-cpu.times.user_ns',
        ),
        {
          displayName:
          'cuj.common-metrics.cpu_usage_stat.cputime-cpu.times.user_ns',
          aggMode: 'p50',
        },
    );
    assert.deepStrictEqual(
        extractAggMode('cuj.common-metrics.meminfo.browser_pss_total_mb-1-End'),
        {
          displayName: 'cuj.common-metrics.meminfo.browser_pss_total_mb-1-End',
          aggMode: 'raw',
        },
    );
    assert.deepStrictEqual(
        extractAggMode('cuj.common-metrics.lmk_kill_count-1'),
        {displayName: 'cuj.common-metrics.lmk_kill_count-1', aggMode: 'raw'},
    );
  });
});

// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {describe, it, before, after} from 'node:test';
import assert from 'node:assert';
import {spawn} from 'child_process';
import {join, dirname} from 'path';
import {fileURLToPath} from 'url';
import {writeFileSync, unlinkSync} from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const mcpPath = join(__dirname, '../mcp.js');

// Create some dummy datasets for testing
const mockDataset1Path = join(__dirname, 'mock_dataset1.json');
const mockDataset2Path = join(__dirname, 'mock_dataset2.json');

const mockDataset1 = {
  metadata: {run_id: 'left'},
  metrics: [
    {test_name: 'test_A', metric: 'score', values: [100]},
    {test_name: 'test_B', metric: 'score', values: [200]},
    {
      test_name: 'setup',
      metric: 'cuj.common-metrics.system_info.os-linux',
      values: [1],
    },
    {
      test_name: 'setup',
      metric: 'cuj.common-metrics.system_info.ram-16GB',
      values: [1],
    },
  ],
};

const mockDataset2 = {
  metadata: {run_id: 'right'},
  metrics: [
    {test_name: 'test_A', metric: 'score', values: [110]},
    {test_name: 'test_C', metric: 'score', values: [300]},
    {
      test_name: 'setup',
      metric: 'cuj.common-metrics.system_info.os-linux',
      values: [1],
    },
    {
      test_name: 'setup',
      metric: 'cuj.common-metrics.system_info.ram-32GB',
      values: [1],
    },
  ],
};

const testDatasetGroups = [
  {name: 'Group 1', paths: [mockDataset1Path]},
  {name: 'Group 2', paths: [mockDataset2Path]},
];

describe('MCP Server', () => {
  let mcpProcess;
  let messageId = 1;
  const pendingRequests = new Map();

  before(() => {
    writeFileSync(mockDataset1Path, JSON.stringify(mockDataset1));
    writeFileSync(mockDataset2Path, JSON.stringify(mockDataset2));

    const nodeBin = join(
        __dirname,
        '../../../third_party/crossbench/third_party/node/linux/node-linux-x64/bin/node',
    );
    mcpProcess = spawn(nodeBin, [mcpPath], {
      stdio: ['pipe', 'pipe', 'inherit'],
    });

    let buffer = '';
    mcpProcess.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.id !== undefined && pendingRequests.has(msg.id)) {
            const {resolve, reject} = pendingRequests.get(msg.id);
            pendingRequests.delete(msg.id);
            if (msg.error) reject(new Error(msg.error.message));
            else resolve(msg.result);
          }
        } catch (e) {
          console.error('Failed to parse JSON:', line, e);
        }
      }
    });
  });

  after(() => {
    if (mcpProcess) mcpProcess.kill();
    try {
      unlinkSync(mockDataset1Path);
    } catch {}
    try {
      unlinkSync(mockDataset2Path);
    } catch {}
  });

  function sendRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = messageId++;
      pendingRequests.set(id, {resolve, reject});
      const request = {
        jsonrpc: '2.0',
        id,
        method,
        params,
      };
      mcpProcess.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  it('should initialize successfully', async () => {
    const result = await sendRequest('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: {name: 'test', version: '1.0'},
    });

    assert.strictEqual(result.serverInfo.name, 'Web Tests Analyzer MCP');
    assert.ok(result.capabilities);
  });

  it('should list tools', async () => {
    const result = await sendRequest('tools/list');
    assert.ok(result.tools.length > 0);
    const toolNames = result.tools.map((t) => t.name);
    assert.ok(toolNames.includes('compare_datasets'));
    assert.ok(toolNames.includes('analyze_test'));
    assert.ok(toolNames.includes('get_important_metrics'));
    assert.ok(toolNames.includes('get_dataset_metadata'));
    assert.ok(toolNames.includes('analyze_all_tests'));
    assert.ok(toolNames.includes('get_significant_changes'));
  });

  it('compare_datasets should return missing and common tests', async () => {
    const result = await sendRequest('tools/call', {
      name: 'compare_datasets',
      arguments: {
        datasetGroups: testDatasetGroups,
      },
    });

    assert.ok(result.content);
    assert.strictEqual(result.content[0].type, 'text');

    const parsed = JSON.parse(result.content[0].text);
    assert.deepStrictEqual(parsed.baselineTests, ['setup', 'test_A', 'test_B']);
    // There should be mismatches between Group 1 and Group 2
    assert.strictEqual(parsed.mismatches.length, 1);
    assert.deepStrictEqual(parsed.mismatches[0].missingTests, [
      'test_B',
      'test_C',
    ]);
  });

  it('compare_datasets should throw if no datasetGroups provided', async () => {
    await assert.rejects(
        sendRequest('tools/call', {
          name: 'compare_datasets',
          arguments: {},
        }),
        /datasetGroups array must contain at least one group/,
    );
  });

  it('get_dataset_metadata should return dataset metadata', async () => {
    const result = await sendRequest('tools/call', {
      name: 'get_dataset_metadata',
      arguments: {
        datasetGroups: testDatasetGroups,
      },
    });

    assert.ok(result.content);
    const parsed = JSON.parse(result.content[0].text);

    assert.ok(parsed['Group 1']);
    assert.strictEqual(parsed['Group 1'].run_id, 'left');
    assert.ok(parsed['Group 2']);
    assert.strictEqual(parsed['Group 2'].run_id, 'right');
  });

  it('analyze_test should return statistical comparison', async () => {
    const result = await sendRequest('tools/call', {
      name: 'analyze_test',
      arguments: {
        testName: 'test_A',
        datasetGroups: testDatasetGroups,
      },
    });

    assert.ok(result.content);
    const parsed = JSON.parse(result.content[0].text);

    assert.ok(parsed.length > 0);
    const scoreMetric = parsed.find((m) => m.metricName === 'score');
    assert.ok(scoreMetric);
    assert.strictEqual(scoreMetric.groupMeans[0], 100);
    assert.strictEqual(scoreMetric.groupMeans[1], 110);
  });

  it('analyze_all_tests returns comparison for all common tests', async () => {
    const result = await sendRequest('tools/call', {
      name: 'analyze_all_tests',
      arguments: {
        datasetGroups: testDatasetGroups,
      },
    });

    assert.ok(result.content);
    const parsed = JSON.parse(result.content[0].text);

    assert.ok(parsed.tests['test_A']);
    assert.strictEqual(parsed.tests['test_A'][0].metricName, 'score');
    assert.strictEqual(parsed.tests['test_A'][0].groupMeans[0], 100);
    assert.strictEqual(parsed.tests['test_A'][0].groupMeans[1], 110);
  });

  it('get_significant_changes filters to significant changes', async () => {
    const result = await sendRequest('tools/call', {
      name: 'get_significant_changes',
      arguments: {
        testName: 'test_A',
        datasetGroups: testDatasetGroups,
      },
    });

    assert.ok(result.content);
    const parsed = JSON.parse(result.content[0].text);

    // Mock datasets have 1 point each so they have pValue null
    // Therefore they are not statistically significant and should be filtered out
    assert.ok(parsed.tests['test_A'] === undefined);
  });

  it('get_significant_changes works with sample files', async () => {
    const sample1Path = join(
        __dirname,
        '../../common/tests/sample_1.metrics.json',
    );
    const sample2Path = join(
        __dirname,
        '../../common/tests/sample_2.metrics.json',
    );
    const sample3Path = join(
        __dirname,
        '../../common/tests/sample_3.metrics.json',
    );

    const result = await sendRequest('tools/call', {
      name: 'get_significant_changes',
      arguments: {
        testName: 'test_suite_A',
        datasetGroups: [
          {name: 'Group 1', paths: [sample1Path]},
          {name: 'Group 2', paths: [sample2Path]},
          {name: 'Group 3', paths: [sample3Path]},
        ],
      },
    });

    assert.ok(result.content);
    const parsed = JSON.parse(result.content[0].text);

    // sample1: 100 avg, sample2: 110 avg, sample3: 90 avg
    // improvement_direction is "down" (lower is better)
    assert.ok(parsed.tests['test_suite_A']);
    const metric = parsed.tests['test_suite_A'][0];
    assert.strictEqual(metric.metricName, 'score');

    // Group 2 comparison (100 -> 110)
    assert.strictEqual(metric.comparisons[0].significant, true);
    assert.strictEqual(metric.comparisons[0].isRegression, true);

    // Group 3 comparison (100 -> 90)
    assert.strictEqual(metric.comparisons[1].significant, true);
    assert.strictEqual(metric.comparisons[1].isImprovement, true);

    assert.strictEqual(parsed.summary.totalRegressions, 1);
    assert.strictEqual(parsed.summary.totalImprovements, 1);
  });
});

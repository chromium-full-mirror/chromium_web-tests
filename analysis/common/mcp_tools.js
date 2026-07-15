// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {AGG_MODES} from './parser.js';
import {
  getCommonTests,
  getDatasetMismatches,
  buildDataModel,
  analyzeTestMetrics,
  filterMetrics,
  getImportantMetricsForTest,
} from './analyzer.js';

const datasetGroupsSchema = {
  type: 'array',
  items: {
    type: 'object',
    properties: {
      name: {type: 'string', description: 'Name of the dataset group.'},
      paths: {
        type: 'array',
        items: {type: 'string'},
        description: 'Array of paths or gs:// URIs to the dataset JSONs.',
      },
    },
    required: ['name', 'paths'],
  },
  description:
    'Array of dataset groups. Each group should have a name and an array of JSON file paths or gs:// URIs.',
};

export const mcpToolSchemas = [
  {
    name: 'get_dataset_metadata',
    description:
      'Get system and environment metadata for the given datasets ' +
      '(e.g. OS, board, RAM). Intended as a starting point for analysis.',
    inputSchema: {
      type: 'object',
      properties: {
        datasetGroups: datasetGroupsSchema,
      },
      required: ['datasetGroups'],
    },
  },
  {
    name: 'compare_datasets',
    description:
      'Load and compare dataset JSON files (local paths or gs:// URLs) ' +
      'to find which tests they ran.',
    inputSchema: {
      type: 'object',
      properties: {
        datasetGroups: datasetGroupsSchema,
      },
      required: ['datasetGroups'],
    },
  },
  {
    name: 'analyze_test',
    description:
      'Analyze the metrics for a specific test across dataset groups.',
    inputSchema: {
      type: 'object',
      properties: {
        testName: {
          type: 'string',
          description: 'Name of the test to analyze (e.g. jetstream_2.2).',
        },
        datasetGroups: datasetGroupsSchema,
        displayAll: {
          type: 'boolean',
          description:
            'If true, display all metrics instead of just the ' +
            'important ones. Default false.',
        },
        aggMode: {
          type: 'string',
          description:
            `Filter for aggregated metrics. Options: ` +
            `'${AGG_MODES.join('\', \'')}'. Default 'all'.`,
        },
        importantMetrics: {
          type: 'array',
          items: {type: 'string'},
          description:
            'List of important metric names to filter by ' +
            'if displayAll is false.',
        },
      },
      required: ['testName', 'datasetGroups'],
    },
  },
  {
    name: 'get_important_metrics',
    description:
      'Get the list of important metrics for a specific test name ' +
      'according to the metrics manifest.',
    inputSchema: {
      type: 'object',
      properties: {
        testName: {
          type: 'string',
          description: 'Name of the test to query (e.g. jetstream_2.2).',
        },
      },
      required: ['testName'],
    },
  },
  {
    name: 'analyze_all_tests',
    description:
      'Analyze the metrics for all common tests across the dataset groups.',
    inputSchema: {
      type: 'object',
      properties: {
        datasetGroups: datasetGroupsSchema,
        displayAll: {
          type: 'boolean',
          description:
            'If true, display all metrics instead of just the ' +
            'important ones. Default false.',
        },
        aggMode: {
          type: 'string',
          description:
            `Filter for aggregated metrics. Options: ` +
            `'${AGG_MODES.join('\', \'')}'. Default 'all'.`,
        },
      },
      required: ['datasetGroups'],
    },
  },
  {
    name: 'get_significant_changes',
    description:
      'Automatically analyze all common tests and filter the results to only ' +
      'show metrics with a statistically significant change ' +
      '(or insufficient data). Ideal for constructing highlight reports.',
    inputSchema: {
      type: 'object',
      properties: {
        datasetGroups: datasetGroupsSchema,
        displayAll: {
          type: 'boolean',
          description:
            'If true, include all metrics with significant changes. ' +
            'If false, only include important metrics. Default false.',
        },
        aggMode: {
          type: 'string',
          description:
            `Filter for aggregated metrics. Options: ` +
            `'${AGG_MODES.join('\', \'')}'. Default 'all'.`,
        },
      },
      required: ['datasetGroups'],
    },
  },
];

export function mcpSchemaToGeminiSchema(mcpSchema) {
  function mapType(type) {
    if (type === 'string') return 'STRING';
    if (type === 'number' || type === 'integer') return 'NUMBER';
    if (type === 'boolean') return 'BOOLEAN';
    if (type === 'object') return 'OBJECT';
    if (type === 'array') return 'ARRAY';
    return 'STRING';
  }

  function convertProperties(props) {
    const geminiProps = {};
    for (const key of Object.keys(props)) {
      const prop = props[key];
      const newProp = {type: mapType(prop.type)};
      if (prop.description) newProp.description = prop.description;
      if (prop.items) newProp.items = {type: mapType(prop.items.type)};
      if (prop.properties) {
        newProp.type = 'OBJECT';
      }
      geminiProps[key] = newProp;
    }
    return geminiProps;
  }

  return {
    name: mcpSchema.name,
    description: mcpSchema.description,
    parameters: {
      type: mapType(mcpSchema.inputSchema.type),
      properties: convertProperties(mcpSchema.inputSchema.properties || {}),
      required: mcpSchema.inputSchema.required || [],
    },
  };
}

async function loadDatasets(args, loadDatasetFn) {
  const datasetGroups = args.datasetGroups || [];

  if (datasetGroups.length === 0) {
    throw new Error('datasetGroups array must contain at least one group.');
  }

  const dataModel = {groups: []};
  for (const group of datasetGroups) {
    const rawStrings = await Promise.all(
        group.paths.map((p) => loadDatasetFn(p)),
    );
    dataModel.groups.push({
      name: group.name,
      _rawStrings: rawStrings,
    });
  }

  return buildDataModel(dataModel);
}

export async function executeMcpTool(name, args, loadDatasetFn) {
  if (name === 'compare_datasets') {
    const dataModel = await loadDatasets(args, loadDatasetFn);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
              {
                commonTests: getCommonTests(dataModel),
                mismatches: getDatasetMismatches(dataModel),
              },
              null,
              2,
          ),
        },
      ],
    };
  }

  if (name === 'analyze_test') {
    const dataModel = await loadDatasets(args, loadDatasetFn);
    const results = analyzeTestMetrics(args.testName, dataModel);

    const importantMetrics =
      args.importantMetrics || getImportantMetricsForTest(args.testName);

    const filteredResults = filterMetrics(results, {
      aggMode: args.aggMode || 'all',
      importantMetrics,
      displayAll: args.displayAll || false,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(filteredResults, null, 2),
        },
      ],
    };
  }

  if (name === 'get_dataset_metadata') {
    const dataModel = await loadDatasets(args, loadDatasetFn);
    const metadataResult = {};
    for (const group of dataModel.groups) {
      metadataResult[group.name] = group.metrics.metadata;
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(metadataResult, null, 2),
        },
      ],
    };
  }

  if (name === 'get_important_metrics') {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
              getImportantMetricsForTest(args.testName),
              null,
              2,
          ),
        },
      ],
    };
  }

  if (name === 'analyze_all_tests' || name === 'get_significant_changes') {
    const dataModel = await loadDatasets(args, loadDatasetFn);
    const commonTests = getCommonTests(dataModel);

    const allResults = {
      summary: {
        totalRegressions: 0,
        totalImprovements: 0,
      },
      tests: {},
    };

    for (const testName of commonTests) {
      let importantMetrics = [];
      if (!args.displayAll) {
        importantMetrics = getImportantMetricsForTest(testName);
      }

      const results = analyzeTestMetrics(testName, dataModel);

      const filteredResults = filterMetrics(results, {
        aggMode: args.aggMode || 'all',
        importantMetrics,
        displayAll: args.displayAll || false,
        significantOnly: name === 'get_significant_changes',
      });

      if (filteredResults.length > 0) {
        allResults.tests[testName] = filteredResults;
        for (const m of filteredResults) {
          // Count regressions and improvements
          if (m.significant) {
            if (m.isRegression) allResults.summary.totalRegressions++;
            if (m.isImprovement) allResults.summary.totalImprovements++;
          }
        }
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(allResults, null, 2),
        },
      ],
    };
  }

  throw new Error(`Tool ${name} not found`);
}

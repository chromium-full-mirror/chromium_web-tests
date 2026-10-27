// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {AGG_MODES} from './parser.js';
import {
  getBaselineTests,
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

        aggMode: {
          type: 'string',
          description:
            `Filter for aggregated metrics. Options: ` +
            `'${AGG_MODES.join('\', \'')}'. Default 'all'.`,
        },
        importantMetrics: {
          type: 'array',
          items: {type: 'string'},
          description: 'List of important metric names to filter by.',
        },
        searchQuery: {
          type: 'string',
          description:
            'Optional case-insensitive substring to search across metric names.',
        },
        displayAll: {
          type: 'boolean',
          description:
            'If true, returns all metrics for the test instead of filtering ' +
            'to importantMetrics. Defaults to false (or true when searchQuery is set).',
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

        aggMode: {
          type: 'string',
          description:
            `Filter for aggregated metrics. Options: ` +
            `'${AGG_MODES.join('\', \'')}'. Default 'all'.`,
        },
        searchQuery: {
          type: 'string',
          description:
            'Optional case-insensitive substring to search across metric names.',
        },
        displayAll: {
          type: 'boolean',
          description:
            'If true, analyzes all metrics instead of only importantMetrics.',
        },
      },
      required: ['datasetGroups'],
    },
  },
  {
    name: 'get_significant_changes',
    description:
      'Analyze a specific test (or all common tests if testName is omitted) ' +
      'and filter the results to only show metrics with a statistically ' +
      'significant change. Ideal for constructing highlight reports.',
    inputSchema: {
      type: 'object',
      properties: {
        testName: {
          type: 'string',
          description:
            'Optional name of a specific test to query (e.g. jetstream_2.2). ' +
            'If omitted, analyzes all common baseline tests.',
        },
        datasetGroups: datasetGroupsSchema,

        aggMode: {
          type: 'string',
          description:
            `Filter for aggregated metrics. Options: ` +
            `'${AGG_MODES.join('\', \'')}'. Default 'all'.`,
        },
        importantMetrics: {
          type: 'array',
          items: {type: 'string'},
          description: 'Optional list of metric names/substrings to filter by.',
        },
        searchQuery: {
          type: 'string',
          description:
            'Optional case-insensitive substring to search across metric names.',
        },
        displayAll: {
          type: 'boolean',
          description:
            'If true, checks all metrics for significance instead of only importantMetrics.',
        },
        includeRawSignificant: {
          type: 'boolean',
          description:
            'If true, also includes metrics with raw pValue <= 0.05 even when ' +
            'small sample size (e.g. N <= 5) prevents passing Holm-Bonferroni.',
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

let cachedDataModel = null;
let cachedGroupsSignature = null;
const cachedTestAnalysis = new Map();

function matchesCachedSignature(datasetGroups, rawStringsByGroup) {
  if (!cachedGroupsSignature) return false;
  if (cachedGroupsSignature.length !== datasetGroups.length) return false;
  for (let i = 0; i < datasetGroups.length; i++) {
    const entry = cachedGroupsSignature[i];
    if (entry.name !== datasetGroups[i].name) return false;
    const rawStrings = rawStringsByGroup[i];
    if (entry.rawStrings.length !== rawStrings.length) return false;
    for (let j = 0; j < rawStrings.length; j++) {
      if (entry.rawStrings[j] !== rawStrings[j]) return false;
    }
  }
  return true;
}

async function loadDatasets(args, loadDatasetFn) {
  const datasetGroups = args.datasetGroups || [];

  if (datasetGroups.length === 0) {
    throw new Error('datasetGroups array must contain at least one group.');
  }

  const rawStringsByGroup = [];
  for (const group of datasetGroups) {
    const rawStrings = await Promise.all(
        group.paths.map((p) => loadDatasetFn(p)),
    );
    rawStringsByGroup.push(rawStrings);
  }

  if (
    cachedDataModel &&
    matchesCachedSignature(datasetGroups, rawStringsByGroup)
  ) {
    return cachedDataModel;
  }

  const dataModel = {groups: []};
  for (let i = 0; i < datasetGroups.length; i++) {
    dataModel.groups.push({
      name: datasetGroups[i].name,
      _rawStrings: rawStringsByGroup[i],
    });
  }

  cachedDataModel = buildDataModel(dataModel);
  cachedGroupsSignature = datasetGroups.map((g, i) => ({
    name: g.name,
    rawStrings: rawStringsByGroup[i],
  }));
  cachedTestAnalysis.clear();

  return cachedDataModel;
}

function getCachedTestMetrics(testName, dataModel) {
  if (!cachedTestAnalysis.has(testName)) {
    cachedTestAnalysis.set(testName, analyzeTestMetrics(testName, dataModel));
  }
  return cachedTestAnalysis.get(testName);
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
                baselineTests: getBaselineTests(dataModel),
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
    const results = getCachedTestMetrics(args.testName, dataModel);

    const importantMetrics =
      args.importantMetrics || getImportantMetricsForTest(args.testName);
    const displayAll =
      args.displayAll !== undefined ?
        Boolean(args.displayAll) :
        Boolean(args.searchQuery && !args.importantMetrics);

    const filteredResults = filterMetrics(results, {
      aggMode: args.aggMode || 'all',
      importantMetrics,
      displayAll,
      searchQuery: args.searchQuery || '',
    });

    // Strip groupValuesList to reduce JSON size for the LLM
    filteredResults.forEach((m) => {
      delete m.groupValuesList;
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
    const testsToAnalyze = args.testName ?
      [args.testName] :
      getBaselineTests(dataModel);

    const includeRawSignificant = Boolean(args.includeRawSignificant);
    const displayAll =
      args.displayAll !== undefined ?
        Boolean(args.displayAll) :
        Boolean(args.searchQuery && !args.importantMetrics);

    const allResults = {
      summary: {
        totalRegressions: 0,
        totalImprovements: 0,
        totalUnknownDirection: 0,
        totalRawRegressions: 0,
        totalRawImprovements: 0,
      },
      tests: {},
    };

    for (const testName of testsToAnalyze) {
      const importantMetrics =
        args.importantMetrics || getImportantMetricsForTest(testName);

      const results = getCachedTestMetrics(testName, dataModel);

      const filteredResults = filterMetrics(results, {
        aggMode: args.aggMode || 'all',
        importantMetrics,
        displayAll,
        searchQuery: args.searchQuery || '',
        significantOnly: name === 'get_significant_changes',
        includeRawSignificant,
      });

      if (filteredResults.length > 0) {
        // Strip groupValuesList to reduce JSON size for the LLM
        filteredResults.forEach((m) => {
          delete m.groupValuesList;
        });

        allResults.tests[testName] = filteredResults;
        for (const m of filteredResults) {
          // Count regressions and improvements
          if (m.comparisons) {
            for (const comp of m.comparisons) {
              if (comp.significant) {
                if (comp.isRegression) allResults.summary.totalRegressions++;
                else if (comp.isImprovement) {
                  allResults.summary.totalImprovements++;
                } else allResults.summary.totalUnknownDirection++;
              }
              if (comp.rawSignificant) {
                if (comp.isRegression) allResults.summary.totalRawRegressions++;
                else if (comp.isImprovement) {
                  allResults.summary.totalRawImprovements++;
                }
              }
            }
          }
        }

        if (name === 'get_significant_changes') {
          // Remove metrics that don't have any actual statistically significant changes
          // (some might sneak in if they had missing data comparisons)
          allResults.tests[testName] = filteredResults.filter((m) => {
            if (!m.comparisons) return false;
            return m.comparisons.some(
                (c) =>
                  c.significant === true ||
                (includeRawSignificant && c.rawSignificant === true),
            );
          });

          if (allResults.tests[testName].length === 0) {
            delete allResults.tests[testName];
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

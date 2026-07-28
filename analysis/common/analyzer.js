// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {mean, permutationTest, holmBonferroni} from './stats.js';
import {
  getDisplayName,
  getAggregationMode,
  matchesAggMode,
  parseDataset,
} from './parser.js';
import {importantMetricsManifest} from './important_metrics.js';

export function getBaselineTests(dataModel) {
  if (!dataModel || !dataModel.groups || dataModel.groups.length === 0) {
    return [];
  }

  return Array.from(dataModel.groups[0].metrics.keys()).sort();
}

export function getDatasetMismatches(dataModel) {
  const warnings = [];
  if (!dataModel || !dataModel.groups || dataModel.groups.length < 2) {
    return warnings;
  }

  const baselineGroup = dataModel.groups[0];
  const baselineTests = Array.from(baselineGroup.metrics.keys());

  for (let i = 1; i < dataModel.groups.length; i++) {
    const group = dataModel.groups[i];
    const groupTests = Array.from(group.metrics.keys());

    const baselineMissing = groupTests.filter(
        (test) => !baselineGroup.metrics.has(test),
    );
    const groupMissing = baselineTests.filter(
        (test) => !group.metrics.has(test),
    );

    const allMissing = [...baselineMissing, ...groupMissing].sort();

    if (allMissing.length > 0) {
      warnings.push({
        baselineName: baselineGroup.name,
        groupName: group.name,
        missingTests: allMissing,
      });
    }
  }
  return warnings;
}

export function buildDataModel(dataModel) {
  for (const group of dataModel.groups) {
    if (group._rawStrings) {
      group.metrics = parseDataset(group._rawStrings);
      delete group._rawStrings;
    }
  }
  return dataModel;
}

export function analyzeTestMetrics(testName, dataModel) {
  const groupMetrics = dataModel.groups.map(
      (group) => group.metrics.get(testName) || new Map(),
  );

  const allMetricNames = new Set();
  for (const metrics of groupMetrics) {
    for (const metricName of metrics.keys()) {
      allMetricNames.add(metricName);
    }
  }

  let results = [];

  for (const metricName of allMetricNames) {
    const groupDataList = groupMetrics.map((metrics) =>
      metrics.get(metricName),
    );
    const missingData = groupDataList.some((data) => !data);

    if (groupDataList.every((data) => !data)) {
      continue;
    }

    const displayName = getDisplayName(metricName);
    const groupValuesList = groupDataList.map((data) =>
      data ? data.values : [],
    );
    const groupMeans = groupValuesList.map((values) =>
      values.length > 0 ? mean(values) : null,
    );

    const units = groupDataList.find((data) => data != null)?.units || '';
    const improvementDirection =
      groupDataList.find((data) => data != null)?.improvement_direction || null;

    const comparisons = [];

    if (dataModel.groups.length >= 2) {
      const lMean = groupMeans[0];
      const lVals = groupValuesList[0];

      for (let i = 1; i < dataModel.groups.length; i++) {
        const rMean = groupMeans[i];
        const rVals = groupValuesList[i];
        const compMissingData = !groupDataList[0] || !groupDataList[i];
        const compInsufficientData =
          compMissingData || lVals.length < 2 || rVals.length < 2;

        let change = 0;
        let isRegression = false;
        let isImprovement = false;
        let pValue = null;

        if (!compMissingData) {
          change =
            lMean !== 0 && lMean !== null && rMean !== null ?
              (rMean - lMean) / lMean :
              0;

          if (
            improvementDirection === 'up' ||
            improvementDirection === 'HIGHER_IS_BETTER'
          ) {
            if (change < 0) isRegression = true;
            if (change > 0) isImprovement = true;
          } else if (
            improvementDirection === 'down' ||
            improvementDirection === 'LOWER_IS_BETTER'
          ) {
            if (change > 0) isRegression = true;
            if (change < 0) isImprovement = true;
          }

          if (!compInsufficientData) {
            pValue = permutationTest(lVals, rVals);
          }
        }

        comparisons.push({
          change,
          isRegression,
          isImprovement,
          pValue,
          missingData: compMissingData,
          insufficientData: compInsufficientData,
        });
      }
    }

    results.push({
      metricName: displayName,
      originalMetricName: metricName,
      aggMode: getAggregationMode(metricName),
      groupMeans,
      groupValuesList,
      comparisons,
      improvementDirection,
      missingData,
      units,
    });
  }

  if (dataModel.groups.length >= 2) {
    results = holmBonferroni(results);
  }

  return results;
}

export function filterSignificantChanges(results) {
  return results.filter((m) => {
    if (!m.comparisons || m.comparisons.length === 0) return true;
    return m.comparisons.some(
        (c) => c.significant === true || c.pValue === null,
    );
  });
}

export function getImportantMetricsForTest(testName) {
  if (!importantMetricsManifest) return [];
  const sortedBases = Object.keys(importantMetricsManifest).sort(
      (a, b) => b.length - a.length,
  );
  for (const base of sortedBases) {
    if (testName.startsWith(base)) {
      return importantMetricsManifest[base];
    }
  }
  return [];
}

export function filterMetrics(results, options = {}) {
  const {
    aggMode = 'all',
    importantMetrics = [],
    displayAll = false,
    significantOnly = false,
    searchQuery = '',
  } = options;

  let filtered = results;

  // Filter by aggMode
  if (aggMode !== 'all') {
    filtered = filtered.filter((r) => {
      const isAggregated = r.aggMode !== 'raw';
      if (isAggregated && !matchesAggMode(r.originalMetricName, aggMode)) {
        return false;
      }
      return true;
    });
  }

  // Filter by importantMetrics and handle missing metrics
  if (!displayAll && importantMetrics.length > 0) {
    const aggFilteredNames = new Set(filtered.map((r) => r.metricName));
    const finalResults = [];

    // Add missing important metrics
    for (const important of importantMetrics) {
      let found = false;
      for (const m of aggFilteredNames) {
        if (m === important || m.includes(important)) {
          found = true;
          break;
        }
      }
      if (!found) {
        finalResults.push({
          metricName: important,
          originalMetricName: important,
          missingData: true,
        });
      }
    }

    // Add existing important metrics
    for (const r of filtered) {
      let isImportant = false;
      for (let i = 0; i < importantMetrics.length; i++) {
        const important = importantMetrics[i];
        if (r.metricName === important || r.metricName.includes(important)) {
          isImportant = true;
          r.orderIndex = i;
          break;
        }
      }
      if (isImportant) {
        finalResults.push(r);
      }
    }

    finalResults.sort((a, b) => {
      if (a.orderIndex !== undefined && b.orderIndex !== undefined) {
        return a.orderIndex - b.orderIndex;
      }
      if (a.orderIndex !== undefined) return -1;
      if (b.orderIndex !== undefined) return 1;
      return a.metricName.localeCompare(b.metricName);
    });
    filtered = finalResults;
  } else {
    // Sort alphabetically if we are not forcing the important metrics order
    filtered = [...filtered];
    filtered.sort((a, b) => a.metricName.localeCompare(b.metricName));
  }

  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    filtered = filtered.filter((r) => r.metricName.toLowerCase().includes(q));
  }

  if (significantOnly) {
    filtered = filterSignificantChanges(filtered);
  }

  return filtered;
}

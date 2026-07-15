// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

export const AGG_MODES = [
  'all',
  'avg',
  'max',
  'min',
  'p50',
  'p75',
  'p90',
  'p95',
  'p99',
  'sum',
  'count',
  'stddev',
];

const UMA_PREFIXES = [
  'cuj.uma.lower_is_better-',
  'cuj.uma.higher_is_better-',
  'cuj.uma_histogram_summaries-',
];

function stripUmaPrefix(metricName) {
  for (const prefix of UMA_PREFIXES) {
    if (metricName.startsWith(prefix)) {
      return metricName.substring(prefix.length);
    }
  }
  return metricName;
}

const ALIASES = {
  mean: 'avg',
  total: 'sum',
};

const ALL_MODES = [
  ...AGG_MODES.filter((m) => m !== 'all'),
  ...Object.keys(ALIASES),
];

export function extractAggMode(metricName) {
  const displayName = stripUmaPrefix(metricName);

  for (const rawMode of ALL_MODES) {
    const canonicalMode = ALIASES[rawMode] || rawMode;

    // Check for suffix -mode
    if (displayName.endsWith('-' + rawMode)) {
      return {
        displayName: displayName.slice(0, -(rawMode.length + 1)),
        aggMode: canonicalMode,
      };
    }

    // Check for embedded mode with separators (e.g. .p50_ or .mean_)
    const match = displayName.match(new RegExp(`([.\\-_])${rawMode}([.\\-_])`));
    if (match) {
      const newName = displayName.replace(match[0], match[1]);
      return {
        displayName: newName,
        aggMode: canonicalMode,
      };
    }
  }

  return {
    displayName: displayName,
    aggMode: 'raw',
  };
}

export function getDisplayName(metricName) {
  return extractAggMode(metricName).displayName;
}

export function getAggregationMode(metricName) {
  return extractAggMode(metricName).aggMode;
}

export function matchesAggMode(metricName, mode) {
  if (mode === 'all') return true;
  return getAggregationMode(metricName) === mode;
}

export function parseDataset(jsonInput) {
  const jsonStrings = Array.isArray(jsonInput) ? jsonInput : [jsonInput];
  const map = new Map();
  map.metadata = {};

  for (const jsonString of jsonStrings) {
    if (!jsonString) continue;
    const data = JSON.parse(jsonString);

    if (data.metadata) {
      Object.assign(map.metadata, data.metadata);
    }

    if (data.metrics) {
      for (const metric of data.metrics) {
        let testName = metric.test_name || 'Unknown_Test';
        if (
          metric.variant &&
          metric.variant !== 'default' &&
          metric.variant !== ''
        ) {
          testName = `${testName} (${metric.variant})`;
        }

        if (metric.browser && !map.metadata['cr_version']) {
          map.metadata['cr_version'] = metric.browser;
        }

        if (!map.has(testName)) {
          map.set(testName, new Map());
        }
        const testMap = map.get(testName);
        const metricName = metric.metric;

        const commonMetricsPrefix = 'cuj.common-metrics.';
        if (metricName.startsWith(commonMetricsPrefix)) {
          const keyValString = metricName.substring(commonMetricsPrefix.length);
          const firstDashIdx = keyValString.indexOf('-');
          if (firstDashIdx !== -1) {
            const fullKey = keyValString.substring(0, firstDashIdx);
            const value = keyValString.substring(firstDashIdx + 1);

            const keyParts = fullKey.split('.');
            const actualKey = keyParts[keyParts.length - 1];
            map.metadata[actualKey] = value;
          } else if (metric.values && metric.values.length > 0) {
            const keyParts = keyValString.split('.');
            const actualKey = keyParts[keyParts.length - 1];
            map.metadata[actualKey] = metric.values[0];
          }
        }

        if (!testMap.has(metricName)) {
          testMap.set(metricName, {
            values: [],
            units: metric.units || '',
            improvement_direction: metric.improvement_direction || '',
          });
        }

        const vals = Array.isArray(metric.values) ?
          metric.values :
          [metric.values];
        const numericVals = vals.map(Number).filter((v) => !isNaN(v));
        testMap.get(metricName).values.push(...numericVals);
      }
    }
  }

  return map;
}

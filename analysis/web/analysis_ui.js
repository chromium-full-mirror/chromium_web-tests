// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {
  getCommonTests,
  getDatasetMismatches,
  analyzeTestMetrics,
  filterMetrics,
  getImportantMetricsForTest,
} from '../common/analyzer.js';
import {AGG_MODES} from '../common/parser.js';

export function initAnalysisDashboard(dataModel) {
  renderMetadataPanels(dataModel);
  renderWarningsPanel(dataModel);
  renderFiltersPanel(dataModel);
  renderMetricsPanel(dataModel);
}

function extractMetadata(source) {
  if (!source) {
    return {
      device: 'Unknown',
      os: 'Unknown',
      osbuild: 'Unknown',
      browser: 'Unknown',
      ram: 'Unknown',
    };
  }

  let devName = source['system_machine'] || source['system_name'] || 'Unknown';
  if (source['full_hardware_class']) {
    devName = source['full_hardware_class'];
  } else if (source['hardware_class']) {
    devName = source['hardware_class'];
  }

  if (source['android_build_fingerprint']) {
    const fp = source['android_build_fingerprint'];
    const fpParts = fp.split('/');
    if (fpParts.length >= 3) {
      devName = fpParts[2].split(':')[0];
    }
  }

  const os = source['cr_os_name'] ?
    `${source['cr_os_name']} ${source['cr_os_version'] || ''}`.trim() :
    'Unknown';

  let buildNum = 'Unknown';
  if (source['android_build_fingerprint']) {
    const fp = source['android_build_fingerprint'];
    const fpParts = fp.split('/');
    if (fpParts.length >= 4) {
      buildNum = fpParts[3];
    } else {
      buildNum = fp;
    }
  } else if (source['cr_os_version']) {
    buildNum = source['cr_os_version'];
  } else if (source['system_release']) {
    buildNum = source['system_release'];
  }

  const browser = source['cr_version'] || 'Unknown';

  let memoryGb = 'Unknown';
  if (source['system_ram_bytes'] || source['cr_physical_memory']) {
    const bytes = parseInt(
        source['system_ram_bytes'] || source['cr_physical_memory'],
        10,
    );
    if (!isNaN(bytes)) {
      const rawGb = bytes / (1024 * 1024 * 1024);
      const commonSizes = [2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 256];
      const roundedGb = Math.round(rawGb);

      let closestSize = roundedGb;
      let minDiff = 2;
      for (const size of commonSizes) {
        const diff = Math.abs(rawGb - size);
        if (diff < minDiff) {
          minDiff = diff;
          closestSize = size;
        }
      }
      memoryGb = closestSize + ' GB';
    }
  }

  return {device: devName, os, osbuild: buildNum, browser, ram: memoryGb};
}

function renderMetadataPanels(dataModel) {
  const container = document.getElementById('metadata-panels');
  if (!container) return;

  container.innerHTML = '';

  for (const group of dataModel.groups) {
    const metadata = group.metrics.metadata || {};
    const parsedMeta = extractMetadata(metadata);

    const card = document.createElement('div');
    card.className = 'card';
    card.style.flex = '1';
    card.style.minWidth = '0';

    card.innerHTML = `
            <h2 style="margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--card-border); font-size: 1.5rem;">${group.name}</h2>
            <div style="display: grid; grid-template-columns: auto 1fr; gap: 1rem 1.5rem; font-size: 1.15rem;">
                <span style="color: var(--text-secondary);">Device</span>
                <span style="font-weight: 500;">${parsedMeta.device}</span>

                <span style="color: var(--text-secondary);">OS</span>
                <span style="font-weight: 500;">${parsedMeta.os}</span>

                <span style="color: var(--text-secondary);">OS Build</span>
                <span style="font-weight: 500;">${parsedMeta.osbuild}</span>

                <span style="color: var(--text-secondary);">Browser</span>
                <span style="font-weight: 500;">${parsedMeta.browser}</span>

                <span style="color: var(--text-secondary);">RAM</span>
                <span style="font-weight: 500;">${parsedMeta.ram}</span>
            </div>
        `;

    container.appendChild(card);
  }
}

function renderWarningsPanel(dataModel) {
  const container = document.getElementById('warnings-panel');
  if (!container) return;

  const warnings = getDatasetMismatches(dataModel);

  if (warnings.length === 0) {
    container.innerHTML = '';
    return;
  }

  let html = `
        <div class="group-card" style="border: 1px solid var(--warning); padding: 0; overflow: hidden;">
            <div class="group-header" style="cursor: pointer; border-bottom: none; transition: background 0.2s; padding: 1.25rem 1.5rem; margin-bottom: 0;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'" onclick="
                const c = document.getElementById('warnings-content');
                const icon = document.getElementById('warnings-chevron');
                if (c.style.display === 'none') {
                    c.style.display = 'block';
                    icon.style.transform = 'rotate(180deg)';
                    this.style.borderBottom = '1px solid var(--card-border)';
                } else {
                    c.style.display = 'none';
                    icon.style.transform = 'rotate(0deg)';
                    this.style.borderBottom = 'none';
                }
            ">
                <div class="group-title-wrapper" style="display: flex; align-items: center; gap: 0.75rem; color: var(--warning);">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    <h3 style="margin: 0; font-size: 1.1rem; color: var(--warning);">Dataset Mismatch Warnings (${warnings.reduce((acc, w) => acc + w.missingTests.length, 0)} tests missing)</h3>
                </div>
                <svg id="warnings-chevron" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" stroke-width="2" style="transition: transform 0.2s;"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>

            <div id="warnings-content" style="display: none; padding: 1.5rem;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
    `;

  for (const w of warnings) {
    html += `
            <div>
                <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-weight: 500;">Present in ${w.groupName}, missing elsewhere:</h4>
                <div style="display: flex; flex-direction: column; gap: 0.5rem; max-height: 250px; overflow-y: auto; padding-right: 0.5rem;">
                    ${w.missingTests
      .map(
          (t) => `
                        <div style="background: rgba(255,255,255,0.03); padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.9rem; display: flex; align-items: center; gap: 0.75rem; border: 1px solid rgba(255,255,255,0.05);">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                            ${t}
                        </div>
                    `,
      )
      .join('')}
                </div>
            </div>
        `;
  }

  html += `
                </div>
            </div>
        </div>
    `;

  container.innerHTML = html;
}

function renderFiltersPanel(dataModel) {
  const container = document.getElementById('filters-panel');
  if (!container) return;

  const commonTests = getCommonTests(dataModel);

  // Read current URL params
  const urlParams = new URLSearchParams(window.location.search);
  const urlTest = urlParams.get('test');
  const urlAgg = urlParams.get('agg') || 'all';
  const urlSignificant = urlParams.get('significant') !== 'false'; // Default to true
  const urlAllMetrics = urlParams.get('all') === 'true'; // Default to false

  let initialTest = '';
  if (urlTest && commonTests.includes(urlTest)) {
    initialTest = urlTest;
  } else if (commonTests.length > 0) {
    initialTest = commonTests[0];
  }

  const html = `
        <div class="group-card" style="padding: 1.5rem; display: flex; align-items: center; gap: 2rem; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 1rem; flex: 1; min-width: 300px;">
                <label for="test-suite-select" style="font-weight: 500; font-size: 1.1rem; color: var(--text-primary); white-space: nowrap;">Test Suite</label>
                <div style="position: relative; flex: 1; max-width: 400px;">
                    <select id="test-suite-select" style="
                        width: 100%;
                        padding: 0.75rem 1rem;
                        padding-right: 2.5rem;
                        border-radius: 8px;
                        border: 1px solid var(--card-border);
                        background: rgba(255, 255, 255, 0.03);
                        color: var(--text-primary);
                        font-size: 1rem;
                        font-family: var(--font-main);
                        outline: none;
                        cursor: pointer;
                        appearance: none;
                        -webkit-appearance: none;
                    " onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='var(--card-border)'" onfocus="this.style.borderColor='#6366f1'">
                        ${commonTests.length === 0 ? '<option value="">No common tests found</option>' : ''}
                        ${commonTests.map((t) => `<option value="${t}" style="background: #1e1e2d; color: #ffffff;" ${t === initialTest ? 'selected' : ''}>${t}</option>`).join('')}
                    </select>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-secondary);">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
            </div>

            <div style="display: flex; align-items: center; gap: 1rem; min-width: 200px;">
                <label for="agg-mode-select" style="font-weight: 500; color: var(--text-primary); white-space: nowrap;">UMA Metric Aggregation</label>
                <div style="position: relative; flex: 1; max-width: 200px;">
                    <select id="agg-mode-select" style="
                        width: 100%;
                        padding: 0.75rem 1rem;
                        padding-right: 2.5rem;
                        border-radius: 8px;
                        border: 1px solid var(--card-border);
                        background: rgba(255, 255, 255, 0.03);
                        color: var(--text-primary);
                        font-size: 1rem;
                        font-family: var(--font-main);
                        outline: none;
                        cursor: pointer;
                        appearance: none;
                        -webkit-appearance: none;
                    " onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='var(--card-border)'" onfocus="this.style.borderColor='#6366f1'">
                        ${AGG_MODES.map((mode) => `<option value="${mode}" style="background: #1e1e2d; color: #ffffff;" ${mode === urlAgg ? 'selected' : ''}>${mode}</option>`).join('')}
                    </select>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-secondary);">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
            </div>

            <div style="display: flex; align-items: center; gap: 2rem;">
                <div class="tooltip-container" style="display: flex; align-items: center; gap: 0.75rem;">
                    <span class="tooltip-text">Filters to only significantly different results when enabled</span>
                    <label class="toggle-switch">
                        <input type="checkbox" id="significant-only-toggle" ${urlSignificant ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <label for="significant-only-toggle" style="font-weight: 500; color: var(--text-primary); cursor: pointer; user-select: none;">Significant Only</label>
                </div>

                <div class="tooltip-container" style="display: flex; align-items: center; gap: 0.75rem;">
                    <span class="tooltip-text">Controls whether to display all metrics for a test or only whitelisted 'top of mind' metrics</span>
                    <label class="toggle-switch">
                        <input type="checkbox" id="all-metrics-toggle" ${urlAllMetrics ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <label for="all-metrics-toggle" style="font-weight: 500; color: var(--text-primary); cursor: pointer; user-select: none;">All Metrics</label>
                </div>
            </div>
        </div>
    `;

  container.innerHTML = html;

  // Set up event listeners for URL syncing
  const testSelect = document.getElementById('test-suite-select');
  const aggSelect = document.getElementById('agg-mode-select');
  const sigToggle = document.getElementById('significant-only-toggle');
  const allToggle = document.getElementById('all-metrics-toggle');

  function updateUrlParams() {
    const url = new URL(window.location);

    if (testSelect.value) {
      url.searchParams.set('test', testSelect.value);
    } else {
      url.searchParams.delete('test');
    }

    if (aggSelect.value && aggSelect.value !== 'all') {
      url.searchParams.set('agg', aggSelect.value);
    } else {
      url.searchParams.delete('agg');
    }

    url.searchParams.set('significant', sigToggle.checked.toString());
    url.searchParams.set('all', allToggle.checked.toString());

    window.history.replaceState({}, '', url);
    renderMetricsPanel(dataModel);
  }

  testSelect.addEventListener('change', updateUrlParams);
  aggSelect.addEventListener('change', updateUrlParams);
  sigToggle.addEventListener('change', updateUrlParams);
  allToggle.addEventListener('change', updateUrlParams);

  // Set initial URL state if defaults were applied
  if (!urlTest && initialTest) {
    updateUrlParams();
  }
}

function renderMetricsPanel(dataModel) {
  const container = document.getElementById('metrics-panel');
  if (!container) return;

  const urlParams = new URLSearchParams(window.location.search);
  const testName = urlParams.get('test');
  const aggMode = urlParams.get('agg') || 'all';
  const significantOnly = urlParams.get('significant') !== 'false';
  const allMetrics = urlParams.get('all') === 'true';

  if (!testName) {
    container.innerHTML =
      '<div class="group-card" style="padding: 2rem; text-align: center; color: var(--text-secondary);">No test suite selected.</div>';
    return;
  }

  let results = analyzeTestMetrics(testName, dataModel);

  let importantMetrics = [];
  if (!allMetrics) {
    importantMetrics = getImportantMetricsForTest(testName);
  }

  results = filterMetrics(results, {
    significantOnly: significantOnly,
    displayAll: allMetrics,
    importantMetrics: importantMetrics,
    aggMode: aggMode,
  });

  if (results.length === 0) {
    container.innerHTML = `
            <div class="group-card" style="padding: 2rem; text-align: center; color: var(--text-secondary);">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="margin-bottom: 1rem; opacity: 0.5;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">No metrics to display</h3>
                <p>There are no ${significantOnly ? 'significant ' : ''}metrics matching the current filters.</p>
            </div>
        `;
    return;
  }

  const numGroups = dataModel.groups.length;

  let html = `
        <div class="group-card" style="padding: 0; overflow: hidden; display: flex; flex-direction: column;">
            <div style="overflow-x: auto; overflow-y: auto; max-height: 400px; border-bottom: 1px solid var(--card-border);">
                <table style="width: 100%; border-collapse: collapse; text-align: left; position: relative;">
                    <thead style="position: sticky; top: 0; background: #1e1e2d; z-index: 10; box-shadow: 0 1px 0 var(--card-border);">
                        <tr>
                            <th style="padding: 1rem 1.5rem; font-weight: 600; color: var(--text-secondary);">Metric</th>
                            <th style="padding: 1rem 1.5rem; font-weight: 600; color: var(--text-secondary);">Agg Mode</th>
                            ${dataModel.groups.map((g) => `<th style="padding: 1rem 1.5rem; font-weight: 600; color: var(--text-secondary);">${g.name}</th>`).join('')}
                            ${numGroups === 2 ? `<th style="padding: 1rem 1.5rem; font-weight: 600; color: var(--text-secondary);">Diff</th>` : ''}
                        </tr>
                    </thead>
                    <tbody id="metrics-table-body">
    `;

  for (let i = 0; i < results.length; i++) {
    const r = results[i];

    let rowStyle =
      'border-bottom: 1px solid var(--card-border); cursor: pointer; transition: background 0.1s;';
    if (i === results.length - 1) {
      rowStyle = 'cursor: pointer; transition: background 0.1s;';
    }

    let diffCell = '';
    if (numGroups === 2) {
      let changeText = '-';
      let changeColor = 'var(--text-secondary)';
      if (!r.missingData && !r.insufficientData && r.change !== 0) {
        const pct = (r.change * 100).toFixed(2) + '%';
        changeText = (r.change > 0 ? '+' : '') + pct;
        if (r.isImprovement) changeColor = 'var(--success)';
        if (r.isRegression) changeColor = 'var(--danger)';
      } else if (r.insufficientData) {
        changeText = 'N/A';
      }

      diffCell = `<td style="padding: 1rem 1.5rem; font-weight: 500; color: ${changeColor};">${changeText}</td>`;
    }

    const groupCells = r.groupMeans
        .map((mean) => {
          if (mean === null || isNaN(mean)) {
            return `<td style="padding: 1rem 1.5rem; color: var(--text-secondary);">-</td>`;
          }

          // Format number
          const formatted = mean.toLocaleString(undefined, {
            maximumFractionDigits: 2,
          });
          const unitText = r.units && r.units !== 'unknown' ? r.units : '';
          return `<td style="padding: 1rem 1.5rem; font-variant-numeric: tabular-nums;">${formatted} <span style="color: var(--text-secondary); font-size: 0.85rem;">${unitText}</span></td>`;
        })
        .join('');

    const aggModeDisplay =
      r.aggMode === 'raw' ?
        '' :
        `<span style="padding: 0.2rem 0.5rem; background: rgba(255,255,255,0.05); border-radius: 4px; border: 1px solid var(--card-border); font-size: 0.85rem; color: var(--text-secondary);">${r.aggMode}</span>`;

    html += `
            <tr class="metric-row" data-metric="${r.originalMetricName}" style="${rowStyle}" onmouseover="if(!this.classList.contains('selected')) this.style.background='rgba(255,255,255,0.02)'" onmouseout="if(!this.classList.contains('selected')) this.style.background='transparent'">
                <td style="padding: 1rem 1.5rem; font-weight: 500;">
                    ${r.metricName}
                    ${r.missingData ? `<span style="margin-left: 0.5rem; font-size: 0.75rem; padding: 0.1rem 0.4rem; border-radius: 4px; background: rgba(234,179,8,0.1); color: var(--warning);">Missing Data</span>` : ''}
                </td>
                <td style="padding: 1rem 1.5rem;">${aggModeDisplay}</td>
                ${groupCells}
                ${diffCell}
            </tr>
        `;
  }

  html += `
                    </tbody>
                </table>
            </div>

            <!-- Graph container below the table -->
            <div id="graph-panel" style="padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px;">
                <p style="color: var(--text-secondary); font-style: italic;">Select a metric from the table above to view graphs.</p>
            </div>
        </div>
    `;

  container.innerHTML = html;

  // Add row selection logic
  const tbody = document.getElementById('metrics-table-body');
  const rows = tbody.querySelectorAll('.metric-row');
  rows.forEach((row) => {
    row.addEventListener('click', () => {
      // Deselect all
      rows.forEach((r) => {
        r.classList.remove('selected');
        r.style.background = 'transparent';
        r.style.borderLeft = 'none';
      });
      // Select current
      row.classList.add('selected');
      row.style.background = 'rgba(99, 102, 241, 0.1)';
      row.style.borderLeft = '4px solid var(--accent)';

      const selectedMetric = row.getAttribute('data-metric');

      // Sync to URL
      const url = new URL(window.location);
      url.searchParams.set('metric', selectedMetric);
      window.history.replaceState({}, '', url);

      const resultData = results.find(
          (r) => r.originalMetricName === selectedMetric,
      );
      renderGraphPanel(resultData, dataModel);
    });
  });

  // Auto-select from URL
  const urlMetric = urlParams.get('metric');
  if (urlMetric) {
    const rowToSelect = Array.from(rows).find(
        (r) => r.getAttribute('data-metric') === urlMetric,
    );
    if (rowToSelect) {
      // Use setTimeout to allow the browser to paint before scrolling
      setTimeout(() => {
        rowToSelect.click();
        rowToSelect.scrollIntoView({block: 'center', behavior: 'smooth'});
      }, 50);
    }
  }
}

function renderGraphPanel(metricData, dataModel) {
  const graphContainer = document.getElementById('graph-panel');
  if (!graphContainer) return;

  // Reset container style for graph
  graphContainer.style.display = 'block';
  graphContainer.style.alignItems = 'initial';
  graphContainer.style.justifyContent = 'initial';

  graphContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding: 0 1rem;">
            <h3 style="color: var(--text-primary); margin: 0;">${metricData.metricName} <span style="font-size: 0.9rem; font-weight: normal; color: var(--text-secondary);">(${metricData.aggMode !== 'raw' ? metricData.aggMode : 'raw'})</span></h3>
        </div>
        <div style="display: flex; gap: 1rem; width: 100%;">
            <div id="plotly-violin-container" style="flex: 1; height: 400px; min-width: 0;"></div>
            <div id="plotly-box-container" style="flex: 1; height: 400px; min-width: 0;"></div>
        </div>
    `;

  const tracesViolin = [];
  const tracesBox = [];
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']; // Tailwind colors for groups

  for (let i = 0; i < dataModel.groups.length; i++) {
    const vals = metricData.groupValuesList[i];

    tracesViolin.push({
      y: vals,
      type: 'violin',
      name: dataModel.groups[i].name,
      box: {visible: false},
      meanline: {visible: true},
      points: 'all',
      jitter: 0.5,
      pointpos: 0,
      marker: {color: colors[i % colors.length]},
      line: {color: colors[i % colors.length]},
    });

    tracesBox.push({
      y: vals,
      type: 'box',
      name: dataModel.groups[i].name,
      boxpoints: false,
      marker: {color: colors[i % colors.length]},
      line: {color: colors[i % colors.length]},
    });
  }

  const unitString =
    metricData.units && metricData.units !== 'unknown' ? metricData.units : '';

  const commonLayout = {
    yaxis: {
      title: unitString,
      zerolinecolor: 'rgba(255,255,255,0.1)',
      gridcolor: 'rgba(255,255,255,0.05)',
      tickfont: {color: '#a0a0b0'},
      titlefont: {color: '#a0a0b0'},
    },
    xaxis: {
      tickfont: {color: '#a0a0b0'},
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {l: 60, r: 20, t: 30, b: 40},
    showlegend: false,
    hovermode: 'closest',
  };

  const config = {
    responsive: true,
    displayModeBar: true,
  };

  if (window.Plotly) {
    Plotly.newPlot(
        'plotly-violin-container',
        tracesViolin,
        {
          ...commonLayout,
          title: {
            text: 'Distribution (Violin)',
            font: {color: '#a0a0b0', size: 14},
          },
        },
        config,
    );
    Plotly.newPlot(
        'plotly-box-container',
        tracesBox,
        {
          ...commonLayout,
          title: {text: 'Quartiles (Box)', font: {color: '#a0a0b0', size: 14}},
        },
        config,
    );
  } else {
    graphContainer.innerHTML +=
      '<p style="color: var(--danger); text-align: center; margin-top: 2rem;">Plotly failed to load.</p>';
  }
}

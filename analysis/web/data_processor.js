// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {accessToken} from './auth.js';
import {buildDataModel} from '../common/analyzer.js';
import {initAnalysisDashboard} from './analysis_ui.js';

export async function processLocalFileStr(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export async function processGcsFileStr(path) {
  const url = path.replace('gs://', 'https://storage.googleapis.com/');
  const headers = {};
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;

  const response = await fetch(url, {headers});
  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: ${response.statusText}`);
  }
  return await response.text();
}

export function createProcessingItem(name) {
  const div = document.createElement('div');
  div.style.display = 'flex';
  div.style.alignItems = 'center';
  div.style.justifyContent = 'space-between';
  div.style.padding = '0.5rem';
  div.style.background = 'rgba(255,255,255,0.05)';
  div.style.borderRadius = '6px';
  div.style.fontSize = '0.9rem';

  const nameSpan = document.createElement('span');
  nameSpan.textContent = name;
  nameSpan.style.overflow = 'hidden';
  nameSpan.style.textOverflow = 'ellipsis';
  nameSpan.style.whiteSpace = 'nowrap';
  nameSpan.style.marginRight = '1rem';
  nameSpan.title = name;

  const statusDiv = document.createElement('div');
  statusDiv.className = 'loader-spinner';
  statusDiv.style.width = '16px';
  statusDiv.style.height = '16px';
  statusDiv.style.borderWidth = '2px';

  div.appendChild(nameSpan);
  div.appendChild(statusDiv);

  return {element: div, statusDiv};
}

export function markProcessingItemSuccess(uiItem) {
  uiItem.statusDiv.className = '';
  uiItem.statusDiv.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
}

export function markProcessingItemError(uiItem, errorMsg) {
  uiItem.statusDiv.className = '';
  uiItem.statusDiv.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
  uiItem.statusDiv.title = errorMsg;
}

export async function startAnalysis(config) {
  const datasetView = document.getElementById('dataset-selection-view');
  const processingSplashView = document.getElementById(
      'processing-splash-view',
  );
  const analysisView = document.getElementById('analysis-dashboard-view');
  const processingFileList = document.getElementById('processing-file-list');
  const debugOutput = document.getElementById('analysis-debug-output');

  datasetView.classList.add('hidden');
  processingSplashView.classList.remove('hidden');

  // Check if all datasets are GCS paths to update URL
  const hasLocalFiles = config.groups.some((g) => g.localFiles.length > 0);
  if (!hasLocalFiles) {
    const urlParams = new URLSearchParams();
    config.groups.forEach((g) => {
      g.gcsPaths.forEach((path) => {
        urlParams.append(g.name, path);
      });
    });
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    window.history.pushState({path: newUrl}, '', newUrl);
  }

  processingFileList.innerHTML = '';
  const finalDataModel = {groups: []};
  const allTasks = [];

  // Step 1: Fire off all downloads and track them
  for (const group of config.groups) {
    const groupResult = {
      name: group.name,
      metric_files: [],
      metrics: null,
    };
    finalDataModel.groups.push(groupResult);

    const groupJsonStrings = [];

    for (const file of group.localFiles) {
      groupResult.metric_files.push(file.name);
      const uiItem = createProcessingItem(file.name);
      processingFileList.appendChild(uiItem.element);

      const task = processLocalFileStr(file)
          .then((str) => {
            groupJsonStrings.push(str);
            markProcessingItemSuccess(uiItem);
          })
          .catch((err) => {
            console.error('Local file error:', err);
            markProcessingItemError(uiItem, err.message || err);
          });
      allTasks.push(task);
    }

    for (const path of group.gcsPaths) {
      groupResult.metric_files.push(path);
      const parts = path.split('/');
      const filename = parts[parts.length - 1] || path;
      const uiItem = createProcessingItem(filename);
      processingFileList.appendChild(uiItem.element);

      const task = processGcsFileStr(path)
          .then((str) => {
            groupJsonStrings.push(str);
            markProcessingItemSuccess(uiItem);
          })
          .catch((err) => {
            console.error('GCS file error:', err);
            markProcessingItemError(uiItem, err.message || err);
          });
      allTasks.push(task);
    }

    // We attach the strings array so we can parse it in Step 2
    groupResult._rawStrings = groupJsonStrings;
  }

  // Wait for all downloads to finish
  await Promise.allSettled(allTasks);

  // Allow UI to paint green checkmarks before parsing blocking operation
  await new Promise((r) => setTimeout(r, 100));

  // Step 2: Parse each group's strings into a unified Map
  buildDataModel(finalDataModel);

  // Transition to analysis dashboard
  setTimeout(() => {
    processingSplashView.classList.add('hidden');
    analysisView.classList.remove('hidden');
    document.getElementById('back-btn').classList.remove('hidden');

    initAnalysisDashboard(finalDataModel);

    // Output summary of parsed data
    const summary = finalDataModel.groups.map((g) => ({
      name: g.name,
      filesCount: g.metric_files.length,
      totalTestsFound: g.metrics.size,
    }));

    debugOutput.textContent = JSON.stringify(summary, null, 2);
    window.analysisDataModel = finalDataModel; // Export for console debugging if needed
  }, 800);
}

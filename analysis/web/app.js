// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {icons} from './icons.js';
import {initAuth, checkAuthStatus} from './auth.js';
import {
  initGcsBrowser,
  openGcsBrowser,
  resumeGcsBrowserIfPending,
} from './gcs_browser.js';
import {startAnalysis} from './data_processor.js';

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Auth and GCS Browser
  initAuth(() => {
    // When auth succeeds, resume whatever flow was waiting for auth
    if (resumeGcsBrowserIfPending()) return;

    if (window._pendingAnalysisConfig) {
      startAnalysis(window._pendingAnalysisConfig);
      window._pendingAnalysisConfig = null;
    }
  });

  initGcsBrowser();

  // 2. Setup Dataset UI State
  const groupsContainer = document.getElementById('groups-container');
  const addGroupBtn = document.getElementById('add-group-btn');
  const datasetView = document.getElementById('dataset-selection-view');
  const analysisView = document.getElementById('analysis-dashboard-view');
  const MAX_GROUPS = 2;

  let groups = [];
  let groupIdCounter = 0;

  function createGroupUI(initialName = null, initialPaths = []) {
    const id = groupIdCounter++;
    const isFirst = groups.length === 0;

    const groupData = {
      id,
      localFiles: [],
      gcsPaths: initialPaths,
    };
    groups.push(groupData);

    const card = document.createElement('div');
    card.className = 'group-card';
    card.id = `group-${id}`;

    card.innerHTML = `
            <div class="group-header">
                <div class="group-title-wrapper">
                    <span class="group-label">Group ${id + 1}</span>
                    <input type="text" class="group-nickname-input" placeholder="Enter Group Nickname" value="${initialName || (isFirst ? 'Control' : 'Experiment')}">
                </div>
                ${!isFirst ? `<button class="remove-group-btn" title="Remove Group">${icons.trash}</button>` : ''}
            </div>

            <div class="data-sources">
                <div class="source-section gcs-source">
                    <h3 class="source-title">${icons.cloud} Google Cloud Storage</h3>
                    <div class="gcs-input-wrapper" style="margin-top: 1rem;">
                        <button class="btn primary-btn btn-small browse-gcs-btn" style="width: 100%;">Browse Google Cloud Storage</button>
                    </div>
                    <div class="file-list gcs-file-list"></div>
                </div>

                <div class="source-section local-source">
                    <h3 class="source-title">${icons.folder} Local Files</h3>
                    <div class="drop-zone">
                        ${icons.upload}
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Drop metrics JSON files here<br>or click to browse</p>
                        <input type="file" multiple accept=".json" class="hidden file-input">
                    </div>
                    <div class="file-list local-file-list"></div>
                </div>
            </div>
        `;

    const addGroupWrapper = document.getElementById('add-group-wrapper');
    groupsContainer.insertBefore(card, addGroupWrapper);
    setupGroupEvents(card, groupData);
    if (initialPaths.length > 0) {
      renderGcsFiles(groupData, card.querySelector('.gcs-file-list'));
    }
    updateUIState();
  }

  function setupGroupEvents(card, groupData) {
    // Remove Group
    const removeBtn = card.querySelector('.remove-group-btn');
    if (removeBtn) {
      removeBtn.addEventListener('click', () => {
        card.remove();
        groups = groups.filter((g) => g.id !== groupData.id);
        updateUIState();
        updateGroupLabels();
      });
    }

    // Local Files Drag & Drop
    const dropZone = card.querySelector('.drop-zone');
    const fileInput = card.querySelector('.file-input');
    const localFileList = card.querySelector('.local-file-list');

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.closest('.source-section').classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dropZone.closest('.source-section').classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.closest('.source-section').classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files, groupData, localFileList);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        handleFiles(e.target.files, groupData, localFileList);
      }
    });

    // GCS Paths
    const gcsFileList = card.querySelector('.gcs-file-list');
    const browseGcsBtn = card.querySelector('.browse-gcs-btn');
    browseGcsBtn.addEventListener('click', () => {
      openGcsBrowser((selectedPath) => {
        const prefix = 'gs://web_tests_metrics/';
        const formattedPath = selectedPath.startsWith(prefix) ?
          selectedPath :
          `${prefix}${selectedPath}`;

        if (!groupData.gcsPaths.includes(formattedPath)) {
          groupData.gcsPaths.push(formattedPath);
          renderGcsFiles(groupData, gcsFileList);
        }
      });
    });
  }

  function handleFiles(files, groupData, listElement) {
    Array.from(files).forEach((file) => {
      if (file.name.endsWith('.json')) {
        if (!groupData.localFiles.some((f) => f.name === file.name)) {
          groupData.localFiles.push(file);
        }
      }
    });
    renderLocalFiles(groupData, listElement);
  }

  function renderLocalFiles(groupData, listElement) {
    listElement.innerHTML = '';
    groupData.localFiles.forEach((file, index) => {
      const item = document.createElement('div');
      item.className = 'file-item';
      item.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 0.5rem; overflow: hidden;">
                    <div style="flex-shrink: 0; margin-top: 2px;">${icons.file}</div>
                    <span class="file-name" title="${file.name}">${file.name}</span>
                </div>
                <div class="remove-file" data-index="${index}">${icons.x}</div>
            `;
      listElement.appendChild(item);
    });

    listElement.querySelectorAll('.remove-file').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.dataset.index);
        groupData.localFiles.splice(idx, 1);
        renderLocalFiles(groupData, listElement);
      });
    });
  }

  function renderGcsFiles(groupData, listElement) {
    listElement.innerHTML = '';
    groupData.gcsPaths.forEach((path, index) => {
      const item = document.createElement('div');
      item.className = 'file-item';
      item.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 0.5rem; overflow: hidden;">
                    <div style="flex-shrink: 0; margin-top: 2px;">${icons.cloud}</div>
                    <span class="file-name" title="${path}">${path}</span>
                </div>
                <div class="remove-file" data-index="${index}">${icons.x}</div>
            `;
      listElement.appendChild(item);
    });

    listElement.querySelectorAll('.remove-file').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.dataset.index);
        groupData.gcsPaths.splice(idx, 1);
        renderGcsFiles(groupData, listElement);
      });
    });
  }

  function updateGroupLabels() {
    const cards = groupsContainer.querySelectorAll('.group-card');
    cards.forEach((card, idx) => {
      card.querySelector('.group-label').textContent = `Group ${idx + 1}`;
    });
  }

  function updateUIState() {
    const addGroupWrapper = document.getElementById('add-group-wrapper');
    if (groups.length >= MAX_GROUPS) {
      addGroupBtn.disabled = true;
      addGroupWrapper.title = 'Currently only 2 groups are supported.';
    } else {
      addGroupBtn.disabled = false;
      addGroupWrapper.title = '';
    }
  }

  addGroupBtn.addEventListener('click', () => {
    if (groups.length < MAX_GROUPS) {
      createGroupUI();
    }
  });

  document.getElementById('continue-btn').addEventListener('click', () => {
    const analysisConfig = {groups: []};
    let hasData = false;

    groups.forEach((groupData, idx) => {
      const card = document.getElementById(`group-${groupData.id}`);
      const nameInput = card.querySelector('.group-nickname-input');
      const groupName = nameInput.value.trim() || `Group ${idx + 1}`;

      if (groupData.gcsPaths.length > 0 || groupData.localFiles.length > 0) {
        hasData = true;
        analysisConfig.groups.push({
          name: groupName,
          gcsPaths: [...groupData.gcsPaths],
          localFiles: [...groupData.localFiles],
        });
      }
    });

    if (!hasData) {
      alert(
          'Please add at least one dataset (GCS path or local file) before continuing.',
      );
      return;
    }

    const needsAuth = analysisConfig.groups.some((g) => g.gcsPaths.length > 0);
    if (needsAuth && !checkAuthStatus()) {
      document.getElementById('auth-modal').classList.remove('hidden');
      window._pendingAnalysisConfig = analysisConfig;
      return;
    }

    startAnalysis(analysisConfig);
  });

  document.getElementById('back-btn').addEventListener('click', () => {
    analysisView.classList.add('hidden');
    datasetView.classList.remove('hidden');
    document.getElementById('back-btn').classList.add('hidden');
  });

  // 3. Process URL Params
  function checkUrlParams() {
    const params = new URLSearchParams(window.location.search);
    let hasData = false;

    for (const key of new Set(params.keys())) {
      if (groups.length >= MAX_GROUPS) break;

      const paths = [...new Set(params.getAll(key))];
      if (paths.length > 0) {
        hasData = true;
        createGroupUI(key, paths);
      }
    }

    if (hasData) {
      document.getElementById('continue-btn').click();
    } else {
      createGroupUI();
    }
  }

  checkUrlParams();

  // Expose to window so we can trigger programmatically if needed in console
  window.startAnalysis = startAnalysis;
});

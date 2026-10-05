// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {accessToken, checkAuthStatus} from './auth.js';

let currentGcsPrefix = '';
let onGcsSelectCallback = null;

// Multi-select state. Selections are full object names and persist while the
// modal is open, so files from several folders can be added in one go.
const selectedPaths = new Set();
let visibleFiles = []; // Object names currently listed (after filter).
let lastClickedIndex = -1; // Anchor for shift+click range selection.

export function openGcsBrowser(callback) {
  const authModal = document.getElementById('auth-modal');
  if (!checkAuthStatus()) {
    window._pendingGcsCallback = callback;
    authModal.classList.remove('hidden');
    return;
  }
  onGcsSelectCallback = callback;
  selectedPaths.clear();
  lastClickedIndex = -1;
  const filterInput = document.getElementById('gcs-filter-input');
  if (filterInput) filterInput.value = '';
  updateSelectionUi();
  document.getElementById('gcs-browser-modal').classList.remove('hidden');
  currentGcsPrefix = '';
  renderGcsBrowser(currentGcsPrefix);
}

export function resumeGcsBrowserIfPending() {
  if (window._pendingGcsCallback) {
    openGcsBrowser(window._pendingGcsCallback);
    window._pendingGcsCallback = null;
    return true;
  }
  return false;
}

function closeGcsBrowser() {
  document.getElementById('gcs-browser-modal').classList.add('hidden');
}

function commitSelection(paths) {
  closeGcsBrowser();
  if (!onGcsSelectCallback) return;
  for (const path of [...paths].sort()) onGcsSelectCallback(path);
}

export function initGcsBrowser() {
  const gcsUpBtn = document.getElementById('gcs-up-btn');
  const gcsCloseBtn = document.getElementById('gcs-close-btn');
  const addBtn = document.getElementById('gcs-add-selected-btn');
  const selectAllBtn = document.getElementById('gcs-select-all-btn');
  const clearBtn = document.getElementById('gcs-clear-selection-btn');
  const filterInput = document.getElementById('gcs-filter-input');

  gcsCloseBtn.addEventListener('click', closeGcsBrowser);

  gcsUpBtn.addEventListener('click', () => {
    const parts = currentGcsPrefix.split('/').filter(Boolean);
    parts.pop();
    currentGcsPrefix = parts.length > 0 ? parts.join('/') + '/' : '';
    renderGcsBrowser(currentGcsPrefix);
  });

  addBtn.addEventListener('click', () => {
    if (selectedPaths.size > 0) commitSelection(selectedPaths);
  });

  selectAllBtn.addEventListener('click', () => {
    for (const name of visibleFiles) selectedPaths.add(name);
    syncRowStates();
  });

  clearBtn.addEventListener('click', () => {
    selectedPaths.clear();
    syncRowStates();
  });

  filterInput.addEventListener('input', () => {
    lastClickedIndex = -1;
    applyFilter();
  });
  filterInput.addEventListener('keydown', (e) => {
    // Enter in the filter box: select all matches and add them.
    if (e.key === 'Enter' && visibleFiles.length > 0) {
      for (const name of visibleFiles) selectedPaths.add(name);
      commitSelection(selectedPaths);
    }
  });
}

function updateSelectionUi() {
  const addBtn = document.getElementById('gcs-add-selected-btn');
  const countEl = document.getElementById('gcs-selection-count');
  if (!addBtn || !countEl) return;
  const n = selectedPaths.size;
  addBtn.disabled = n === 0;
  addBtn.textContent = n > 0 ? `Add ${n} file${n === 1 ? '' : 's'}` : 'Add';
  countEl.textContent = n > 0 ? `${n} selected` : '';
}

function syncRowStates() {
  const list = document.getElementById('gcs-browser-list');
  list.querySelectorAll('.gcs-item.file').forEach((row) => {
    const selected = selectedPaths.has(row.dataset.name);
    row.classList.toggle('selected', selected);
    const cb = row.querySelector('input[type="checkbox"]');
    if (cb) cb.checked = selected;
  });
  updateSelectionUi();
}

function applyFilter() {
  const filterInput = document.getElementById('gcs-filter-input');
  const q = (filterInput?.value || '').trim().toLowerCase();
  const list = document.getElementById('gcs-browser-list');
  visibleFiles = [];
  list.querySelectorAll('.gcs-item').forEach((row) => {
    const label = (row.dataset.label || '').toLowerCase();
    const match = !q || label.includes(q);
    row.style.display = match ? '' : 'none';
    if (match && row.classList.contains('file')) {
      visibleFiles.push(row.dataset.name);
    }
  });
  const selectAllBtn = document.getElementById('gcs-select-all-btn');
  if (selectAllBtn) {
    selectAllBtn.textContent = q ?
      `Select ${visibleFiles.length} matching` :
      `Select all (${visibleFiles.length})`;
    selectAllBtn.disabled = visibleFiles.length === 0;
  }
}

function onFileRowClick(e, name) {
  const idx = visibleFiles.indexOf(name);
  if (e.shiftKey && lastClickedIndex >= 0 && idx >= 0) {
    // Shift+click: set the whole range to the state of the clicked row.
    const target = !selectedPaths.has(name);
    const [from, to] = [lastClickedIndex, idx].sort((a, b) => a - b);
    for (let i = from; i <= to; i++) {
      if (target) selectedPaths.add(visibleFiles[i]);
      else selectedPaths.delete(visibleFiles[i]);
    }
  } else if (selectedPaths.has(name)) {
    selectedPaths.delete(name);
  } else {
    selectedPaths.add(name);
  }
  lastClickedIndex = idx;
  syncRowStates();
}

async function listGcsPrefix(prefix) {
  // Follow nextPageToken so folders with >1000 objects are fully listed.
  const prefixes = [];
  const items = [];
  let pageToken = '';
  do {
    const url =
      `https://storage.googleapis.com/storage/v1/b/web_tests_metrics/o` +
      `?delimiter=/&prefix=${encodeURIComponent(prefix)}` +
      (pageToken ? `&pageToken=${encodeURIComponent(pageToken)}` : '');
    const response = await fetch(url, {
      headers: {Authorization: `Bearer ${accessToken}`},
    });
    if (!response.ok) throw new Error('Failed to fetch GCS list');
    const data = await response.json();
    if (data.prefixes) prefixes.push(...data.prefixes);
    if (data.items) items.push(...data.items);
    pageToken = data.nextPageToken || '';
  } while (pageToken);
  return {prefixes, items};
}

async function renderGcsBrowser(prefix) {
  const gcsBrowserList = document.getElementById('gcs-browser-list');
  const gcsUpBtn = document.getElementById('gcs-up-btn');
  const gcsCurrentPath = document.getElementById('gcs-current-path');

  gcsBrowserList.innerHTML = '<div style="padding:1rem;">Loading...</div>';
  gcsUpBtn.disabled = !prefix;
  gcsCurrentPath.textContent = '/' + prefix;
  visibleFiles = [];
  lastClickedIndex = -1;

  try {
    const data = await listGcsPrefix(prefix);
    gcsBrowserList.innerHTML = '';

    for (const p of data.prefixes) {
      const div = document.createElement('div');
      div.className = 'gcs-item folder';
      div.textContent = p.slice(prefix.length);
      div.dataset.label = p.slice(prefix.length);
      div.addEventListener('click', () => {
        currentGcsPrefix = p;
        renderGcsBrowser(currentGcsPrefix);
      });
      gcsBrowserList.appendChild(div);
    }

    for (const item of data.items) {
      if (item.name.endsWith('/')) continue;
      const label = item.name.slice(prefix.length);
      const div = document.createElement('div');
      div.className = 'gcs-item file';
      div.dataset.name = item.name;
      div.dataset.label = label;
      div.title =
        'Click to select, Shift+click for a range, ' +
        'double-click to add immediately';

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.tabIndex = -1;
      // The row handles clicks; keep the checkbox purely visual.
      cb.style.pointerEvents = 'none';
      const span = document.createElement('span');
      span.textContent = label;
      div.append(cb, span);

      div.addEventListener('mousedown', (e) => {
        if (e.shiftKey) e.preventDefault(); // Avoid text selection.
      });
      div.addEventListener('click', (e) => onFileRowClick(e, item.name));
      div.addEventListener('dblclick', () => commitSelection([item.name]));
      gcsBrowserList.appendChild(div);
    }

    if (data.prefixes.length === 0 && data.items.length === 0) {
      gcsBrowserList.innerHTML =
        '<div style="padding:1rem; color:var(--text-secondary);">Empty directory</div>';
    }
    applyFilter();
    syncRowStates();
  } catch (e) {
    console.error(e);
    gcsBrowserList.innerHTML = `<div style="padding:1rem; color:var(--danger);">Error loading directory. Check console.</div>`;
  }
}

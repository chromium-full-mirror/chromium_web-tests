// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {accessToken, checkAuthStatus} from './auth.js';

let currentGcsPrefix = '';
let onGcsSelectCallback = null;

export function openGcsBrowser(callback) {
  const authModal = document.getElementById('auth-modal');
  if (!checkAuthStatus()) {
    window._pendingGcsCallback = callback;
    authModal.classList.remove('hidden');
    return;
  }
  onGcsSelectCallback = callback;
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

export function initGcsBrowser() {
  const gcsBrowserModal = document.getElementById('gcs-browser-modal');
  const gcsUpBtn = document.getElementById('gcs-up-btn');
  const gcsCloseBtn = document.getElementById('gcs-close-btn');

  gcsCloseBtn.addEventListener('click', () =>
    gcsBrowserModal.classList.add('hidden'),
  );

  gcsUpBtn.addEventListener('click', () => {
    const parts = currentGcsPrefix.split('/').filter(Boolean);
    parts.pop();
    currentGcsPrefix = parts.length > 0 ? parts.join('/') + '/' : '';
    renderGcsBrowser(currentGcsPrefix);
  });
}

async function renderGcsBrowser(prefix) {
  const gcsBrowserList = document.getElementById('gcs-browser-list');
  const gcsUpBtn = document.getElementById('gcs-up-btn');
  const gcsCurrentPath = document.getElementById('gcs-current-path');
  const gcsBrowserModal = document.getElementById('gcs-browser-modal');

  gcsBrowserList.innerHTML = '<div style="padding:1rem;">Loading...</div>';
  gcsUpBtn.disabled = !prefix;
  gcsCurrentPath.textContent = '/' + prefix;

  try {
    const response = await fetch(
        `https://storage.googleapis.com/storage/v1/b/web_tests_metrics/o?delimiter=/&prefix=${encodeURIComponent(prefix)}`,
        {headers: {Authorization: `Bearer ${accessToken}`}},
    );

    if (!response.ok) throw new Error('Failed to fetch GCS list');

    const data = await response.json();
    gcsBrowserList.innerHTML = '';

    if (data.prefixes) {
      data.prefixes.forEach((p) => {
        const div = document.createElement('div');
        div.className = 'gcs-item folder';
        div.textContent = p.slice(prefix.length);
        div.addEventListener('click', () => {
          currentGcsPrefix = p;
          renderGcsBrowser(currentGcsPrefix);
        });
        gcsBrowserList.appendChild(div);
      });
    }

    if (data.items) {
      data.items.forEach((item) => {
        if (item.name.endsWith('/')) return;
        const div = document.createElement('div');
        div.className = 'gcs-item file';
        div.textContent = item.name.slice(prefix.length);
        div.addEventListener('click', () => {
          gcsBrowserModal.classList.add('hidden');
          if (onGcsSelectCallback) onGcsSelectCallback(item.name);
        });
        gcsBrowserList.appendChild(div);
      });
    }

    if (!data.prefixes && !data.items) {
      gcsBrowserList.innerHTML =
        '<div style="padding:1rem; color:var(--text-secondary);">Empty directory</div>';
    }
  } catch (e) {
    console.error(e);
    gcsBrowserList.innerHTML = `<div style="padding:1rem; color:var(--danger);">Error loading directory. Check console.</div>`;
  }
}

// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {initializeApp} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

const firebaseConfig = {
  apiKey: 'AIzaSyC7LAuDn_RzBAUrQbSqPXVduU3ibk_6nVA',
  authDomain: 'chromium-workloads.firebaseapp.com',
  projectId: 'chromium-workloads',
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export let accessToken = sessionStorage.getItem('gcs_access_token');
export let tokenExpiry = sessionStorage.getItem('gcs_token_expiry');

export function checkAuthStatus() {
  const authBtn = document.getElementById('auth-btn');
  if (accessToken && tokenExpiry && Date.now() < parseInt(tokenExpiry)) {
    authBtn.textContent = 'Authenticated';
    authBtn.classList.remove('secondary-btn');
    authBtn.classList.add('primary-btn');
    authBtn.style.backgroundColor = '#16a34a';
    authBtn.style.borderColor = '#16a34a';
    authBtn.disabled = true;
    return true;
  }
  return false;
}

export function initAuth(onAuthSuccess) {
  const authBtn = document.getElementById('auth-btn');
  const modalAuthBtn = document.getElementById('modal-auth-btn');
  const authModal = document.getElementById('auth-modal');

  checkAuthStatus();

  function triggerAuth() {
    const provider = new GoogleAuthProvider();
    // This scope is required to read metrics from Google Cloud Storage
    provider.addScope('https://www.googleapis.com/auth/cloud-platform');

    provider.setCustomParameters({
      prompt: 'select_account',
    });

    signInWithPopup(auth, provider)
        .then((result) => {
          const credential = GoogleAuthProvider.credentialFromResult(result);
          if (credential && credential.accessToken) {
            accessToken = credential.accessToken;
            // Google OAuth access tokens typically expire in 1 hour
            const expiry = Date.now() + 3600 * 1000;
            tokenExpiry = expiry;

            sessionStorage.setItem('gcs_access_token', accessToken);
            sessionStorage.setItem('gcs_token_expiry', expiry);

            checkAuthStatus();
            if (authModal) authModal.classList.add('hidden');

            if (onAuthSuccess) onAuthSuccess();
          }
        })
        .catch((error) => {
          console.error('Firebase Authentication failed:', error);
          alert('Authentication failed: ' + error.message);
        });
  }

  if (authBtn) authBtn.addEventListener('click', triggerAuth);
  if (modalAuthBtn) modalAuthBtn.addEventListener('click', triggerAuth);
}

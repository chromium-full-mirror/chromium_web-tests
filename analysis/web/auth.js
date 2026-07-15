// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

export let accessToken = sessionStorage.getItem('gcs_access_token');
export let tokenExpiry = sessionStorage.getItem('gcs_token_expiry');
let tokenClient;

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

  window.onload = function() {
    tokenClient = google.accounts.oauth2.initTokenClient({
      client_id:
        '1047313083844-qtid5mdtu0fpa1d0m4or9aigma4t92ab.apps.googleusercontent.com',
      scope: 'https://www.googleapis.com/auth/cloud-platform',
      callback: (tokenResponse) => {
        if (tokenResponse && tokenResponse.access_token) {
          accessToken = tokenResponse.access_token;
          const expiry = Date.now() + tokenResponse.expires_in * 1000;
          tokenExpiry = expiry;
          sessionStorage.setItem('gcs_access_token', accessToken);
          sessionStorage.setItem('gcs_token_expiry', expiry);

          checkAuthStatus();
          authModal.classList.add('hidden');

          if (onAuthSuccess) onAuthSuccess();
        }
      },
    });
  };

  function triggerAuth() {
    if (tokenClient) {
      tokenClient.requestAccessToken();
    } else {
      alert(
          'Google Identity Service is still loading. Please try again in a moment.',
      );
    }
  }

  authBtn.addEventListener('click', triggerAuth);
  modalAuthBtn.addEventListener('click', triggerAuth);
}

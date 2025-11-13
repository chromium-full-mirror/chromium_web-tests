// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
const video = document.querySelector('video');

// Fail the test if the necessary playback duration was not achieved
if (video.currentTime < PLAYBACK_DURATION) {
  throw new Error('Video did not finish playing.');
}

const quality = video.getVideoPlaybackQuality();

performance.mark('playback-stats', {
  detail: {
    currentTime: video.currentTime,
    videoHeight: video.videoHeight,
    videoWidth: video.videoWidth,
    totalVideoFrames: quality.totalVideoFrames,
    droppedVideoFrames: quality.droppedVideoFrames,
  },
});

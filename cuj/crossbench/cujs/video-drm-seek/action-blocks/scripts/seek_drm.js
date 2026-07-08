// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

const file = 'FILE_NAME';
const numSeeks = NUM_SEEK;

globalThis.seekCount = 0;

/**
 * Generates a predictable pseudo-random sequence of numbers given a seed.
 * @param {number} seed
 * @return {function(): number}
 */
function randomizer(seed) {
  return function() {
    const x = Math.sin(seed++) * 10000;
    return x - Math.floor(x);
  };
}

const random = randomizer(1);

/**
 * Plays a DRM-protected video using Shaka Player, waits for playback to start,
 * and then performs a series of random seeks, recording performance marks.
 * @param {string} mpdPath The path to the MPD file for the video stream.
 */
async function seekDrmPlayback(mpdPath) {
  const video = document.getElementById('video');
  if (!video) throw new Error('Video element not found');

  const waitForEvent = (eventName) => {
    return new Promise((resolve, reject) => {
      const onEvent = () => {
        cleanup();
        resolve();
      };

      const onError = (e) => {
        cleanup();
        reject(
            new Error(
                `Video error waiting for ${eventName}: ` +
              `${video.error ? video.error.message : e}`,
            ),
        );
      };

      const cleanup = () => {
        video.removeEventListener(eventName, onEvent);
        video.removeEventListener('error', onError);
      };

      video.addEventListener(eventName, onEvent);
      video.addEventListener('error', onError);
    });
  };

  let numberFinishedSeeks = 0;

  const randomSeek = () => {
    return new Promise((resolve, reject) => {
      video.onseeked = (event) => {
        console.log(numberFinishedSeeks);
        resolve(numberFinishedSeeks++);
      };
      video.onerror = (event) => {
        reject(
            new Error(
                'onerror event message: ' +
              (event.message || '') +
              ', video.error.message: ' +
              (video.error ? video.error.message : ''),
            ),
        );
      };
      video.currentTime = random() * video.duration;
    });
  };

  // Start playback.
  console.log(`Starting playback for ${mpdPath}`);
  const playbackPromise = play_shaka_drm(mpdPath);

  console.log('Waiting for playing event...');
  try {
    await Promise.race([waitForEvent('playing'), playbackPromise]);
  } catch (err) {
    throw new Error(`Playback failed to start: ${err}`);
  }

  // Wait 3s to ensure player stabilizes before starting seeks.
  console.log('Waiting 3 seconds before seeking...');
  await new Promise((r) => setTimeout(r, 3000));

  console.log(`Starting seek loop, target number of seeks: ${numSeeks}`);
  performance.mark('test-config', {
    detail: {
      numTargetSeeks: numSeeks,
    },
  });

  for (let i = 0; i < numSeeks; i++) {
    performance.mark(`randomSeek-${i}-start`);
    console.log(`Starting Seek number: ${i}`);
    try {
      globalThis.seekCount = await randomSeek();
      console.log(`Returned seek count: ${globalThis.seekCount}`);
      performance.mark(`randomSeek-${i}-end`);
      performance.measure(
          `randomSeek-${i}-duration`,
          `randomSeek-${i}-start`,
          `randomSeek-${i}-end`,
      );
    } catch (error) {
      console.error(`\nError while seeking: ${error.message}`);
      console.error(
          `Completed ${globalThis.seekCount}/${numSeeks} seeks before failure.`,
      );
      break;
    }

    if (globalThis.seekCount + 1 >= numSeeks) {
      console.log(`Early exit: ${globalThis.seekCount}`);
      break;
    }
  }

  return;
}

await seekDrmPlayback(file);

console.log('DRM Seek playback verification passed.');

// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

function frameURL(num) {
  return `https://chromium-workloads-${num}.web.app/web-tests/main/cuj/crossbench/cujs/tab-stress/multiprocess`;
}

// Replaced by crossbench
const num_frames = NUM_FRAMES;

// Create elements to hold all the iframes.
for (let i = 0; i < num_frames; ++i) {
  let element = document.createElement("span");

  frame = document.createElement("iframe");
  frame.width = 500;
  frame.height = 500;
  element.appendChild(frame);
  frame.src = frameURL(i)

  document.body.appendChild(element);
}
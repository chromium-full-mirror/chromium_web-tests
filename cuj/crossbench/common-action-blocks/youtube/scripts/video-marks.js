performance.mark("video-loaded-start")
performance.mark("switch-resolution-start")
// Add a one-time listener for the video canplay event,
// mark the resolution switching video loading time
const video = document.querySelector("video")
video.addEventListener("canplay", () => {
  performance.mark("video-loaded-end")
  performance.measure("video-ready", "video-loaded-start", "video-loaded-end")
}, { once: true });
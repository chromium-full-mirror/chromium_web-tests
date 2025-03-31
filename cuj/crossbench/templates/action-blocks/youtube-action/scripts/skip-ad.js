let observer = null
const skipAd = async () => {
  const adVideo = document.querySelector(".ad-showing video")
  if (adVideo) {
    if (adVideo.paused) {
      adVideo.play()
    }
    if (isFinite(adVideo.duration) && adVideo.currentTime != adVideo.duration) {
      adVideo.currentTime = adVideo.duration
      performance.mark("skip-ad-executed")
    }
  } else if (document.querySelector("$[VIDEO_SELECTOR]")) {
    return
  }
  await new Promise(resolve => setTimeout(resolve, 2000));
  await skipAd()
}
await skipAd()
const checkVideoEnd = async () => {
  const video = document.querySelector("video");
  if (!video || video.paused || video.ended) {
    return;
  }
  await new Promise(resolve => setTimeout(resolve, 1000));
  await checkVideoEnd();
}
// Block and wait for the video to play until the expected playback time.
await checkVideoEnd();
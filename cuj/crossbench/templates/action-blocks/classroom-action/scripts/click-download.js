performance.mark("download-click-start")
window.addEventListener('click', () => {
  const downloadButton = document.querySelector("$[DOWNLOAD_CLICK_SELECTOR]")
  if (downloadButton) {
    performance.mark('download-click-end')
    performance.measure(
      'download-click-duration',
      'download-click-start',
      'download-click-end'
    )
  }
})
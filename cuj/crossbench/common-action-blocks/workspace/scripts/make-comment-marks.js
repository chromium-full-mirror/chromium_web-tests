// Before we click the comment button, set up an observer to log exactly
// when the comment window appears.
(new MutationObserver((mutationList, observer) => {
  if (document.querySelector("#docos-stream-view [aria-label='Comment draft']")) {
    performance.mark("comment-opened-dom");
    observer.disconnect();
    requestAnimationFrame(() => {
      performance.mark("comment-opened-next-frame");
      performance.measure('comment-opened', 'comment-click', 'comment-opened-next-frame');
    });
  } else {
    performance.mark("comment-progress");
  }
})).observe(
  document.querySelector("#docos-stream-view"),
  { subtree: true, attributes: true },
);

performance.mark('comment-click');
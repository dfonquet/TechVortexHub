(function () {
  var supportsHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!supportsHover || prefersReducedMotion) {
    return;
  }

  document.addEventListener("pointermove", function (event) {
    document.documentElement.style.setProperty("--ambient-x", event.clientX + "px");
    document.documentElement.style.setProperty("--ambient-y", event.clientY + "px");
  });

  var cards = document.querySelectorAll(".post-card");

  cards.forEach(function (card) {
    card.addEventListener("pointermove", function (event) {
      var rect = card.getBoundingClientRect();
      card.style.setProperty("--spotlight-x", event.clientX - rect.left + "px");
      card.style.setProperty("--spotlight-y", event.clientY - rect.top + "px");
    });

    card.addEventListener("pointerleave", function () {
      card.style.removeProperty("--spotlight-x");
      card.style.removeProperty("--spotlight-y");
    });
  });
})();

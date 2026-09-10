(function () {
  var header = document.querySelector(".site-header");
  var links = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'));
  var sections = Array.from(document.querySelectorAll("main > section[id]"));
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var scheduled = false;

  function updateNavigation() {
    var offset = header.getBoundingClientRect().height + 24;
    document.documentElement.style.setProperty("--header-offset", offset + "px");
    var active = sections[0];
    sections.forEach(function (section) {
      if (section.getBoundingClientRect().top <= offset + 40) active = section;
    });
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) {
      active = sections[sections.length - 1];
    }
    links.forEach(function (link) {
      if (link.hash === "#" + active.id) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    scheduled = false;
  }
  function scheduleUpdate() {
    if (!scheduled) {
      scheduled = true;
      window.requestAnimationFrame(updateNavigation);
    }
  }
  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate);
  window.addEventListener("hashchange", scheduleUpdate);
  if ("ResizeObserver" in window) new ResizeObserver(scheduleUpdate).observe(header);
  updateNavigation();

  if (!reducedMotion.matches && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll("[data-reveal]").forEach(function (element) {
      observer.observe(element);
    });
  }
})();

// Article interactions: back-to-top button and image lightbox behavior.
document.addEventListener("DOMContentLoaded", function () {
  const backToTopButton = document.querySelector(".back-to-top");
  const lightbox = document.querySelector("#imageLightbox");
  const lightboxImage = document.querySelector(".lightbox-image");
  const lightboxCaption = document.querySelector(".lightbox-caption");
  const lightboxClose = document.querySelector(".lightbox-close");
  const articleImages = document.querySelectorAll(".article-cover img, .article-image img");

  function toggleBackToTop() {
    if (!backToTopButton) return;

    if (window.scrollY > 420) {
      backToTopButton.classList.add("is-visible");
    } else {
      backToTopButton.classList.remove("is-visible");
    }
  }

  function openLightbox(image) {
    if (!lightbox || !lightboxImage || !lightboxCaption) return;

    const figure = image.closest("figure");
    const caption = figure?.querySelector("figcaption")?.textContent || image.alt || "Article image";

    lightboxImage.src = image.currentSrc || image.src;
    lightboxImage.alt = image.alt || caption;
    lightboxCaption.textContent = caption;

    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.classList.add("lightbox-open");
  }

  function closeLightbox() {
    if (!lightbox || !lightboxImage) return;

    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.classList.remove("lightbox-open");
    lightboxImage.src = "";
  }

  window.addEventListener("scroll", toggleBackToTop, { passive: true });

  backToTopButton?.addEventListener("click", function () {
    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  });

  articleImages.forEach(function (image) {
    image.addEventListener("click", function () {
      openLightbox(image);
    });
  });

  lightboxClose?.addEventListener("click", closeLightbox);

  lightbox?.addEventListener("click", function (event) {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeLightbox();
    }
  });

  toggleBackToTop();
});
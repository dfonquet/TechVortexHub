// Article interactions: back-to-top button, image lightbox, and command copy behavior.
document.addEventListener("DOMContentLoaded", function () {
  const backToTopButton = document.querySelector(".back-to-top");
  const lightbox = document.querySelector("#imageLightbox");
  const lightboxImage = document.querySelector(".lightbox-image");
  const lightboxCaption = document.querySelector(".lightbox-caption");
  const lightboxClose = document.querySelector(".lightbox-close");
  const articleImages = document.querySelectorAll(".article-cover img, .article-image img");
  const copyButtons = document.querySelectorAll(".copy-command");

  function toggleBackToTop() {
    if (!backToTopButton) return;

    backToTopButton.classList.toggle("is-visible", window.scrollY > 420);
  }

  function getImageCaption(image) {
    const figure = image.closest("figure");
    const caption = figure?.querySelector("figcaption")?.textContent;

    return caption || image.alt || "Article image";
  }

  function openLightbox(image) {
    if (!lightbox || !lightboxImage || !lightboxCaption) return;

    const caption = getImageCaption(image);

    lightboxImage.src = image.currentSrc || image.src;
    lightboxImage.alt = image.alt || caption;
    lightboxCaption.textContent = caption;

    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.classList.add("lightbox-open");
  }

  function closeLightbox() {
    if (!lightbox || !lightboxImage || !lightboxCaption) return;

    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.classList.remove("lightbox-open");

    lightboxImage.src = "";
    lightboxImage.alt = "";
    lightboxCaption.textContent = "";
  }

  function fallbackCopyText(text) {
    const textarea = document.createElement("textarea");

    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";

    document.body.appendChild(textarea);
    textarea.select();

    const copied = document.execCommand("copy");
    document.body.removeChild(textarea);

    return copied;
  }

  async function copyText(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }

      return fallbackCopyText(text);
    } catch (error) {
      return fallbackCopyText(text);
    }
  }

  function prepareArticleImages() {
    articleImages.forEach(function (image) {
      image.setAttribute("role", "button");
      image.setAttribute("tabindex", "0");
      image.setAttribute("title", "Open image preview");

      image.addEventListener("click", function () {
        openLightbox(image);
      });

      image.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openLightbox(image);
        }
      });
    });
  }

  function prepareCopyButtons() {
    copyButtons.forEach(function (button) {
      button.addEventListener("click", async function () {
        const textToCopy = button.dataset.copy;
        const originalText = button.textContent;

        if (!textToCopy) return;

        const copied = await copyText(textToCopy);

        button.textContent = copied ? "Copied" : "Error";
        button.classList.toggle("is-copied", copied);

        setTimeout(function () {
          button.textContent = originalText;
          button.classList.remove("is-copied");
        }, 1400);
      });
    });
  }

  window.addEventListener("scroll", toggleBackToTop, { passive: true });

  backToTopButton?.addEventListener("click", function () {
    window.scrollTo({
      top: 0,
      behavior: "smooth"
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

  prepareArticleImages();
  prepareCopyButtons();
  toggleBackToTop();
});
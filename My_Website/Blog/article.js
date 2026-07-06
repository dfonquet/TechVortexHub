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

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeLightbox();
    }
  });

  toggleBackToTop();
});
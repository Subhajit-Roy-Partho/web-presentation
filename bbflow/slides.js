(function () {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const laserBtn = document.getElementById("laserBtn");
  const fullscreenBtn = document.getElementById("fullscreenBtn");
  const helpBtn = document.getElementById("helpBtn");
  const closeHelp = document.getElementById("closeHelp");
  const helpOverlay = document.getElementById("helpOverlay");
  const slideNumber = document.getElementById("slideNumber");
  const slideTotal = document.getElementById("slideTotal");
  const progressBar = document.getElementById("progressBar");
  const laserDot = document.getElementById("laser-dot");

  let current = getInitialSlideIndex();
  let laserOn = false;

  slideTotal.textContent = String(slides.length);
  showSlide(current, { replaceHash: true });

  prevBtn.addEventListener("click", previousSlide);
  nextBtn.addEventListener("click", nextSlide);
  laserBtn.addEventListener("click", toggleLaser);
  fullscreenBtn.addEventListener("click", toggleFullscreen);
  helpBtn.addEventListener("click", openHelp);
  closeHelp.addEventListener("click", closeHelpOverlay);
  helpOverlay.addEventListener("click", (event) => {
    if (event.target === helpOverlay) closeHelpOverlay();
  });

  document.addEventListener("keydown", handleKeydown);
  document.addEventListener("mousemove", updateLaser);
  window.addEventListener("hashchange", () => {
    const index = getInitialSlideIndex();
    if (index !== current) showSlide(index, { replaceHash: true });
  });

  function getInitialSlideIndex() {
    const match = window.location.hash.match(/slide-(\d+)/);
    if (!match) return 0;
    const parsed = Number(match[1]) - 1;
    if (Number.isNaN(parsed)) return 0;
    return clamp(parsed, 0, slides.length - 1);
  }

  function showSlide(index, options = {}) {
    current = clamp(index, 0, slides.length - 1);
    slides.forEach((slide, slideIndex) => {
      slide.classList.toggle("active", slideIndex === current);
      slide.setAttribute("aria-hidden", slideIndex === current ? "false" : "true");
    });

    slideNumber.textContent = String(current + 1);
    progressBar.style.width = `${((current + 1) / slides.length) * 100}%`;
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === slides.length - 1;

    const title = slides[current].dataset.title || `Slide ${current + 1}`;
    document.title = `${current + 1}/${slides.length} - ${title} - BBFlow`;

    if (!options.replaceHash) {
      history.replaceState(null, "", `#slide-${current + 1}`);
    }
  }

  function nextSlide() {
    showSlide(current + 1);
  }

  function previousSlide() {
    showSlide(current - 1);
  }

  function toggleLaser() {
    laserOn = !laserOn;
    document.body.classList.toggle("laser-on", laserOn);
    laserBtn.textContent = laserOn ? "Laser: On" : "Laser: Off";
    laserBtn.classList.toggle("active-toggle", laserOn);
  }

  function updateLaser(event) {
    if (!laserOn) return;
    laserDot.style.transform = `translate(${event.clientX}px, ${event.clientY}px)`;
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  function openHelp() {
    helpOverlay.classList.add("open");
    helpOverlay.setAttribute("aria-hidden", "false");
  }

  function closeHelpOverlay() {
    helpOverlay.classList.remove("open");
    helpOverlay.setAttribute("aria-hidden", "true");
  }

  function handleKeydown(event) {
    const key = event.key;

    if (key === "Escape") {
      if (helpOverlay.classList.contains("open")) {
        closeHelpOverlay();
      } else if (laserOn) {
        toggleLaser();
      }
      return;
    }

    if (helpOverlay.classList.contains("open") && key !== "?") return;

    if (["ArrowRight", "PageDown", " ", "Spacebar", "n", "N"].includes(key)) {
      event.preventDefault();
      nextSlide();
      return;
    }

    if (["ArrowLeft", "PageUp", "p", "P"].includes(key)) {
      event.preventDefault();
      previousSlide();
      return;
    }

    if (key === "Home") {
      event.preventDefault();
      showSlide(0);
      return;
    }

    if (key === "End") {
      event.preventDefault();
      showSlide(slides.length - 1);
      return;
    }

    if (key === "l" || key === "L") {
      event.preventDefault();
      toggleLaser();
      return;
    }

    if (key === "f" || key === "F") {
      event.preventDefault();
      toggleFullscreen();
      return;
    }

    if (key === "?") {
      event.preventDefault();
      if (helpOverlay.classList.contains("open")) closeHelpOverlay();
      else openHelp();
    }
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }
})();

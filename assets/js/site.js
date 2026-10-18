/* Progressive enhancements only: project links and chart tables work without JS. */
(() => {
  const root = document.documentElement;
  const themeButton = document.querySelector('[data-theme-toggle]');
  const preference = window.matchMedia('(prefers-color-scheme: dark)');
  let savedTheme;
  try { savedTheme = localStorage.getItem('portfolio-theme'); } catch { /* Storage can be disabled. */ }
  function setTheme(theme) {
    root.dataset.theme = theme;
    if (themeButton) {
      themeButton.setAttribute('aria-pressed', String(theme === 'dark'));
      themeButton.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    }
  }
  setTheme(savedTheme || (preference.matches ? 'dark' : 'light'));
  if (themeButton) {
    themeButton.hidden = false;
    themeButton.addEventListener('click', () => {
      savedTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      setTheme(savedTheme);
      try { localStorage.setItem('portfolio-theme', savedTheme); } catch { /* Optional persistence. */ }
    });
  }
  preference.addEventListener('change', event => {
    if (!savedTheme) setTheme(event.matches ? 'dark' : 'light');
  });

  const carousel = document.querySelector('[data-tool-carousel]');
  if (carousel) {
    const slides = [...carousel.querySelectorAll('[data-tool-slide]')];
    const selectors = [...carousel.querySelectorAll('[data-tool-select]')];
    const track = carousel.querySelector('[data-tool-track]');
    const announcement = carousel.querySelector('[data-tool-announcement]');
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
    let current = 0;
    let rotationTimer;
    let overlay;
    let entrance;
    let exit;
    let visible = !('IntersectionObserver' in window);
    let measuredWidth = 0;

    function clearTransition() {
      entrance?.cancel();
      exit?.cancel();
      overlay?.remove();
      overlay = null;
    }

    function scheduleRotation() {
      clearTimeout(rotationTimer);
      const paused = reducedMotion.matches || document.hidden || !visible || carousel.matches(':hover') || carousel.contains(document.activeElement);
      carousel.dataset.rotation = paused ? 'paused' : 'playing';
      if (paused) return;
      rotationTimer = setTimeout(() => show(current + 1), 6000);
    }

    function show(index, announce = false, animate = true) {
      const next = (index + slides.length) % slides.length;
      clearTransition();
      if (animate && next !== current && !reducedMotion.matches && typeof slides[next].animate === 'function') {
        // A decorative copy crossfades out; only the new slide remains accessible.
        overlay = slides[current].cloneNode(true);
        overlay.removeAttribute('data-tool-slide');
        overlay.removeAttribute('aria-label');
        overlay.setAttribute('aria-hidden', 'true');
        overlay.inert = true;
        overlay.hidden = false;
        overlay.classList.add('tool-transition');
        track.append(overlay);
      }
      current = next;
      slides.forEach((slide, position) => { slide.hidden = position !== current; });
      selectors.forEach((button, position) => {
        button.setAttribute('aria-pressed', String(position === current));
      });
      if (overlay) {
        const outgoing = overlay;
        const options = { duration:420, easing:'cubic-bezier(.22,.61,.36,1)' };
        exit = outgoing.animate([{opacity:1, transform:'translateY(0)'}, {opacity:0, transform:'translateY(-5px)'}], options);
        entrance = slides[current].animate([{opacity:0, transform:'translateY(5px)'}, {opacity:1, transform:'translateY(0)'}], options);
        exit.finished.then(() => {
          outgoing.remove();
          if (overlay === outgoing) overlay = null;
        }).catch(() => { /* Fast manual selection can cancel the preceding fade. */ });
      }
      announcement.textContent = announce ? slides[current].innerText.replace(/\s+/g, ' ').trim() : '';
      scheduleRotation();
    }

    function measureSlides() {
      // Reserve the tallest slide so autoplay never shifts the content below it.
      carousel.classList.add('tool-carousel--measuring');
      const height = Math.max(...slides.map(slide => slide.getBoundingClientRect().height));
      carousel.classList.remove('tool-carousel--measuring');
      track.style.minHeight = `${Math.ceil(height)}px`;
      measuredWidth = carousel.clientWidth;
    }

    carousel.querySelector('[data-tool-controls]').hidden = false;
    carousel.querySelector('[data-tool-choices]').hidden = false;
    carousel.classList.add('tool-carousel--ready');
    carousel.querySelector('[data-tool-previous]').addEventListener('click', () => show(current - 1, true));
    carousel.querySelector('[data-tool-next]').addEventListener('click', () => show(current + 1, true));
    selectors.forEach(button => {
      button.addEventListener('click', () => show(Number(button.dataset.toolSelect), true));
    });
    carousel.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        show(current + (event.key === 'ArrowRight' ? 1 : -1), true);
      }
    });
    carousel.addEventListener('mouseenter', scheduleRotation);
    carousel.addEventListener('mouseleave', scheduleRotation);
    carousel.addEventListener('focusin', scheduleRotation);
    carousel.addEventListener('focusout', () => setTimeout(scheduleRotation, 0));
    document.addEventListener('visibilitychange', scheduleRotation);
    reducedMotion.addEventListener('change', () => {
      clearTransition();
      scheduleRotation();
    });
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(entries => {
        visible = entries[0].isIntersecting && entries[0].intersectionRatio >= 0.2;
        scheduleRotation();
      }, { threshold:[0, 0.2] }).observe(carousel);
    }
    if ('ResizeObserver' in window) {
      new ResizeObserver(() => {
        if (carousel.clientWidth !== measuredWidth) measureSlides();
      }).observe(carousel);
    } else window.addEventListener('resize', measureSlides);
    show(0, false, false);
    measureSlides();
    document.fonts?.ready.then(measureSlides);
  }

  document.querySelectorAll('[data-optional-image]').forEach(image => {
    const hide = () => { image.closest('[data-image-container]').hidden = true; };
    image.addEventListener('error', hide);
    if (image.complete && image.naturalWidth === 0) hide();
  });

})();

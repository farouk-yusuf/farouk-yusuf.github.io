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
    const announcement = carousel.querySelector('[data-tool-announcement]');
    let current = 0;

    function show(index, announce = false) {
      current = (index + slides.length) % slides.length;
      slides.forEach((slide, position) => { slide.hidden = position !== current; });
      selectors.forEach((button, position) => {
        button.setAttribute('aria-pressed', String(position === current));
      });
      if (announce) {
        announcement.textContent = slides[current].innerText.replace(/\s+/g, ' ').trim();
      }
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
    show(0);
  }

  document.querySelectorAll('[data-optional-image]').forEach(image => {
    const hide = () => { image.closest('[data-image-container]').hidden = true; };
    image.addEventListener('error', hide);
    if (image.complete && image.naturalWidth === 0) hide();
  });

})();

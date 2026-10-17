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

  const filters = document.querySelector('[data-project-filters]');
  const cards = [...document.querySelectorAll('[data-sector]')];
  if (filters && cards.length) {
    filters.hidden = false;
    filters.addEventListener('click', event => {
      const button = event.target.closest('button[data-filter]');
      if (!button) return;
      filters.querySelectorAll('button').forEach(item => {
        item.setAttribute('aria-pressed', String(item === button));
      });
      let visible = 0;
      cards.forEach(card => {
        card.hidden = button.dataset.filter !== 'all' && card.dataset.sector !== button.dataset.filter;
        if (!card.hidden) visible += 1;
      });
      document.querySelector('[data-filter-status]').textContent = `${visible} ${visible === 1 ? 'project' : 'projects'} shown`;
    });
  }

  document.querySelectorAll('[data-optional-image]').forEach(image => {
    const hide = () => { image.closest('[data-image-container]').hidden = true; };
    image.addEventListener('error', hide);
    if (image.complete && image.naturalWidth === 0) hide();
  });

  const journey = document.querySelector('[data-journey]');
  const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (journey && 'IntersectionObserver' in window && !motionPreference.matches) {
    const steps = [...journey.querySelectorAll('[data-journey-step]')];
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-revealed');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -24px 0px' });
    steps.forEach(step => observer.observe(step));
    journey.classList.add('journey--animated');
    // Keyboard navigation and fragment links must never leave focused text hidden.
    journey.addEventListener('focusin', event => {
      event.target.closest('[data-journey-step]')?.classList.add('is-revealed');
    });
    motionPreference.addEventListener('change', event => {
      if (event.matches) {
        journey.classList.remove('journey--animated');
        observer.disconnect();
      }
    });
  }
})();

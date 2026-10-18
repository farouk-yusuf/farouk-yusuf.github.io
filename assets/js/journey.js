/* Progressive enhancement: a sticky scene and native page scroll, no wheel interception. */
(() => {
  const route = document.querySelector('.route-section');
  if (!route) return;
  const scroller = route.querySelector('[data-route-scroll]');
  const scene = route.querySelector('[data-route-scene]');
  const chapters = [...route.querySelectorAll('[data-route-chapter]')];
  const stops = [...route.querySelectorAll('[data-route-stop]')];
  const positions = chapters.map(chapter => Number(chapter.dataset.stop));
  const links = [...route.querySelectorAll('[data-route-jump]')];
  const tools = [...route.querySelectorAll('[data-route-tool]')];
  const carried = [...route.querySelectorAll('[data-walker-item]')];
  const walker = route.querySelector('[data-route-walker]');
  const ending = route.querySelector('.route-ending');
  const viewToggle = route.querySelector('[data-route-view]');
  const desktop = matchMedia('(min-width: 768px) and (min-height: 760px)');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const stickySupported = CSS.supports('position', 'sticky') && CSS.supports('overflow', 'clip');
  let enhanced = false;
  let listChosen = false;
  let active = 0;
  let start = 0;
  let span = 1;
  let length = 3000;
  let previousY = scrollY;
  let stride = 0;
  let framePending = false;
  let stopTimer;

  function stopWalking() {
    walker.dataset.frame = '0';
    walker.classList.remove('is-walking');
  }

  function render() {
    framePending = false;
    if (!enhanced) return;
    const progress = Math.max(0, Math.min(1, (scrollY - start) / span));
    const travel = Math.min(1, progress / 0.84);
    const finished = progress >= 0.95;
    active = positions.reduce((last, position, index) => travel + 0.003 >= position ? index : last, 0);
    route.style.setProperty('--route-travel', `${-travel * length}px`);
    route.dataset.routeCurrent = String(active + 1);
    route.dataset.routeProgress = progress.toFixed(3);
    route.classList.toggle('route-at-end', finished);
    ending.querySelectorAll('a').forEach(link => { link.tabIndex = finished ? 0 : -1; });
    chapters.forEach((chapter, index) => chapter.classList.toggle('is-active', index === active && !finished));
    stops.forEach((stop, index) => stop.classList.toggle('is-past', index < active));
    tools.forEach((tool, index) => tool.classList.toggle('is-collected', index <= active));
    carried.forEach((item, index) => item.classList.toggle('is-collected', index <= active));
    links.forEach(link => {
      const selected = finished ? link.dataset.routeJump === 'ending' : Number(link.dataset.routeJump) === active;
      if (selected) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    });

    const delta = scrollY - previousY;
    previousY = scrollY;
    if (Math.abs(delta) > 0.5 && progress > 0 && progress < 0.84) {
      stride += Math.abs(delta);
      walker.style.setProperty('--facing', delta < 0 ? '-1' : '1');
      walker.dataset.frame = String(Math.floor(stride / 15) % 4);
      walker.classList.add('is-walking');
      clearTimeout(stopTimer);
      stopTimer = setTimeout(stopWalking, 140);
    } else if (progress <= 0 || progress >= 0.84) stopWalking();
  }

  function schedule() {
    if (!framePending && enhanced) {
      framePending = true;
      requestAnimationFrame(render);
    }
  }

  function measure() {
    length = Math.max(2900, scene.clientWidth * 3.6);
    route.style.setProperty('--route-length', `${length}px`);
    start = scroller.getBoundingClientRect().top + scrollY - 64;
    span = Math.max(1, scroller.offsetHeight - scene.offsetHeight);
    previousY = scrollY;
    render();
  }

  function configure() {
    enhanced = desktop.matches && !reduced.matches && !listChosen && stickySupported;
    route.classList.toggle('route-enhanced', enhanced);
    viewToggle.hidden = !desktop.matches || reduced.matches || !stickySupported;
    viewToggle.textContent = listChosen ? 'Show walking timeline' : 'Read as a list';
    viewToggle.setAttribute('aria-pressed', String(listChosen));
    if (enhanced) measure();
    else {
      route.classList.remove('route-at-end');
      ending.querySelectorAll('a').forEach(link => link.removeAttribute('tabindex'));
      clearTimeout(stopTimer);
      stopWalking();
      links.forEach(link => link.removeAttribute('aria-current'));
    }
  }

  function jump(destination) {
    const progress = destination === 'ending' ? 0.98 : positions[Number(destination)] * 0.84 + 0.005;
    window.scrollTo({ top:start + span * progress, behavior:'instant' });
    render();
  }

  links.forEach(link => link.addEventListener('click', event => {
    if (!enhanced) return;
    event.preventDefault();
    jump(link.dataset.routeJump);
    history.replaceState(null, '', link.getAttribute('href'));
  }));
  viewToggle.addEventListener('click', () => {
    listChosen = !listChosen;
    configure();
    if (enhanced) jump(active);
    else chapters[active].scrollIntoView({ behavior:'instant', block:'start' });
    // Keep the reading-mode control reachable after the layout change.
    viewToggle.focus({ preventScroll:true });
  });
  document.addEventListener('focusin', event => {
    const chapter = event.target.closest('[data-route-chapter]');
    if (enhanced && chapter) jump(chapters.indexOf(chapter));
  });
  window.addEventListener('scroll', schedule, { passive:true });
  window.addEventListener('resize', configure);
  desktop.addEventListener('change', configure);
  reduced.addEventListener('change', configure);
  window.addEventListener('load', () => {
    configure();
    const target = links.find(link => link.getAttribute('href') === location.hash);
    if (enhanced && target) jump(target.dataset.routeJump);
  });
  document.fonts?.ready.then(() => { if (enhanced) measure(); });
  configure();
})();

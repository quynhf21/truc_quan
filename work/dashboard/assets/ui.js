// Bridge visible field labels to Dash's generated trigger and selected-value label.
(() => {
  let pending = false;
  function syncInterface() {
    pending = false;
    document.querySelectorAll('.filters label').forEach(label => {
      const control = label.parentElement.querySelector('.dash-dropdown');
      if (!control) return;
      label.htmlFor = control.id;
      label.id = `${control.id}-label`;
      const ids = (control.getAttribute('aria-labelledby') || '').split(/\s+/)
        .filter(id => id && id !== label.id);
      const value = [label.id, ...ids].join(' ');
      if (control.getAttribute('aria-labelledby') !== value) control.setAttribute('aria-labelledby', value);
      if (control.tagName === 'BUTTON') control.tabIndex = 0;
    });
    document.querySelectorAll('.nav-item').forEach(link => {
      const active = new URL(link.href).pathname === location.pathname;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }
  const schedule = () => {
    if (!pending) { pending = true; requestAnimationFrame(syncInterface); }
  };
  new MutationObserver(schedule).observe(document.documentElement, {childList: true, subtree: true});
  window.addEventListener('popstate', schedule);
  schedule();
})();

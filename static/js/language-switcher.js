(function () {
  'use strict';

  function closeAll(except) {
    document.querySelectorAll('[data-lang-switcher].is-open').forEach(function (el) {
      if (el === except) return;
      el.classList.remove('is-open');
      var btn = el.querySelector('.lang-switcher-toggle');
      var menu = el.querySelector('.lang-switcher-menu');
      if (btn) btn.setAttribute('aria-expanded', 'false');
      if (menu) menu.hidden = true;
    });
  }

  document.addEventListener('click', function (e) {
    var switcher = e.target.closest('[data-lang-switcher]');
    var toggle = e.target.closest('.lang-switcher-toggle');

    if (toggle && switcher) {
      e.preventDefault();
      var willOpen = !switcher.classList.contains('is-open');
      closeAll();
      if (willOpen) {
        switcher.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
        var menu = switcher.querySelector('.lang-switcher-menu');
        if (menu) menu.hidden = false;
      }
      return;
    }

    if (!switcher) closeAll();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll();
  });
})();

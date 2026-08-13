(function () {
  'use strict';

  function wrapPasswordFields(root) {
    var scope = root || document;
    scope.querySelectorAll('.auth-card input[type="password"]').forEach(function (input) {
      if (input.closest('.password-field-wrap')) return;

      var wrap = document.createElement('div');
      wrap.className = 'password-field-wrap';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'password-toggle-btn';
      btn.setAttribute('aria-label', 'Show password');
      btn.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i>';
      wrap.appendChild(btn);

      btn.addEventListener('click', function () {
        var show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
        btn.innerHTML = show
          ? '<i class="bi bi-eye-slash" aria-hidden="true"></i>'
          : '<i class="bi bi-eye" aria-hidden="true"></i>';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    wrapPasswordFields();
  });
})();

(function() {
  'use strict';
  var saved = localStorage.getItem('cms-theme');
  if (!saved) {
    saved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  document.documentElement.setAttribute('data-theme', saved);
  var btn = document.getElementById('themeToggle');
  if (btn) {
    btn.textContent = saved === 'dark' ? '\u2600\ufe0f' : '\ud83c\udf19';
    btn.addEventListener('click', function() {
      var cur = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('cms-theme', next);
      btn.textContent = next === 'dark' ? '\u2600\ufe0f' : '\ud83c\udf19';
    });
  }
})();

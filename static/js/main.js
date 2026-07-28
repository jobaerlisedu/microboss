(function() {
  'use strict';

  // ─── Sidebar ───
  window.toggleSidebarCollapse = function() {
    var sidebar = document.getElementById('appSidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('phoenix-sidebar-collapsed', sidebar.classList.contains('collapsed') ? '1' : '0');
  };

  window.toggleSidebarMobile = function() {
    var sidebar = document.getElementById('appSidebar');
    var backdrop = document.getElementById('sidebarBackdrop');
    if (!sidebar) return;
    var isOpen = sidebar.classList.toggle('mobile-open');
    if (backdrop) backdrop.classList.toggle('show', isOpen);
    if (!isOpen) sidebar.classList.remove('collapsed');
    document.body.classList.toggle('sidebar-open', isOpen);
  };

  // Close sidebar on backdrop click
  document.addEventListener('click', function(e) {
    if (e.target.id === 'sidebarBackdrop') {
      window.toggleSidebarMobile();
    }
  });

  // Close mobile sidebar on route change (HTMX)
  document.addEventListener('htmx:afterSwap', function() {
    if (window.innerWidth <= 768) {
      var sidebar = document.getElementById('appSidebar');
      var backdrop = document.getElementById('sidebarBackdrop');
      if (sidebar) sidebar.classList.remove('mobile-open');
      if (backdrop) backdrop.classList.remove('show');
    }
  });

  window.toggleNavGroup = function(el) {
    var group = el.closest('.nav-group');
    if (group) group.classList.toggle('open');
  };

  // ─── Modal ───
  var _lastFocusedEl = null;

  window.openNoticeModal = function(url) {
    var overlay = document.getElementById('modal-overlay');
    var body = document.getElementById('modal-body');
    if (!overlay || !body) return;
    _lastFocusedEl = document.activeElement;
    body.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-soft);">Loading...</div>';
    overlay.classList.remove('hidden');
    overlay.focus();
    htmx.ajax('GET', url, {target: '#modal-body', swap: 'innerHTML'});
  };

  window.closeModal = function() {
    var overlay = document.getElementById('modal-overlay');
    if (!overlay) return;
    overlay.classList.add('hidden');
    if (_lastFocusedEl && _lastFocusedEl.focus) {
      _lastFocusedEl.focus();
      _lastFocusedEl = null;
    }
  };

  // ─── Toast ───
  window.showToast = function(msg, type) {
    var el = document.getElementById('toast');
    if (!el) return;
    el.textContent = msg;
    el.style.background = type === 'error' ? '#E45744' : type === 'success' ? '#22A67E' : 'var(--navy-900)';
    el.classList.add('show');
    if (window._toastTimer) clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(function() { el.classList.remove('show'); }, 3500);
  };

  // ─── DOM ───
  document.addEventListener('DOMContentLoaded', function() {

    // Restore sidebar
    if (localStorage.getItem('phoenix-sidebar-collapsed') === '1') {
      var sidebar = document.getElementById('appSidebar');
      if (sidebar) sidebar.classList.add('collapsed');
    }

    // HTMX: refresh dashboard charts after any swap
    document.addEventListener('htmx:afterSwap', function() {
      if (typeof window.refreshDashboardData === 'function') {
        setTimeout(window.refreshDashboardData, 50);
      }
      // Re-bind newly loaded .tab-btn elements via delegation (noop, handled by delegation below)
    });

    // HTMX: inject CSRF token
    document.body.addEventListener('htmx:configRequest', function(e) {
      var meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) {
        e.detail.headers['X-CSRFToken'] = meta.getAttribute('content');
      }
    });

    // HTMX: suppress swap on 5xx; pass 404 through so error content renders
    document.addEventListener('htmx:beforeSwap', function(evt) {
      if (evt.detail.xhr && evt.detail.xhr.status >= 400) {
        if (evt.detail.xhr.status === 404) return;
        evt.detail.shouldSwap = false;
      }
    });

    // HTMX: toast listener
    document.addEventListener('cms-toast', function(e) {
      var d = e.detail;
      if (d && d.message) {
        window.showToast(d.message, d.type || 'success');
      }
    });

    // ─── Tab URL mapping for active-state restoration ───
    var TAB_URL_RULES = [
      // Specific sub-paths must come before their parent prefixes
      { prefix: '/cms/admin-panel/roles/', tab: 'roles' },
      { prefix: '/cms/entries/new/', tab: 'new' },
      // General prefixes (ordered most-to-least specific)
      { prefix: '/cms/dashboard/', tab: 'dashboard' },
      { prefix: '/cms/assignments/', tab: 'assignment' },
      { prefix: '/cms/content-sources/', tab: 'contentlist' },
      { prefix: '/cms/scripts/', tab: 'scripts' },
      { prefix: '/cms/audio/', tab: 'audio' },
      { prefix: '/cms/final-packages/', tab: 'finalpackage' },
      { prefix: '/cms/entries/', tab: 'all' },
      { prefix: '/cms/archive/', tab: 'archive' },
      { prefix: '/cms/sponsors/', tab: 'sponsors' },
      { prefix: '/cms/content-deletion/', tab: 'content-deletion' },
      { prefix: '/cms/deleted-data/', tab: 'deleted-data' },
      { prefix: '/cms/roster/', tab: 'duty-roster' },
      { prefix: '/cms/leave/', tab: 'leave' },
      { prefix: '/cms/leaderboard/', tab: 'leaderboard' },
      { prefix: '/cms/notices/', tab: 'notices' },
      { prefix: '/cms/reports/', tab: 'reports' },
      { prefix: '/cms/admin-panel/', tab: 'admin' },
      { prefix: '/cms/', tab: 'dashboard' },
    ];

    function activateSidebarTab(tab) {
      document.querySelectorAll('#appSidebar .nav-item.tab-btn').forEach(function(b) {
        b.classList.toggle('active', b.getAttribute('data-tab') === tab);
      });
    }

    // Restore active tab from current URL on page load
    var path = window.location.pathname.replace(/\/+$/, '') + '/';
    for (var i = 0; i < TAB_URL_RULES.length; i++) {
      if (path.indexOf(TAB_URL_RULES[i].prefix) === 0) {
        activateSidebarTab(TAB_URL_RULES[i].tab);
        break;
      }
    }

    // ─── Sidebar tab switching (event delegation) ───
    document.body.addEventListener('click', function(e) {
      var btn = e.target.closest('#appSidebar .nav-item.tab-btn');
      if (btn) {
        document.querySelectorAll('#appSidebar .nav-item.tab-btn').forEach(function(b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
      }
    });

    // ─── Keyboard: Escape closes modal ───
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        var overlay = document.getElementById('modal-overlay');
        if (overlay && !overlay.classList.contains('hidden')) {
          window.closeModal();
        }
      }
    });

    // ─── Clock ───
    function tickClock() {
      var el = document.getElementById('clockTime');
      if (!el) return;
      var now = new Date();
      var opts = { timeZone: 'Asia/Dhaka', hour: '2-digit', minute: '2-digit', second: '2-digit' };
      el.textContent = now.toLocaleTimeString('en-US', opts);
      var dateEl = document.getElementById('clockDate');
      if (dateEl) {
        var dOpts = { timeZone: 'Asia/Dhaka', weekday: 'short', day: 'numeric', month: 'short' };
        dateEl.textContent = now.toLocaleDateString('en-US', dOpts);
      }
    }
    tickClock();
    setInterval(tickClock, 1000);

    // ─── Weather (only if clockWx element exists — i.e. user is logged in) ───
    var wxEl = document.getElementById('clockWx');
    if (wxEl) {
      function loadWeather() {
        fetch('https://api.open-meteo.com/v1/forecast?latitude=23.81&longitude=90.41&current_weather=true')
          .then(function(r) { return r.json(); })
          .then(function(data) {
            var t = Math.round(data.current_weather.temperature);
            var code = data.current_weather.weathercode;
            var map = {
              0: '\u2600\ufe0f', 1: '\ud83c\udf24\ufe0f', 2: '\u26c5', 3: '\u2601\ufe0f',
              45: '\ud83c\udf2b\ufe0f', 48: '\ud83c\udf2b\ufe0f', 51: '\ud83c\udf26\ufe0f', 61: '\ud83c\udf27\ufe0f',
              63: '\ud83c\udf27\ufe0f', 65: '\ud83c\udf27\ufe0f', 80: '\ud83c\udf26\ufe0f', 95: '\u26c8\ufe0f'
            };
            wxEl.textContent = (map[code] || '\ud83c\udf21\ufe0f') + ' ' + t + '\u00b0C';
          })
          .catch(function() { wxEl.textContent = ''; });
      }
      loadWeather();
      setInterval(loadWeather, 15 * 60 * 1000);
    }

    // ─── Notification bell dropdown ───
    var bell = document.getElementById('notif-bell');
    var dropdown = document.getElementById('notif-dropdown');
    if (bell && dropdown) {
      var _scrollRafId = null;

      function positionDropdown() {
        var rect = bell.getBoundingClientRect();
        dropdown.style.top = (rect.bottom + 6) + 'px';
        dropdown.style.right = (window.innerWidth - rect.right) + 'px';
      }

      function openNotifDropdown() {
        positionDropdown();
        dropdown.classList.add('open');
        htmx.ajax('GET', '/api/v1/notifications/', {target: '#notif-dropdown-content', swap: 'innerHTML'});
      }

      function closeNotifDropdown() {
        dropdown.classList.remove('open');
        var content = document.getElementById('notif-dropdown-content');
        if (content) content.innerHTML = '';
      }

      bell.addEventListener('click', function(e) {
        e.stopPropagation();
        if (dropdown.classList.contains('open')) {
          closeNotifDropdown();
        } else {
          openNotifDropdown();
        }
      });

      document.addEventListener('click', function(e) {
        if (dropdown.classList.contains('open') && !bell.contains(e.target) && !dropdown.contains(e.target)) {
          closeNotifDropdown();
        }
      });

      function onScrollOrResize() {
        if (_scrollRafId) cancelAnimationFrame(_scrollRafId);
        _scrollRafId = requestAnimationFrame(function() {
          if (dropdown.classList.contains('open')) positionDropdown();
          _scrollRafId = null;
        });
      }

      window.addEventListener('scroll', onScrollOrResize, {passive: true});
      window.addEventListener('resize', onScrollOrResize, {passive: true});
    }

  });

  // ─── Theme ───
  (function() {
    var saved = localStorage.getItem('phoenix-theme');
    if (saved === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      var btn = document.getElementById('themeToggle');
      if (btn) btn.querySelector('i').className = 'bi bi-sun-fill';
    }
  })();

  window.toggleTheme = function() {
    var html = document.documentElement;
    var btn = document.getElementById('themeToggle');
    var isDark = html.getAttribute('data-theme') === 'dark';
    if (isDark) {
      html.removeAttribute('data-theme');
      localStorage.setItem('phoenix-theme', 'light');
      if (btn) btn.querySelector('i').className = 'bi bi-moon-fill';
    } else {
      html.setAttribute('data-theme', 'dark');
      localStorage.setItem('phoenix-theme', 'dark');
      if (btn) btn.querySelector('i').className = 'bi bi-sun-fill';
    }
  };

  // ─── Confetti / Celebration ───
  window.closeCongrats = function() {
    var m = document.getElementById('congratsModal');
    if (m) m.classList.add('hidden');
  };

  window.fireConfetti = function() {
    var layer = document.getElementById('confettiLayer');
    if (!layer) return;
    layer.innerHTML = '';
    var colors = ['#f59e0b','#3b82f6','#ef4444','#22c55e','#8b5cf6','#ec4899','#06b6d4','#f97316'];
    var shapes = ['●','■','▲','★','♦'];
    for (var i = 0; i < 120; i++) {
      var el = document.createElement('span');
      el.textContent = shapes[Math.floor(Math.random() * shapes.length)];
      el.style.cssText = [
        'position:fixed',
        'z-index:9999',
        'pointer-events:none',
        'font-size:' + (8 + Math.random() * 16) + 'px',
        'color:' + colors[Math.floor(Math.random() * colors.length)],
        'left:' + (Math.random() * 100) + 'vw',
        'top:' + (-5 - Math.random() * 10) + 'vh',
        'opacity:' + (0.7 + Math.random() * 0.3),
        'transform:rotate(' + (Math.random() * 360) + 'deg)',
        'transition:transform ' + (2 + Math.random() * 3) + 's linear,top ' + (2 + Math.random() * 3) + 's ease-in,opacity ' + (2 + Math.random() * 2) + 's ease-out',
      ].join(';');
      layer.appendChild(el);
      requestAnimationFrame(function() {
        el.style.top = (100 + Math.random() * 20) + 'vh';
        el.style.transform = 'rotate(' + (720 + Math.random() * 720) + 'deg)';
        el.style.opacity = '0';
      });
    }
    setTimeout(function() { layer.innerHTML = ''; }, 5000);
  };

})();

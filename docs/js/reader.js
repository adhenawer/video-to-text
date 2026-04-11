/* ============================================================
   video-to-text — Reader
   JS compartilhado para artigos: tema, progresso, resume reading
   Requer: <body class="page-article" data-storage-key="reading_VIDEO_ID_">
   ============================================================ */

(function () {
  // --- Device ID ---
  function getDeviceId() {
    var id = localStorage.getItem('_deviceId');
    if (!id) {
      id = 'dev_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
      localStorage.setItem('_deviceId', id);
    }
    return id;
  }

  var STORAGE_KEY = document.body.dataset.storageKey + getDeviceId();
  var saveTimer = null;
  var resumeTarget = null;

  // --- Scroll percentage (clamped 0-100, handles edge cases) ---
  function getScrollPct() {
    var h = document.documentElement;
    var scrollable = h.scrollHeight - h.clientHeight;
    if (scrollable <= 0) return 100; // page fits in viewport = fully read
    var raw = h.scrollTop / scrollable;
    // Snap to 100 when near the bottom (within 5px tolerance)
    if (h.scrollHeight - h.scrollTop - h.clientHeight < 5) return 100;
    return Math.min(100, Math.max(0, Math.round(raw * 100)));
  }

  // --- Current section detection ---
  function getCurrentSection() {
    var current = '';
    document.querySelectorAll('h2').forEach(function (el) {
      if (el.getBoundingClientRect().top < 120) current = el.id;
    });
    return current;
  }

  // --- Save / Load position ---
  function savePosition() {
    var pct = getScrollPct();
    var section = getCurrentSection();
    var data = {
      scrollY: window.scrollY,
      scrollPct: pct,
      section: section,
      sectionTitle: section ? (document.getElementById(section)?.textContent || '') : '',
      theme: document.documentElement.getAttribute('data-theme') || 'light',
      timestamp: Date.now()
    };
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch (e) {}
  }

  function debounceSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(savePosition, 250);
  }

  function loadPosition() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)); }
    catch (e) { return null; }
  }

  // --- Resume banner ---
  function resumeReading() {
    if (!resumeTarget) return;
    // Prefer scrolling to section (stable across sessions) over scrollY (fragile)
    if (resumeTarget.section) {
      var el = document.getElementById(resumeTarget.section);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        document.getElementById('resumeBanner').classList.remove('show');
        return;
      }
    }
    // Fallback to scrollY
    if (resumeTarget.scrollY > 0) {
      window.scrollTo({ top: resumeTarget.scrollY, behavior: 'smooth' });
    }
    document.getElementById('resumeBanner').classList.remove('show');
  }

  function dismissResume() {
    document.getElementById('resumeBanner').classList.remove('show');
  }

  // --- Theme ---
  function setTheme(theme) {
    if (theme === 'light') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-btn').forEach(function (btn, i) {
      btn.classList.toggle('active', ['light', 'cool', 'dark'][i] === theme);
    });
    localStorage.setItem('_reading_theme', theme);
    savePosition();
  }

  // --- Scroll handler ---
  var progressEl = document.getElementById('progress');
  var backTopEl = document.getElementById('backTop');
  var readingPctEl = document.getElementById('readingPct');

  window.addEventListener('scroll', function () {
    var pct = getScrollPct();
    progressEl.style.width = pct + '%';
    backTopEl.classList.toggle('show', window.scrollY > 400);
    readingPctEl.textContent = pct + '%';
    readingPctEl.classList.toggle('show', window.scrollY > 200);
    debounceSave();
  }, { passive: true });

  // --- Persist on page leave (multiple events for cross-browser reliability) ---
  function saveNow() {
    clearTimeout(saveTimer);
    savePosition();
  }

  window.addEventListener('beforeunload', saveNow);
  window.addEventListener('pagehide', saveNow);       // reliable on iOS Safari
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) saveNow();
  });
  // Periodic save as safety net (every 5s while reading)
  setInterval(savePosition, 5000);

  // --- Init ---
  var savedTheme = localStorage.getItem('_reading_theme') || 'light';
  setTheme(savedTheme);

  var saved = loadPosition();
  if (saved && saved.scrollPct > 0 && saved.scrollPct < 100 && (saved.section || saved.scrollY > 300)) {
    // Auto-scroll to saved position after page renders
    setTimeout(function () {
      if (saved.section) {
        var el = document.getElementById(saved.section);
        if (el) { el.scrollIntoView({ behavior: 'instant', block: 'start' }); return; }
      }
      if (saved.scrollY > 0) window.scrollTo({ top: saved.scrollY, behavior: 'instant' });
    }, 100);
  }

  // Expose to onclick handlers in HTML
  window.setTheme = setTheme;
  window.resumeReading = resumeReading;
  window.dismissResume = dismissResume;
})();

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

  // --- Save / Load position ---
  function savePosition() {
    var h = document.documentElement;
    var scrollPct = h.scrollTop / (h.scrollHeight - h.clientHeight);
    var currentSection = '';
    document.querySelectorAll('h2').forEach(function (el) {
      if (el.getBoundingClientRect().top < 100) currentSection = el.id;
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      scrollY: window.scrollY,
      scrollPct: Math.round(scrollPct * 100),
      section: currentSection,
      sectionTitle: currentSection ? document.getElementById(currentSection)?.textContent : '',
      theme: document.documentElement.getAttribute('data-theme') || 'light',
      timestamp: Date.now()
    }));
  }

  function debounceSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(savePosition, 300);
  }

  function loadPosition() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)); }
    catch (e) { return null; }
  }

  // --- Resume banner ---
  function resumeReading() {
    if (resumeTarget) window.scrollTo({ top: resumeTarget.scrollY, behavior: 'smooth' });
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
    var h = document.documentElement;
    var pct = Math.round((h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100);
    progressEl.style.width = pct + '%';
    backTopEl.classList.toggle('show', h.scrollTop > 400);
    readingPctEl.textContent = pct + '%';
    readingPctEl.classList.toggle('show', h.scrollTop > 200);
    debounceSave();
  }, { passive: true });

  // --- Init ---
  var savedTheme = localStorage.getItem('_reading_theme') || 'light';
  setTheme(savedTheme);

  var saved = loadPosition();
  if (saved && saved.scrollY > 300) {
    resumeTarget = saved;
    document.getElementById('resumeText').textContent =
      '\uD83D\uDCD6 Continuar: ' + (saved.sectionTitle || 'seção anterior') + ' (' + (saved.scrollPct || 0) + '%)';
    setTimeout(function () { document.getElementById('resumeBanner').classList.add('show'); }, 500);
    setTimeout(function () { document.getElementById('resumeBanner').classList.remove('show'); }, 8500);
  }

  window.addEventListener('beforeunload', savePosition);
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) savePosition();
  });

  // Expose to onclick handlers in HTML
  window.setTheme = setTheme;
  window.resumeReading = resumeReading;
  window.dismissResume = dismissResume;
})();

/* ============================================================
   video-to-text — Reader
   Progress bar, reading position save/resume.
   Requires: <body class="page-article" data-storage-key="reading_VIDEO_ID_">
   ============================================================ */

(function () {
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

  function getScrollPct() {
    var h = document.documentElement;
    var scrollable = h.scrollHeight - h.clientHeight;
    if (scrollable <= 0) return 100;
    if (h.scrollHeight - h.scrollTop - h.clientHeight < 5) return 100;
    return Math.min(100, Math.max(0, Math.round((h.scrollTop / scrollable) * 100)));
  }

  function getCurrentSection() {
    var current = '';
    document.querySelectorAll('h2').forEach(function (el) {
      if (el.getBoundingClientRect().top < 120) current = el.id;
    });
    return current;
  }

  function savePosition() {
    var pct = getScrollPct();
    var section = getCurrentSection();
    var data = {
      scrollY: window.scrollY,
      scrollPct: pct,
      section: section,
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

  var resumeTarget = null;
  function resumeReading() {
    if (!resumeTarget) return;
    var banner = document.getElementById('resumeBanner');
    if (resumeTarget.section) {
      var el = document.getElementById(resumeTarget.section);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (banner) banner.classList.remove('visible');
        return;
      }
    }
    if (resumeTarget.scrollY > 0) {
      window.scrollTo({ top: resumeTarget.scrollY, behavior: 'smooth' });
    }
    if (banner) banner.classList.remove('visible');
  }

  function dismissResume() {
    var banner = document.getElementById('resumeBanner');
    if (banner) banner.classList.remove('visible');
  }

  var progressEl = document.getElementById('progress');
  var readingPctEl = document.getElementById('readingPct');

  window.addEventListener('scroll', function () {
    var pct = getScrollPct();
    if (progressEl) progressEl.style.width = pct + '%';
    if (readingPctEl) {
      readingPctEl.textContent = pct + '%';
      readingPctEl.classList.toggle('visible', window.scrollY > 200 && pct < 100);
    }
    debounceSave();
  }, { passive: true });

  function saveNow() { clearTimeout(saveTimer); savePosition(); }
  window.addEventListener('beforeunload', saveNow);
  window.addEventListener('pagehide', saveNow);
  document.addEventListener('visibilitychange', function () { if (document.hidden) saveNow(); });
  setInterval(savePosition, 5000);

  var saved = loadPosition();
  if (saved && saved.scrollPct > 5 && saved.scrollPct < 95 && (saved.section || saved.scrollY > 300)) {
    resumeTarget = saved;
    setTimeout(function () {
      var banner = document.getElementById('resumeBanner');
      if (banner) banner.classList.add('visible');
    }, 500);
  }

  window.resumeReading = resumeReading;
  window.dismissResume = dismissResume;
})();

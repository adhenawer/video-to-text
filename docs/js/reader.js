/* ============================================================
   video-to-text — Reader
   Progress bar, reading position save/resume, reading aids:
     • TOC sidebar (left, fixed, ≥1200px) with scrollspy
     • Reading-time estimate (computed from word count)
     • "% · X min restantes" enhanced badge
     • Focus mode (F key — dim everything but the section in view)
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

  if (document.body.classList.contains('page-article') === false) {
    // Reader.js is loaded only on article pages, but be defensive.
    return;
  }

  var STORAGE_KEY = document.body.dataset.storageKey + getDeviceId();
  var saveTimer = null;

  // --------------------------------------------------------------------
  // Reading time estimate (word-count / 200wpm)
  // --------------------------------------------------------------------
  function estimateMinutes() {
    var article = document.querySelector('article');
    if (!article) return 0;
    var text = article.innerText || article.textContent || '';
    var words = text.trim().split(/\s+/).filter(Boolean).length;
    return Math.max(1, Math.round(words / 200));
  }
  var TOTAL_MIN = estimateMinutes();

  // Inject reading-time chip next to the channel/cite line in <header>
  (function injectReadingTime() {
    var article = document.querySelector('article');
    if (!article) return;
    var header = article.querySelector(':scope > header');
    if (!header) return;
    var meta = header.querySelector('.meta');
    if (!meta) return;
    if (meta.querySelector('.reading-time')) return;
    var chip = document.createElement('span');
    chip.className = 'reading-time';
    chip.textContent = TOTAL_MIN + ' min de leitura';
    meta.appendChild(chip);
  })();

  // --------------------------------------------------------------------
  // TOC sidebar (≥1200px) — clones the inline TOC into a fixed left aside
  // --------------------------------------------------------------------
  (function buildTocSidebar() {
    var inlineToc = document.querySelector(
      'nav[aria-label="Índice do artigo"], nav[aria-label="Article table of contents"]'
    );
    if (!inlineToc) return;
    var ol = inlineToc.querySelector('ol');
    if (!ol) return;
    var aside = document.createElement('aside');
    aside.className = 'toc-sidebar';
    aside.setAttribute('aria-label', 'Índice rápido');
    var head = document.createElement('div');
    head.className = 'toc-head';
    head.textContent = 'Neste artigo';
    aside.appendChild(head);
    var olClone = ol.cloneNode(true);
    // Remove any inner numbering — we add §NN via CSS counter
    olClone.removeAttribute('start');
    aside.appendChild(olClone);
    document.body.appendChild(aside);
  })();

  // --------------------------------------------------------------------
  // Video sync card (YouTube IFrame API) — keeps the player at the
  // timestamp of the section currently in view; click "→ saltar para §X"
  // to seek the player without scrolling the page.
  // --------------------------------------------------------------------
  var ytPlayer = null;        // YT.Player instance once ready
  var ytReady = false;        // becomes true on onReady
  var ytPendingSeek = null;   // queue if user clicks before player loads
  var currentSectionTs = 0;   // seconds of the section currently in view
  var currentSectionN  = 1;
  var syncBtn = document.querySelector('.video-card .video-sync');

  function _parseTimestampFromTsLink(h2) {
    // Each H2 has either an <a class="ts-link" href="...&t=NNN"> or <span class="ts-mark">
    var a = h2.querySelector('a.ts-link[href*="t="], a.ts-link[href*="start="]');
    if (a) {
      var m = a.href.match(/[?&](?:t|start)=(\d+)/);
      if (m) return parseInt(m[1], 10);
    }
    // Fallback: parse the visible "MM:SS" / "H:MM:SS" text
    var label = h2.querySelector('.ts-link, .ts-mark');
    if (!label) return 0;
    var parts = (label.textContent.trim().replace(/^▶\s*/, '')).split(':').map(function (p) { return parseInt(p, 10); });
    if (parts.some(isNaN)) return 0;
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    return 0;
  }

  function _formatTs(s) {
    if (s < 60) return '0:' + (s < 10 ? '0' + s : s);
    if (s < 3600) return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
    return Math.floor(s / 3600) + ':' + ('0' + Math.floor((s % 3600) / 60)).slice(-2) + ':' + ('0' + (s % 60)).slice(-2);
  }

  function updateSyncButton() {
    if (!syncBtn) return;
    if (!ytReady) {
      syncBtn.textContent = syncBtn.dataset.default || 'Loading…';
      return;
    }
    var tpl = syncBtn.dataset.template || 'Jump to §{n} · {ts}';
    var label = tpl
      .replace('{n}', ('0' + currentSectionN).slice(-2))
      .replace('{ts}', _formatTs(currentSectionTs));
    syncBtn.textContent = label;
  }

  if (syncBtn) {
    syncBtn.addEventListener('click', function () {
      if (!ytReady) {
        // Player not yet loaded — queue the seek for onReady
        ytPendingSeek = currentSectionTs;
        return;
      }
      try {
        ytPlayer.seekTo(currentSectionTs, true);
        ytPlayer.playVideo();
        syncBtn.classList.add('playing');
      } catch (e) {}
    });
  }

  // Load YouTube IFrame API only if the YouTube card is present
  (function loadYouTube() {
    var card = document.querySelector('.video-card[data-provider="youtube"]');
    if (!card) return;
    var vid = card.dataset.vid;
    if (!vid) return;

    var prevHook = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = function () {
      if (typeof prevHook === 'function') {
        try { prevHook(); } catch (e) {}
      }
      var mount = card.querySelector('#ytplayer-mount');
      if (!mount || typeof YT === 'undefined' || !YT.Player) return;
      ytPlayer = new YT.Player(mount, {
        videoId: vid,
        width: '100%',
        height: '100%',
        host: 'https://www.youtube-nocookie.com',
        playerVars: { rel: 0, modestbranding: 1, playsinline: 1 },
        events: {
          onReady: function () {
            ytReady = true;
            updateSyncButton();
            if (ytPendingSeek != null) {
              try {
                ytPlayer.seekTo(ytPendingSeek, true);
                ytPlayer.playVideo();
              } catch (e) {}
              ytPendingSeek = null;
            }
          }
        }
      });
    };
    if (document.querySelector('script[src*="youtube.com/iframe_api"]')) {
      // Already loading — onReady will fire normally
      return;
    }
    var s = document.createElement('script');
    s.src = 'https://www.youtube.com/iframe_api';
    s.async = true;
    document.head.appendChild(s);
  })();

  // --------------------------------------------------------------------
  // Scrollspy — highlight TOC entry whose section is currently in view
  // --------------------------------------------------------------------
  function setupScrollspy() {
    var headings = Array.prototype.slice.call(document.querySelectorAll('article h2[id]'));
    if (!headings.length) return null;
    var tocLinks = Array.prototype.slice.call(document.querySelectorAll(
      '.toc-sidebar a, nav[aria-label="Índice do artigo"] a, nav[aria-label="Article table of contents"] a'
    ));
    var byId = {};
    tocLinks.forEach(function (a) {
      var href = a.getAttribute('href') || '';
      var m = href.match(/^#(.+)$/);
      if (m) byId[m[1]] = byId[m[1]] || [];
      if (m) byId[m[1]].push(a);
    });
    function update() {
      var current = headings[0];
      var idx = 0;
      for (var i = 0; i < headings.length; i++) {
        if (headings[i].getBoundingClientRect().top < 140) {
          current = headings[i];
          idx = i;
        } else break;
      }
      var id = current && current.id;
      tocLinks.forEach(function (a) { a.classList.remove('is-active'); });
      if (id && byId[id]) byId[id].forEach(function (a) { a.classList.add('is-active'); });
      // Track current section's timestamp for the video card sync button
      var ts = _parseTimestampFromTsLink(current);
      currentSectionTs = ts;
      currentSectionN  = idx + 1;
      updateSyncButton();
    }
    return update;
  }
  var spyUpdate = setupScrollspy();

  // --------------------------------------------------------------------
  // Focus mode — F key toggles, IntersectionObserver picks the active section
  // --------------------------------------------------------------------
  (function setupFocusMode() {
    var sections = document.querySelectorAll('article section');
    if (!sections.length) return;
    var hint = document.createElement('div');
    hint.className = 'focus-hint';
    hint.textContent = 'Modo foco · F para sair';
    document.body.appendChild(hint);

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && e.intersectionRatio > 0.15) {
          // Mark the first-visible section as active
          sections.forEach(function (s) { s.classList.remove('in-view'); });
          e.target.classList.add('in-view');
        }
      });
    }, { rootMargin: '-25% 0px -50% 0px', threshold: [0, 0.15, 0.4] });
    sections.forEach(function (s) { io.observe(s); });

    document.addEventListener('keydown', function (e) {
      var t = e.target;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      if (e.key === 'f' || e.key === 'F') {
        document.body.classList.toggle('focus-mode');
      } else if (e.key === 'Escape' && document.body.classList.contains('focus-mode')) {
        document.body.classList.remove('focus-mode');
      }
    });
  })();

  // --------------------------------------------------------------------
  // Position save/resume + progress bar (+ min restantes)
  // --------------------------------------------------------------------
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
  if (readingPctEl) readingPctEl.classList.add('with-min');

  window.addEventListener('scroll', function () {
    var pct = getScrollPct();
    if (progressEl) progressEl.style.width = pct + '%';
    if (readingPctEl) {
      var remaining = Math.max(0, Math.round(TOTAL_MIN * (1 - pct / 100)));
      readingPctEl.textContent = pct + '% · ' + remaining + ' min restantes';
      readingPctEl.classList.toggle('visible', window.scrollY > 200 && pct < 100);
    }
    if (spyUpdate) spyUpdate();
    debounceSave();
  }, { passive: true });

  function saveNow() { clearTimeout(saveTimer); savePosition(); }
  window.addEventListener('beforeunload', saveNow);
  window.addEventListener('pagehide', saveNow);
  document.addEventListener('visibilitychange', function () { if (document.hidden) saveNow(); });
  setInterval(savePosition, 5000);

  // First scrollspy update on load
  if (spyUpdate) spyUpdate();

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

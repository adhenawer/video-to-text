// Global language switcher + browser locale detection.
// Each page declares its language pair via <link rel="alternate" hreflang="...">.
(function () {
  'use strict';

  const STORAGE_KEY = '_site_lang';
  const DEFAULT_LANG = 'pt-BR';

  function getPreferredLang() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return saved;
    const nav = (navigator.language || navigator.userLanguage || '').toLowerCase();
    return nav.startsWith('pt') ? 'pt-BR' : 'en';
  }

  function setPreferredLang(lang) {
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
  }

  function findAlternate(hreflang) {
    return document.querySelector('link[rel="alternate"][hreflang="' + hreflang + '"]');
  }

  function setupButtons() {
    const btns = document.querySelectorAll('.site-header .lang-btn');
    btns.forEach(function (btn) {
      const lang = btn.getAttribute('data-lang');
      if (!lang) return;
      const alt = findAlternate(lang);
      const currentLang = document.documentElement.lang || DEFAULT_LANG;

      if (currentLang.toLowerCase().startsWith(lang.toLowerCase()) ||
          (lang === 'pt-BR' && currentLang.toLowerCase() === 'pt-br') ||
          (lang === 'en' && currentLang.toLowerCase() === 'en')) {
        btn.classList.add('active');
      }

      if (alt) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          setPreferredLang(lang);
          window.location.href = alt.href;
        });
      } else {
        btn.classList.add('disabled');
        btn.setAttribute('aria-disabled', 'true');
        btn.style.opacity = '0.45';
        btn.style.cursor = 'not-allowed';
      }
    });
  }

  function redirectIfNeeded() {
    // Only redirect on pages that explicitly opt in via data-auto-redirect="true"
    // (avoids redirecting on article pages where the user may want the current language)
    if (!document.body.dataset.autoRedirect) return;
    if (sessionStorage.getItem('_site_lang_redirected') === '1') return;
    const preferred = getPreferredLang();
    const currentLang = document.documentElement.lang || DEFAULT_LANG;
    if (preferred.toLowerCase().startsWith(currentLang.toLowerCase()) ||
        currentLang.toLowerCase().startsWith(preferred.toLowerCase())) return;
    const alt = findAlternate(preferred);
    if (alt) {
      sessionStorage.setItem('_site_lang_redirected', '1');
      window.location.href = alt.href;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      redirectIfNeeded();
      setupButtons();
    });
  } else {
    redirectIfNeeded();
    setupButtons();
  }
})();

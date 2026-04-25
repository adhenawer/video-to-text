// Tags + lateral on the index pages.
// Reads data/moc.json (slug -> tags, category) and patches each card:
//   1. injects clickable tag pills under the description
//   2. moves "lateral" cards into a "Curiosidades" section at the end
//   3. wires up the tag filter bar
(function () {
  // Resolve data path relative to the page (works for / and /en/).
  const dataUrl = new URL('data/moc.json', new URL('..', document.baseURI || location.href)).pathname;
  // ^ for /en/index.html → /data/moc.json. For /index.html → /data/moc.json.
  const fallbackUrl = location.pathname.includes('/en/') ? '../data/moc.json' : 'data/moc.json';
  const isEN = location.pathname.includes('/en/');

  const LATERAL_TITLE_PT = 'Curiosidades';
  const LATERAL_TITLE_EN = 'Curiosities';
  const LATERAL_HINT_PT = 'fora do eixo principal — finanças, mercado, pessoal';
  const LATERAL_HINT_EN = 'off the main axis — finance, market, personal';

  // Fallback for posts whose HTML exists on the index page but is not yet
  // in transcripts/index.json (legacy/manual entries). Keep small.
  const ORPHAN_TAGS = {
    'dario-amodei-scaling-rl-agi-futuro-anthropic': { tags: ['ia-2026', 'agentic-engineering'], category: 'core' },
    'ronycoder-video': { tags: ['soft-skills', 'carreira'], category: 'core' },
    'ronycoder-arte-comunicar': { tags: ['soft-skills', 'carreira'], category: 'core' },
    'how-speak-patrick-winston-giving-talks-matter': { tags: ['soft-skills', 'carreira'], category: 'core' },
    'art-communicate-ronycoder': { tags: ['soft-skills', 'carreira'], category: 'core' },
    'dario-amodei-scaling-rl-agi-future-anthropic': { tags: ['ia-2026', 'agentic-engineering'], category: 'core' },
  };

  function loadIndex() {
    return fetch(fallbackUrl, { cache: 'no-cache' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)));
  }

  function slugFromHref(href) {
    const m = href.match(/\/([^\/]+)\.html$/);
    return m ? m[1] : null;
  }

  function buildSlugLookup(nodes) {
    const map = Object.create(null);
    for (const n of nodes) {
      const ptSlug = slugFromHref(n.url_pt || '');
      const enSlug = slugFromHref(n.url_en || '');
      if (ptSlug) map[ptSlug] = n;
      if (enSlug) map[enSlug] = n;
    }
    return map;
  }

  function injectTagPillsIntoCard(card, node) {
    if (!node || !node.tags || !node.tags.length) return;
    if (card.querySelector('.tags')) return;
    const wrap = document.createElement('div');
    wrap.className = 'tags';
    for (const t of node.tags) {
      const a = document.createElement('a');
      a.href = '#tag-' + t;
      a.className = 'tag';
      a.dataset.tag = t;
      a.textContent = '#' + t;
      a.addEventListener('click', (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        applyFilter(t);
      });
      wrap.appendChild(a);
    }
    card.appendChild(wrap);
    // Annotate card for filtering
    card.dataset.tags = node.tags.join(' ');
    card.dataset.category = node.category || 'core';
  }

  function moveLateralCards(container, lateralCards) {
    if (!lateralCards.length) return;
    const heading = document.createElement('div');
    heading.className = 'section-title lateral';
    heading.textContent = isEN ? LATERAL_TITLE_EN : LATERAL_TITLE_PT;
    const hint = document.createElement('span');
    hint.className = 'lateral-hint';
    hint.textContent = isEN ? '— ' + LATERAL_HINT_EN : '— ' + LATERAL_HINT_PT;
    heading.appendChild(hint);
    container.appendChild(heading);
    for (const card of lateralCards) container.appendChild(card);
  }

  function buildFilterBar(barEl, allTags) {
    const tags = Array.from(allTags).sort();
    for (const t of tags) {
      const a = document.createElement('a');
      a.href = '#tag-' + t;
      a.className = 'tag';
      a.dataset.tag = t;
      a.textContent = '#' + t;
      a.addEventListener('click', (ev) => {
        ev.preventDefault();
        applyFilter(t);
      });
      barEl.appendChild(a);
    }
    // wire "all" button
    const allBtn = barEl.querySelector('[data-tag="all"]');
    if (allBtn) {
      allBtn.addEventListener('click', (ev) => {
        ev.preventDefault();
        applyFilter('all');
      });
    }
  }

  function applyFilter(tag) {
    const cards = document.querySelectorAll('.page-index .card');
    cards.forEach((c) => {
      if (tag === 'all') {
        c.hidden = false;
        return;
      }
      const tags = (c.dataset.tags || '').split(/\s+/);
      c.hidden = !tags.includes(tag);
    });
    document.querySelectorAll('.tag-bar .tag').forEach((el) => {
      el.classList.toggle('is-active', el.dataset.tag === tag);
    });
    // Hide lateral heading if all lateral cards are filtered out
    const lateralHeading = document.querySelector('.section-title.lateral');
    if (lateralHeading) {
      const lateralVisible = Array.from(
        document.querySelectorAll('.page-index .card[data-category="lateral"]')
      ).some((c) => !c.hidden);
      lateralHeading.hidden = !lateralVisible && tag !== 'all';
    }
  }

  function init() {
    const barEl = document.getElementById('tag-bar');
    if (!barEl) return; // page without tag bar
    const container = document.querySelector('.page-index .container') || document.body;

    loadIndex()
      .then((data) => {
        const lookup = buildSlugLookup(data.nodes || []);
        const cards = Array.from(document.querySelectorAll('.page-index .card'));
        const lateralCards = [];
        const allTags = new Set();

        for (const card of cards) {
          const href = card.getAttribute('href') || '';
          const slug = slugFromHref(href);
          if (!slug) continue;
          // Static data-tags emitted by build_moc.py wins over the JSON
          // (visible to crawlers without JS, also makes filtering work
          // even if the fetch fails).
          let node = null;
          if (card.dataset.tags) {
            node = {
              tags: card.dataset.tags.split(/\s+/).filter(Boolean),
              category: card.dataset.category || 'core',
            };
          } else {
            node = lookup[slug];
            if (!node && ORPHAN_TAGS[slug]) {
              node = { tags: ORPHAN_TAGS[slug].tags, category: ORPHAN_TAGS[slug].category };
            }
          }
          if (!node) continue;
          injectTagPillsIntoCard(card, node);
          (node.tags || []).forEach((t) => allTags.add(t));
          if ((node.category || 'core') === 'lateral') {
            lateralCards.push(card);
          }
        }

        moveLateralCards(container, lateralCards);
        buildFilterBar(barEl, allTags);

        // honor #tag-foo deep link
        const m = location.hash.match(/^#tag-(.+)$/);
        if (m) applyFilter(decodeURIComponent(m[1]));
      })
      .catch((err) => {
        // Silent: tags are progressive enhancement.
        console && console.warn && console.warn('[tags] load failed', err);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

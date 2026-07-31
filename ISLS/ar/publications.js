(function () {
  var fallbackPublications = window.NSLS_PUBLICATIONS_BILINGUAL || [];
  var output = document.querySelector('[data-publications-output]');
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[data-publication-filter]'));

  if (!output) return;

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  var MONTHS_AR = ['كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول'];

  function formatDate(iso) {
    if (!iso) return '';
    var parts = String(iso).split('-');
    var year = parts[0];
    var month = parseInt(parts[1], 10);
    var day = parts[2] ? parseInt(parts[2], 10) : null;
    var monthName = MONTHS_AR[month - 1];
    return day ? (day + ' ' + monthName + ' ' + year) : (monthName + ' ' + year);
  }

  function normalizeArabicPath(value) {
    if (!value || /^https?:/i.test(value) || value.charAt(0) === '#') return value;
    if (value.indexOf('../') === 0 || value.indexOf('/') === 0) return value;
    return '../' + value;
  }

  function flattenItem(item) {
    var flat = Object.assign({}, item, item.ar || {});
    flat._isoDate = item.date || '';
    flat.date = formatDate(item.date);
    flat.image = normalizeArabicPath(flat.image);
    flat.url = normalizeArabicPath(flat.url);
    flat.pdf = normalizeArabicPath(flat.pdf);
    flat.file = normalizeArabicPath(flat.file);
    flat.downloadUrl = normalizeArabicPath(flat.downloadUrl);
    return flat;
  }

  function publicationFormat(item) {
    return item.publicationFormat || (item.pdf || item.file || item.downloadUrl ? 'pdf' : item.external ? 'external' : 'page');
  }

  function publicationUrl(item) {
    if (item.slug) {
      return 'publications/' + encodeURIComponent(item.slug) + '/';
    }
    return item.url || '#';
  }

  function linkAttrs(item) {
    return !item.slug && publicationFormat(item) === 'external' ? ' target="_blank" rel="noopener"' : '';
  }

  function topicLinks(item) {
    return (item.topics || []).map(function (topic) {
      return '<a href="#publication-list">' + escapeHtml(topic) + '</a>';
    }).join(', ');
  }

  function metaLine(item) {
    var parts = [item.source, item.date].filter(Boolean).map(escapeHtml);
    return parts.join(' <span>&middot;</span> ');
  }

  function imageMarkup(item, className) {
    if (item.image) {
      return '<a class="' + className + '" href="' + escapeHtml(publicationUrl(item)) + '"' + linkAttrs(item) + '>' +
        '<img src="' + escapeHtml(item.image) + '" alt="' + escapeHtml(item.imageAlt || item.title) + '">' +
        '</a>';
    }

    if (publicationFormat(item) === 'pdf') {
      return '<a class="' + className + ' publication-pdf-thumb" href="' + escapeHtml(publicationUrl(item)) + '" aria-label="' + escapeHtml(item.title) + '">' +
        '<span></span>' +
        '</a>';
    }

    return '<a class="' + className + ' publication-thumb-mark" href="' + escapeHtml(publicationUrl(item)) + '"' + linkAttrs(item) + ' aria-label="' + escapeHtml(item.title) + '">' +
      escapeHtml(item.mark || 'NSLS') +
      '</a>';
  }

  function featureMarkup(item) {
    return '<article class="publication-feature-card">' +
      imageMarkup(item, 'publication-feature-image') +
      '<div class="publication-feature-copy">' +
        '<span class="publication-pill">' + escapeHtml(item.label) + '</span>' +
        '<h2><a href="' + escapeHtml(publicationUrl(item)) + '"' + linkAttrs(item) + '>' + escapeHtml(item.title) + '</a></h2>' +
        '<p>' + escapeHtml(item.description) + '</p>' +
        '<p class="publication-meta">' + metaLine(item) + ' <span>&middot;</span> ' + topicLinks(item) + '</p>' +
      '</div>' +
    '</article>';
  }

  function rowMarkup(item) {
    return '<article class="publication-row">' +
      imageMarkup(item, 'publication-thumb') +
      '<div class="publication-row-copy">' +
        '<span class="publication-pill">' + escapeHtml(item.label) + '</span>' +
        '<h2><a href="' + escapeHtml(publicationUrl(item)) + '"' + linkAttrs(item) + '>' + escapeHtml(item.title) + '</a></h2>' +
        '<p>' + escapeHtml(item.description) + '</p>' +
      '</div>' +
      '<div class="publication-row-meta">' +
        '<p>' + metaLine(item) + '</p>' +
        '<p>' + topicLinks(item) + '</p>' +
      '</div>' +
    '</article>';
  }

  function setActive(filter) {
    tabs.forEach(function (tab) {
      var isActive = tab.getAttribute('data-publication-filter') === filter;
      tab.setAttribute('aria-current', isActive ? 'page' : 'false');
    });
  }

  function typeRank(item) {
    var order = { 'policy-paper': 0, memo: 1, commentary: 2, analysis: 2, 'institutional-note': 3 };
    return Object.prototype.hasOwnProperty.call(order, item.type) ? order[item.type] : 4;
  }

  function sortedForDisplay(items) {
    return items.slice().sort(function (a, b) {
      if (!!a.featured !== !!b.featured) return a.featured ? -1 : 1;
      if (a._isoDate !== b._isoDate) return a._isoDate < b._isoDate ? 1 : -1;
      return typeRank(a) - typeRank(b);
    });
  }

  var publications = fallbackPublications.map(flattenItem);

  function render(filter) {
    var visible = filter === 'all'
      ? publications.slice()
      : publications.filter(function (item) { return item.type === filter; });

    visible = sortedForDisplay(visible);
    setActive(filter);

    if (!visible.length) {
      output.innerHTML = '<p class="publication-empty">لا توجد منشورات في هذا التصنيف بعد.</p>';
      return;
    }

    var html = featureMarkup(visible[0]);
    visible.slice(1).forEach(function (item) {
      html += rowMarkup(item);
    });
    html += '<a class="publications-more" href="contact.html#general">اقرأ أحدث أعمال فريق الباحثين لدينا. <span>&larr;</span></a>';
    output.innerHTML = html;
  }

  function filterFromHash() {
    var hash = (window.location.hash || '').replace('#', '');
    return ['memo', 'commentary', 'analysis', 'policy-paper', 'institutional-note'].indexOf(hash) >= 0 ? hash : 'all';
  }

  function currentFilter() {
    var active = tabs.find(function (tab) {
      return tab.getAttribute('aria-current') === 'page';
    });
    return active ? active.getAttribute('data-publication-filter') : filterFromHash();
  }

  function normalizeData(data) {
    var raw = data && Array.isArray(data.publications) ? data.publications : fallbackPublications;
    return raw.map(flattenItem);
  }

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var filter = tab.getAttribute('data-publication-filter') || 'all';
      if (filter === 'all') {
        history.replaceState(null, '', window.location.pathname + '#publication-list');
      } else {
        history.replaceState(null, '', window.location.pathname + '#' + filter);
      }
      render(filter);
    });
  });

  render(filterFromHash());

  fetch('../content/publications-bilingual.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('Publication data unavailable');
      return response.json();
    })
    .then(function (data) {
      publications = normalizeData(data);
      render(currentFilter());
    })
    .catch(function () {
      publications = fallbackPublications.map(flattenItem);
      render(currentFilter());
    });
})();

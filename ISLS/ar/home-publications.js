(function () {
  var fallbackPublications = window.NSLS_PUBLICATIONS_BILINGUAL || [];
  var output = document.querySelector('[data-home-publications-output]');
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
    flat.pdf = normalizeArabicPath(flat.pdf);
    flat.file = normalizeArabicPath(flat.file);
    flat.downloadUrl = normalizeArabicPath(flat.downloadUrl);
    return flat;
  }

  function publicationFormat(item) {
    return item.publicationFormat || (item.pdf || item.file || item.downloadUrl ? 'pdf' : item.external ? 'external' : 'page');
  }

  function publicationUrl(item) {
    if (item.slug) return 'publications/' + encodeURIComponent(item.slug) + '/';
    return item.url || '#';
  }

  function typeRank(item) {
    var order = { 'policy-paper': 0, memo: 1, commentary: 2, analysis: 2, 'institutional-note': 3 };
    return Object.prototype.hasOwnProperty.call(order, item.type) ? order[item.type] : 4;
  }

  function sortedForHome(items) {
    return items.slice().sort(function (a, b) {
      if (!!a.featured !== !!b.featured) return a.featured ? -1 : 1;
      if (a._isoDate !== b._isoDate) return a._isoDate < b._isoDate ? 1 : -1;
      return typeRank(a) - typeRank(b);
    }).slice(0, 3);
  }

  function normalizeData(data) {
    var raw = data && Array.isArray(data.publications) ? data.publications : fallbackPublications;
    return raw.map(flattenItem);
  }

  function topicSummary(item) {
    return (item.topics || []).slice(0, 1).join('، ');
  }

  function metaLine(item) {
    return [item.source, item.date, topicSummary(item)].filter(Boolean).map(escapeHtml).join(' &middot; ');
  }

  function visualMarkup(item) {
    if (item.image) {
      return '<img src="' + escapeHtml(item.image) + '" alt="' + escapeHtml(item.imageAlt || item.title) + '">';
    }
    if (publicationFormat(item) === 'pdf') {
      return '<div class="analysis-list-mark publication-pdf-thumb" aria-hidden="true"><span></span></div>';
    }
    return '<div class="analysis-list-mark" aria-hidden="true">' + escapeHtml(item.mark || 'NSLS') + '</div>';
  }

  function cardMarkup(item, index) {
    var extra = index === 0 && !item.image ? ' no-image-feature' : '';
    return '<a class="analysis-list-item' + extra + '" href="' + escapeHtml(publicationUrl(item)) + '">' +
      visualMarkup(item) +
      '<div>' +
        '<span>' + escapeHtml(item.label || item.type || 'منشور') + '</span>' +
        '<h3>' + escapeHtml(item.title) + '</h3>' +
        '<p>' + metaLine(item) + '</p>' +
        (index === 0 && item.description ? '<small>' + escapeHtml(item.description) + '</small>' : '') +
      '</div>' +
    '</a>';
  }

  function render(items) {
    var visible = sortedForHome(items);
    if (!visible.length) {
      output.innerHTML = '';
      return;
    }
    output.innerHTML = visible.map(cardMarkup).join('') +
      '<a class="analysis-list-more" href="publications.html">اقرأ أحدث أعمال فريق الباحثين لدينا. <span>&larr;</span></a>';
  }

  render(normalizeData({ publications: fallbackPublications }));

  fetch('../content/publications-bilingual.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('Publication data unavailable');
      return response.json();
    })
    .then(function (data) { render(normalizeData(data)); })
    .catch(function () { render(normalizeData({ publications: fallbackPublications })); });
})();

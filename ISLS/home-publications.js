(function () {
  var fallbackPublications = window.NSLS_PUBLICATIONS || [];
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

  var MONTHS = {
    jan: 0, january: 0, feb: 1, february: 1, mar: 2, march: 2, apr: 3, april: 3,
    may: 4, jun: 5, june: 5, jul: 6, july: 6, aug: 7, august: 7,
    sep: 8, sept: 8, september: 8, oct: 9, october: 9, nov: 10, november: 10, dec: 11, december: 11
  };

  function dateValue(item) {
    var raw = String(item.date || '').trim();
    var match = /^([A-Za-z]+)\s+(\d{1,2})?,?\s*(\d{4})$/.exec(raw);
    if (match) {
      var monthKey = match[1].toLowerCase();
      if (Object.prototype.hasOwnProperty.call(MONTHS, monthKey)) {
        var day = match[2] ? parseInt(match[2], 10) : 1;
        var year = parseInt(match[3], 10);
        return Date.UTC(year, MONTHS[monthKey], day);
      }
    }
    var t = Date.parse(raw);
    return isNaN(t) ? 0 : t;
  }

  function sortedForHome(items) {
    return items.slice().sort(function (a, b) {
      if (!!a.featured !== !!b.featured) return a.featured ? -1 : 1;
      var dateDelta = dateValue(b) - dateValue(a);
      if (dateDelta) return dateDelta;
      return typeRank(a) - typeRank(b);
    }).slice(0, 3);
  }

  function topicSummary(item) {
    return (item.topics || []).slice(0, 1).join(', ');
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
        '<span>' + escapeHtml(item.label || item.type || 'Publication') + '</span>' +
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
      '<a class="analysis-list-more" href="publications.html">Read the latest work from our team of researchers. <span>&rarr;</span></a>';
  }

  function normalizeData(data) {
    return data && Array.isArray(data.publications) ? data.publications : fallbackPublications;
  }

  render(fallbackPublications);

  fetch('content/publications.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('Publication data unavailable');
      return response.json();
    })
    .then(function (data) { render(normalizeData(data)); })
    .catch(function () { render(fallbackPublications); });
})();

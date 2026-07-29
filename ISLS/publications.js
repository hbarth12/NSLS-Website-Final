(function () {
  var fallbackPublications = window.NSLS_PUBLICATIONS || [];
  var publications = fallbackPublications.slice();
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

  function publicationFormat(item) {
    return item.publicationFormat || (item.pdf || item.file || item.downloadUrl ? 'pdf' : item.external ? 'external' : 'page');
  }

  function publicationUrl(item) {
    if (item.slug) {
      return 'publication.html?slug=' + encodeURIComponent(item.slug);
    }
    return item.url || '#';
  }

  function linkAttrs(item) {
    return '';
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

  function sortedForDisplay(items) {
    return items.slice().sort(function (a, b) {
      if (!!a.featured !== !!b.featured) return a.featured ? -1 : 1;
      var dateDelta = dateValue(b) - dateValue(a);
      if (dateDelta) return dateDelta;
      return typeRank(a) - typeRank(b);
    });
  }

  function render(filter) {
    var visible = filter === 'all'
      ? publications.slice()
      : publications.filter(function (item) { return item.type === filter; });

    visible = sortedForDisplay(visible);
    setActive(filter);

    if (!visible.length) {
      output.innerHTML = '<p class="publication-empty">No publications in this category yet.</p>';
      return;
    }

    var html = featureMarkup(visible[0]);
    visible.slice(1).forEach(function (item) {
      html += rowMarkup(item);
    });
    html += '<a class="publications-more" href="contact.html#request">Read the latest work from our researchers. <span>&rarr;</span></a>';
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
    return data && Array.isArray(data.publications) ? data.publications : fallbackPublications;
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

  fetch('content/publications.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('Publication data unavailable');
      return response.json();
    })
    .then(function (data) {
      publications = normalizeData(data);
      render(currentFilter());
    })
    .catch(function () {
      publications = fallbackPublications;
      render(currentFilter());
    });
})();

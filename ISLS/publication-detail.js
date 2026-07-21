(function () {
  var fallbackPublications = window.NSLS_PUBLICATIONS || [];
  var output = document.querySelector('[data-publication-detail]');
  if (!output) return;

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function inlineMarkdown(value) {
    return escapeHtml(value).replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }

  function markdownToHtml(value) {
    var blocks = String(value || '').trim().split(/\n{2,}/).filter(Boolean);
    if (!blocks.length) return '';
    return blocks.map(function (block) {
      var text = block.trim();
      if (/^###\s+/.test(text)) return '<h3>' + inlineMarkdown(text.replace(/^###\s+/, '')) + '</h3>';
      if (/^##\s+/.test(text)) return '<h2>' + inlineMarkdown(text.replace(/^##\s+/, '')) + '</h2>';
      if (/^#\s+/.test(text)) return '<h2>' + inlineMarkdown(text.replace(/^#\s+/, '')) + '</h2>';
      return '<p>' + inlineMarkdown(text).replace(/\n/g, '<br>') + '</p>';
    }).join('');
  }

  function slugFromUrl() {
    var params = new URLSearchParams(window.location.search);
    return params.get('slug') || params.get('id') || '';
  }

  function topicLine(item) {
    return (item.topics || []).filter(Boolean).map(escapeHtml).join(', ');
  }

  function fileUrl(item) {
    return item.pdf || item.file || item.downloadUrl || '';
  }

  function render(item) {
    var format = item.publicationFormat || (item.pdf ? 'pdf' : item.external ? 'external' : 'page');
    var download = fileUrl(item);
    var body = item.body || item.content || item.articleBody || '';
    var image = item.image ? '<figure class="publication-detail-image"><img src="' + escapeHtml(item.image) + '" alt="' + escapeHtml(item.imageAlt || item.title) + '"></figure>' : '';
    var pdfBlock = download ? '<aside class="publication-download"><p>Download</p><a class="button primary" href="' + escapeHtml(download) + '" target="_blank" rel="noopener">' + escapeHtml(item.pdfLabel || 'Download PDF') + '</a></aside>' : '';
    var externalBlock = format === 'external' && item.url ? '<p><a class="button primary" href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">Read at ' + escapeHtml(item.source || 'source') + '</a></p>' : '';
    var article = body ? markdownToHtml(body) : '<p>' + escapeHtml(item.description || '') + '</p>';

    document.title = item.title + ' | Network for Syrian Legislative Studies';
    output.innerHTML =
      '<header class="publication-detail-hero">' +
        '<a class="publication-back" href="publications.html">Back to publications</a>' +
        '<span class="publication-pill">' + escapeHtml(item.label || item.type || 'Publication') + '</span>' +
        '<h1>' + escapeHtml(item.title) + '</h1>' +
        '<p class="publication-detail-deck">' + escapeHtml(item.description || '') + '</p>' +
        '<p class="publication-meta">' + [item.source, item.date, topicLine(item)].filter(Boolean).map(escapeHtml).join(' <span>&middot;</span> ') + '</p>' +
      '</header>' +
      image +
      '<div class="publication-detail-grid">' +
        '<div class="publication-detail-body">' + article + externalBlock + '</div>' +
        '<div class="publication-detail-aside">' + pdfBlock + '<div class="publication-detail-note"><p>Publication format</p><strong>' + escapeHtml(format === 'pdf' ? 'PDF report' : format === 'external' ? 'External analysis' : 'Website article') + '</strong></div></div>' +
      '</div>';
  }

  function normalizeData(data) {
    return data && Array.isArray(data.publications) ? data.publications : fallbackPublications;
  }

  function load() {
    var slug = slugFromUrl();
    var renderFrom = function (items) {
      var item = items.find(function (entry) { return entry.slug === slug; });
      if (!item) {
        output.innerHTML = '<p class="publication-empty">Publication not found. <a href="publications.html">Return to publications.</a></p>';
        return;
      }
      render(item);
    };

    fetch('content/publications.json', { cache: 'no-cache' })
      .then(function (response) {
        if (!response.ok) throw new Error('Publication data unavailable');
        return response.json();
      })
      .then(function (data) { renderFrom(normalizeData(data)); })
      .catch(function () { renderFrom(fallbackPublications); });
  }

  load();
})();

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


  function normalizeArabicPath(value) {
    if (!value || /^https?:/i.test(value) || value.charAt(0) === '#') return value;
    if (value.indexOf('../') === 0 || value.indexOf('/') === 0) return value;
    return '../' + value;
  }

  function fileUrl(item) {
    return normalizeArabicPath(item.pdf || item.file || item.downloadUrl || '');
  }


  function publicationUrl(item) {
    if (item.slug) return 'publication.html?slug=' + encodeURIComponent(item.slug);
    return item.url || '#';
  }

  function recentItems(current, items) {
    return items.filter(function (entry) {
      return entry.slug !== current.slug;
    }).slice(0, 3);
  }

  function recentCard(item) {
    return '<a class="publication-recent-card" href="' + escapeHtml(publicationUrl(item)) + '">' +
      '<span class="publication-pill">' + escapeHtml(item.label || item.type || 'Publication') + '</span>' +
      '<h3>' + escapeHtml(item.title) + '</h3>' +
      '<p>' + escapeHtml([item.source, item.date].filter(Boolean).join(' · ')) + '</p>' +
    '</a>';
  }

  function renderPdf(item, items) {
    var download = fileUrl(item);
    var body = item.body || item.content || item.articleBody || item.description || '';
    var article = markdownToHtml(body);
    var recent = recentItems(item, items).map(recentCard).join('');
    var fileSize = item.pdfLabel ? item.pdfLabel.replace(/^Download PDF\s*/i, '').replace(/^تحميل PDF\s*/i, '').replace(/[()]/g, '') : 'PDF';
    var readTime = item.readTime || '';

    document.body.classList.add('pdf-publication-page');
    document.title = item.title + ' | Network for Syrian Legislative Studies';
    output.innerHTML =
      '<nav class="publication-breadcrumb" aria-label="Breadcrumb">' +
        '<a href="index.html">الرئيسية</a><span>/</span><a href="publications.html">المنشورات</a><span>/</span><a href="publications.html#policy-paper">Policy Papers</a>' +
      '</nav>' +
      '<section class="policy-paper-hero">' +
        '<div class="policy-paper-copy">' +
          '<span class="publication-pill policy-paper-pill">' + escapeHtml(item.label || 'Policy Paper') + '</span>' +
          '<h1>' + escapeHtml(item.title) + '</h1>' +
          '<div class="policy-paper-rule" aria-hidden="true"></div>' +
          '<p class="policy-paper-meta"><span>' + escapeHtml(item.author || '') + '</span><span>' + escapeHtml(item.date || '') + '</span></p>' +
          '<div class="policy-paper-summary">' + article + '</div>' +
          '<div class="policy-paper-actions policy-paper-actions-final">' +
            (download ? '<a class="button primary policy-paper-download policy-paper-action-tile" href="' + escapeHtml(download) + '" target="_blank" rel="noopener">تحميل PDF</a>' : '') +
            '<div class="policy-paper-stat policy-paper-action-tile"><span>مدة القراءة</span><strong>' + escapeHtml(readTime || 'تقرير') + '</strong></div>' +
            '<div class="policy-paper-stat policy-paper-action-tile"><span>حجم الملف</span><strong>' + escapeHtml(fileSize || 'PDF') + '</strong></div>' +
          '</div>' +
        '</div>' +
        '<aside class="publication-paper-preview policy-paper-cover" aria-label="Policy paper cover preview"><div><h2>' + escapeHtml(item.title) + '</h2><p>' + escapeHtml(item.author || '') + '</p><hr><strong>' + escapeHtml(item.label || 'Policy Paper') + '</strong><span>' + escapeHtml(item.date || '') + '</span><em>NSLS</em></div></aside>' +
      '</section>' +
      '<section class="other-publications" aria-labelledby="other-publications-title">' +
        '<div class="other-publications-heading">' +
          '<p class="section-kicker">أحدث الأعمال</p>' +
          '<h2 id="other-publications-title">منشورات حديثة أخرى</h2>' +
        '</div>' +
        '<div class="other-publications-grid">' + recent + '</div>' +
      '</section>';
  }

  function render(item, items) {
    var format = item.publicationFormat || (item.pdf ? 'pdf' : item.external ? 'external' : 'page');
    if (format === 'pdf') {
      renderPdf(item, items || []);
      return;
    }
    var download = fileUrl(item);
    var body = item.body || item.content || item.articleBody || '';
    var metaItems = [item.date, item.author, item.readTime, item.source, topicLine(item)].filter(Boolean).map(escapeHtml).join(' <span>&middot;</span> ');
    var imageSrc = normalizeArabicPath(item.image);
    var image = imageSrc ? '<figure class="publication-detail-image"><img src="' + escapeHtml(imageSrc) + '" alt="' + escapeHtml(item.imageAlt || item.title) + '"></figure>' : '';
    var pdfBlock = download ? '<aside class="publication-download"><p>Download</p><a class="button primary" href="' + escapeHtml(download) + '" target="_blank" rel="noopener">' + escapeHtml(item.pdfLabel || 'Download PDF') + '</a></aside>' : '';
    var externalBlock = format === 'external' && item.url ? '<p><a class="button primary" href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">Read more at ' + escapeHtml(item.source || 'source') + '</a></p>' : '';
    var article = body ? markdownToHtml(body) : '<p>' + escapeHtml(item.description || '') + '</p>';
    var paperPreview = format === 'pdf' ? '<aside class="publication-paper-preview" aria-label="Policy paper cover preview"><div><h2>' + escapeHtml(item.title) + '</h2><p>' + escapeHtml(item.author || '') + '</p><hr><strong>' + escapeHtml(item.label || 'Policy Paper') + '</strong><span>' + escapeHtml(item.date || '') + '</span><em>NSLS</em></div></aside>' : '';

    document.body.classList.remove('pdf-publication-page');
    document.body.classList.toggle('external-publication-page', format === 'external');
    document.title = item.title + ' | Network for Syrian Legislative Studies';
    output.innerHTML =
      '<header class="publication-detail-hero">' +
        '<a class="publication-back" href="publications.html">Back to publications</a>' +
        '<span class="publication-pill publication-detail-label">' + escapeHtml(item.label || item.type || 'Publication') + '</span>' +
        '<h1>' + escapeHtml(item.title) + '</h1>' +
        '<p class="publication-detail-deck">' + escapeHtml(item.description || '') + '</p>' +
        '<p class="publication-meta">' + metaItems + '</p>' +
      '</header>' +
      image +
      '<div class="publication-detail-grid">' +
        '<div class="publication-detail-body">' + article + externalBlock + '</div>' +
        '<div class="publication-detail-aside">' + paperPreview + pdfBlock + '<div class="publication-detail-note"><p>Publication format</p><strong>' + escapeHtml(format === 'pdf' ? 'PDF report' : format === 'external' ? 'External commentary' : 'Website article') + '</strong></div></div>' +
      '</div>';
  }

  function normalizeData(data) {
    var items = data && Array.isArray(data.publications) ? data.publications : fallbackPublications;
    return items.map(function (item) {
      var copy = Object.assign({}, item);
      copy.image = normalizeArabicPath(copy.image);
      copy.url = normalizeArabicPath(copy.url);
      copy.pdf = normalizeArabicPath(copy.pdf);
      copy.file = normalizeArabicPath(copy.file);
      copy.downloadUrl = normalizeArabicPath(copy.downloadUrl);
      return copy;
    });
  }

  function load() {
    var slug = slugFromUrl();
    var renderFrom = function (items) {
      var item = items.find(function (entry) { return entry.slug === slug; });
      if (!item) {
        output.innerHTML = '<p class="publication-empty">Publication not found. <a href="publications.html">Return to publications.</a></p>';
        return;
      }
      render(item, items);
    };

    fetch('../content/publications-ar.json', { cache: 'no-cache' })
      .then(function (response) {
        if (!response.ok) throw new Error('Publication data unavailable');
        return response.json();
      })
      .then(function (data) { renderFrom(normalizeData(data)); })
      .catch(function () { renderFrom(normalizeData({ publications: fallbackPublications })); });
  }

  load();
})();

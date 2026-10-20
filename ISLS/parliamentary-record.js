(function () {
  // Reads only parliamentary-record-data.js, which
  // scripts/generate-parliamentary-record.py writes in the same run as the
  // session pages -- never the raw content JSON -- so a session can't be
  // listed before its page exists.
  var sessions = window.NSLS_PARLIAMENTARY_RECORD || [];
  var output = document.querySelector('[data-record-output]');
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[data-record-type]'));
  var tagSelect = document.querySelector('[data-record-tag]');

  if (!output) return;

  var LANG = document.documentElement.lang === 'ar' ? 'ar' : 'en';
  var TYPES = ['plenary', 'committee', 'other'];

  var CONFIG = {
    en: {
      dir: 'ltr',
      months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
      formatDate: function (monthName, day, year) {
        return day ? (monthName + ' ' + day + ', ' + year) : (monthName + ' ' + year);
      },
      pagePath: function (slug, lang) {
        return (lang === 'ar' ? 'ar/' : '') + 'parliamentary-record/' + encodeURIComponent(slug) + '/';
      },
      session: 'Session',
      speakers: 'Speakers: ',
      placeholder: 'Placeholder',
      empty: 'No sessions match this filter yet.',
      separator: ', ',
    },
    ar: {
      dir: 'rtl',
      months: ['كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول'],
      formatDate: function (monthName, day, year) {
        return day ? (day + ' ' + monthName + ' ' + year) : (monthName + ' ' + year);
      },
      pagePath: function (slug, lang) {
        return (lang === 'en' ? '../' : '') + 'parliamentary-record/' + encodeURIComponent(slug) + '/';
      },
      session: 'الجلسة',
      speakers: 'المتحدثون: ',
      placeholder: 'تجريبي',
      empty: 'لا توجد جلسات تطابق هذا التصنيف بعد.',
      separator: '، ',
    },
  };

  // Shown on a card whose session exists only in the other language: the
  // card is written in that language, so its badge is too.
  var ONLY_IN = { en: 'English only', ar: 'بالعربية فقط' };

  var config = CONFIG[LANG];

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function bdi(value) {
    return value ? '<bdi>' + escapeHtml(value) + '</bdi>' : '';
  }

  function formatDate(iso, lang) {
    if (!iso) return '';
    var conf = CONFIG[lang];
    var parts = String(iso).split('-');
    var month = parseInt(parts[1], 10);
    var day = parts[2] ? parseInt(parts[2], 10) : null;
    return conf.formatDate(conf.months[month - 1], day, parts[0]);
  }

  // Each card is shown in the page's language when that language exists,
  // otherwise in the language that does (with an "only" badge).
  function view(session) {
    var lang = session[LANG] ? LANG : (LANG === 'en' ? 'ar' : 'en');
    if (!session[lang]) return null;
    return {
      session: session,
      lang: lang,
      foreign: lang !== LANG,
      block: session[lang],
      href: config.pagePath(session.slug, lang),
    };
  }

  var views = sessions.map(view).filter(Boolean).sort(function (a, b) {
    if (a.session.date !== b.session.date) return a.session.date < b.session.date ? 1 : -1;
    return (parseInt(b.session.sessionNumber, 10) || 0) - (parseInt(a.session.sessionNumber, 10) || 0);
  });

  function tagHref(tag) {
    return '?tag=' + encodeURIComponent(tag) + '#record-list';
  }

  function rowMarkup(v) {
    var conf = CONFIG[v.lang];
    var s = v.session;
    var b = v.block;
    var langAttrs = v.foreign ? ' lang="' + v.lang + '" dir="' + conf.dir + '"' : '';
    var pills = '<span class="publication-pill" dir="auto">' + escapeHtml(b.typeLabel) + '</span>';
    if (v.foreign) pills += ' <span class="publication-pill record-only-pill">' + escapeHtml(ONLY_IN[v.lang]) + '</span>';
    if (s.placeholder) pills += ' <span class="publication-pill record-placeholder-pill">' + escapeHtml(conf.placeholder) + '</span>';

    var meta = [bdi(formatDate(s.date, v.lang))];
    if (s.sessionNumber) meta.push(/^\d+$/.test(s.sessionNumber) ? escapeHtml(conf.session) + ' ' + bdi(s.sessionNumber) : bdi(s.sessionNumber));

    // Tag links filter this listing, so only offer them for the page's own
    // language; a foreign card's tags are shown as plain text.
    var tags = (b.tags || []).map(function (tag) {
      return v.foreign ? bdi(tag) : '<a href="' + escapeHtml(tagHref(tag)) + '" data-tag="' + escapeHtml(tag) + '">' + escapeHtml(tag) + '</a>';
    }).join(conf.separator);

    var speakers = (b.speakers || []).length
      ? '<p class="record-row-speakers" dir="auto">' + escapeHtml(conf.speakers) + (b.speakers || []).map(bdi).join(conf.separator) + '</p>'
      : '';

    var day = s.date ? String(parseInt(s.date.split('-')[2] || '', 10) || '') : '';
    var monthYear = s.date ? formatDate(s.date.slice(0, 7), v.lang) : '';

    return '<article class="publication-row record-row' + (v.foreign ? ' record-row-foreign' : '') + '"' + langAttrs + '>' +
      '<a class="publication-thumb record-thumb" href="' + escapeHtml(v.href) + '" aria-hidden="true" tabindex="-1">' +
        (day ? '<strong>' + escapeHtml(day) + '</strong>' : '') + '<span>' + escapeHtml(monthYear) + '</span>' +
      '</a>' +
      '<div class="publication-row-copy">' +
        '<div class="record-pills">' + pills + '</div>' +
        '<h2 dir="auto"><a href="' + escapeHtml(v.href) + '">' + escapeHtml(b.title) + '</a></h2>' +
        '<p dir="auto">' + escapeHtml(b.summary) + '</p>' +
        speakers +
      '</div>' +
      '<div class="publication-row-meta">' +
        '<p dir="' + conf.dir + '">' + meta.join(' <span>&middot;</span> ') + '</p>' +
        (tags ? '<p dir="' + conf.dir + '">' + tags + '</p>' : '') +
      '</div>' +
    '</article>';
  }

  function readState() {
    var params = new URLSearchParams(window.location.search);
    var type = params.get('type');
    return {
      type: TYPES.indexOf(type) >= 0 ? type : 'all',
      tag: params.get('tag') || '',
    };
  }

  function writeState(state) {
    var params = new URLSearchParams();
    if (state.type !== 'all') params.set('type', state.type);
    if (state.tag) params.set('tag', state.tag);
    var query = params.toString();
    history.replaceState(null, '', window.location.pathname + (query ? '?' + query : '') + '#record-list');
  }

  function fillTags(selected) {
    if (!tagSelect) return;
    var seen = {};
    views.forEach(function (v) {
      if (v.foreign) return;
      (v.block.tags || []).forEach(function (tag) { seen[tag] = true; });
    });
    var tags = Object.keys(seen).sort(function (a, b) { return a.localeCompare(b, LANG); });
    if (selected && !seen[selected]) tags.unshift(selected);
    var first = tagSelect.options[0];
    tagSelect.innerHTML = '';
    tagSelect.appendChild(first);
    tags.forEach(function (tag) {
      var option = document.createElement('option');
      option.value = tag;
      option.textContent = tag;
      tagSelect.appendChild(option);
    });
    tagSelect.value = selected;
  }

  function render(state) {
    tabs.forEach(function (tab) {
      tab.setAttribute('aria-current', tab.getAttribute('data-record-type') === state.type ? 'page' : 'false');
    });
    if (tagSelect) tagSelect.value = state.tag;

    var visible = views.filter(function (v) {
      if (state.type !== 'all' && v.session.type !== state.type) return false;
      if (state.tag && (v.foreign || (v.block.tags || []).indexOf(state.tag) < 0)) return false;
      return true;
    });

    output.innerHTML = visible.length
      ? visible.map(rowMarkup).join('')
      : '<p class="publication-empty">' + escapeHtml(config.empty) + '</p>';
  }

  var state = readState();

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      state.type = tab.getAttribute('data-record-type') || 'all';
      writeState(state);
      render(state);
    });
  });

  if (tagSelect) {
    tagSelect.addEventListener('change', function () {
      state.tag = tagSelect.value;
      writeState(state);
      render(state);
    });
  }

  output.addEventListener('click', function (event) {
    var link = event.target.closest ? event.target.closest('a[data-tag]') : null;
    if (!link) return;
    event.preventDefault();
    state.tag = link.getAttribute('data-tag');
    writeState(state);
    render(state);
    document.getElementById('record-list').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  fillTags(state.tag);
  render(state);
})();

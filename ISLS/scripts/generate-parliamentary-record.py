#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates the Parliamentary Record section from
ISLS/content/parliamentary-record-bilingual.json:

  ISLS/parliamentary-record/<slug>/index.html      (English session page)
  ISLS/ar/parliamentary-record/<slug>/index.html   (Arabic session page)
  ISLS/parliamentary-record-data.js                (listing data, both languages)

and the block of ISLS/sitemap.xml between the
<!-- BEGIN GENERATED PARLIAMENTARY RECORD --> / <!-- END GENERATED
PARLIAMENTARY RECORD --> markers.

A language is "published" for a session only when that language has both
a title and a transcript. Unpublished languages get no page, no sitemap
entry and no hreflang alternate; the listing in that language shows the
session as a card in the language that does exist ("English only" /
"بالعربية فقط") linking to the existing page.

The listing pages (parliamentary-record.html, ar/parliamentary-record.html)
read parliamentary-record-data.js only -- never the raw JSON -- and that file
is written in the same run as the pages, so the listing can never link to
a session page that hasn't been generated yet. It deliberately carries no
transcript text, so the listing stays small however long transcripts get.

Entries with "placeholder": true get <meta name="robots" content="noindex">
and are left out of sitemap.xml.

Run: python3 ISLS/scripts/generate-parliamentary-record.py
"""
import importlib.util
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content' / 'parliamentary-record-bilingual.json'
CHROME = json.loads((ROOT / 'content' / 'site-chrome.json').read_text(encoding='utf-8'))
DATA_JS = ROOT / 'parliamentary-record-data.js'
SITEMAP = ROOT / 'sitemap.xml'
SITE_URL = 'https://www.nsls.network'
SECTION = 'parliamentary-record'
SITEMAP_BEGIN_MARKER = '<!-- BEGIN GENERATED PARLIAMENTARY RECORD -->'
SITEMAP_END_MARKER = '<!-- END GENERATED PARLIAMENTARY RECORD -->'

# Reuse the publication generator's text helpers (escaping, <bdi> isolation,
# inline Markdown, date formatting) instead of copying them. The module is
# only imported, never run, so publication pages are unaffected.
_spec = importlib.util.spec_from_file_location(
    'generate_publication_pages', Path(__file__).with_name('generate-publication-pages.py'))
pubgen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pubgen)
escape_html = pubgen.escape_html
bdi = pubgen.bdi
inline_markdown = pubgen.inline_markdown
format_date = pubgen.format_date

TYPE_LABELS = {
    'en': {'plenary': 'Plenary', 'committee': 'Committee', 'other': 'Other'},
    'ar': {'plenary': 'جلسة عامة', 'committee': 'جلسة لجنة', 'other': 'أخرى'},
}

LANGS = {
    'en': {
        'output_root': ROOT,
        'url_path': '',
        'html_lang': 'en',
        'html_dir': 'ltr',
        'body_extra_class': '',
        'own_prefix': '../../',
        'true_prefix': '../../',
        'other_lang_prefix': '../../ar/',
        'arabic_font_link': '',
        'site_name': 'Network for Syrian Legislative Studies',
        'list_separator': ', ',
        'toggle_label': 'العربية',
        'strings': {
            'back': 'Back to Parliamentary Record',
            'session': 'Session',
            'download_pdf': 'Download PDF',
            'download_label': 'Download',
            'watch_video': 'Watch source video',
            'source_label': 'Source',
            'speakers_label': 'Speakers',
            'tags_label': 'Tags',
            'note_label': 'Accuracy and translation note',
            'transcript_heading': 'Transcript',
            'studio_label': 'Studio commentary',
            'placeholder_banner': 'PLACEHOLDER SESSION — sample content for previewing the layout. '
                                  'Not indexed by search engines. Delete this entry in '
                                  '{cms_path} before launch.',
            'default_description': 'Transcript of a public session of the Syrian People’s Assembly, '
                                   'from the Network for Syrian Legislative Studies.',
            'record_name': 'Parliamentary Record',
        },
    },
    'ar': {
        'output_root': ROOT / 'ar',
        'url_path': 'ar/',
        'html_lang': 'ar',
        'html_dir': 'rtl',
        'body_extra_class': ' arabic-page',
        'own_prefix': '../../',
        'true_prefix': '../../../',
        'other_lang_prefix': '../../../',
        'arabic_font_link': pubgen.LANGS['ar']['arabic_font_link'],
        'site_name': 'الشبكة السورية للدراسات التشريعية',
        'list_separator': '، ',
        'toggle_label': 'English',
        'strings': {
            'back': 'العودة إلى السجل البرلماني',
            'session': 'الجلسة',
            'download_pdf': 'تحميل PDF',
            'download_label': 'تحميل',
            'watch_video': 'مشاهدة الفيديو المصدر',
            'source_label': 'المصدر',
            'speakers_label': 'المتحدثون',
            'tags_label': 'الوسوم',
            'note_label': 'ملاحظة حول الدقة والترجمة',
            'transcript_heading': 'النص الكامل',
            'studio_label': 'تعليق الاستوديو',
            'placeholder_banner': 'جلسة تجريبية مؤقتة — محتوى نموذجي لمعاينة التصميم فقط، '
                                  'ولا تفهرسه محركات البحث. احذف هذا الإدخال من {cms_path} '
                                  'قبل الإطلاق.',
            'default_description': 'النص الكامل لجلسة علنية لمجلس الشعب السوري، '
                                   'من الشبكة السورية للدراسات التشريعية.',
            'record_name': 'السجل البرلماني',
        },
    },
}


# ---------------------------------------------------------------------------
# Publication state per language
# ---------------------------------------------------------------------------

def is_published(entry, lang):
    block = entry.get(lang) or {}
    return bool((block.get('title') or '').strip() and (block.get('transcript') or '').strip())


def published_langs(entry):
    return [lang for lang in ('en', 'ar') if is_published(entry, lang)]


def page_url(entry, lang):
    return SITE_URL + '/' + LANGS[lang]['url_path'] + SECTION + '/' + entry['slug'] + '/'


def type_label(entry, lang):
    block = entry.get(lang) or {}
    return block.get('typeLabel') or TYPE_LABELS[lang].get(entry.get('type')) or TYPE_LABELS[lang]['other']


# ---------------------------------------------------------------------------
# Transcript rendering
#
# Paragraphs are separated by blank lines; each paragraph is one turn:
#
#   [00:00:45] Speaker Name: remarks...
#   [00:12:30] [Studio] Presenter: commentary...
#   (The session is adjourned.)
#
# The timestamp and [Studio] / [استوديو] marker are optional. A paragraph
# without a "Name:" prefix renders as a plain, unattributed paragraph; one
# wrapped in parentheses renders as a procedural note. Consecutive studio
# turns are grouped into one visually distinct block.
# ---------------------------------------------------------------------------

TIMESTAMP_RE = re.compile(r'^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*')
STUDIO_RE = re.compile(r'^\[(?:studio|استوديو|الاستوديو)\]\s*', re.I)
# Up to 60 characters of name (no "!", "?" or newline, so a sentence that
# happens to contain a colon isn't mistaken for a speaker), then a colon.
# Bold markers around the name ("**Name:**" or "**Name**:") are tolerated.
SPEAKER_RE = re.compile(r'^\*{0,2}([^:\n!?؟*]{1,60}?)\*{0,2}\s*:\*{0,2}\s+(.+)$', re.S)
CHUNK_SIZE = 40


def first_strong_dir(text, fallback):
    """Direction of the first strongly-directional character, the same rule
    dir="auto" applies -- computed here so it can skip the speaker name."""
    for ch in text:
        kind = unicodedata.bidirectional(ch)
        if kind in ('R', 'AL'):
            return 'rtl'
        if kind == 'L':
            return 'ltr'
    return fallback


def parse_turn(paragraph):
    text = paragraph.strip()
    time = None
    studio = False
    m = TIMESTAMP_RE.match(text)
    if m:
        time, text = m.group(1), text[m.end():]
    m = STUDIO_RE.match(text)
    if m:
        studio, text = True, text[m.end():]
    if time is None:
        # Allow the marker before the timestamp, too.
        m = TIMESTAMP_RE.match(text)
        if m:
            time, text = m.group(1), text[m.end():]
    speaker = None
    m = SPEAKER_RE.match(text)
    if m and len(m.group(1).split()) <= 8:
        speaker, text = m.group(1).strip(), m.group(2).strip()
    procedural = speaker is None and text.startswith('(') and text.endswith(')')
    return {'time': time, 'studio': studio, 'speaker': speaker, 'text': text, 'procedural': procedural}


def render_turn(turn, page_dir):
    direction = first_strong_dir(turn['text'], page_dir)
    classes = ['turn']
    if turn['procedural']:
        classes.append('turn-procedural')
    head = ''
    if turn['time']:
        head += '<span class="turn-time" dir="ltr">' + escape_html(turn['time']) + '</span> '
    if turn['speaker']:
        head += '<strong class="turn-speaker"><bdi>' + escape_html(turn['speaker']) + '</bdi>:</strong> '
    body = inline_markdown(turn['text']).replace('\n', '<br>')
    return '<p class="' + ' '.join(classes) + '" dir="' + direction + '">' + head + body + '</p>'


def render_transcript(value, lang):
    page_dir = LANGS[lang]['html_dir']
    studio_label = LANGS[lang]['strings']['studio_label']
    paragraphs = [p for p in re.split(r'\n{2,}', str(value or '').strip()) if p.strip()]

    # Group consecutive studio turns, then split into chunks the browser can
    # skip laying out while they're off-screen (content-visibility: auto).
    units = []
    studio_run = []
    for paragraph in paragraphs:
        turn = parse_turn(paragraph)
        if turn['studio']:
            studio_run.append(render_turn(turn, page_dir))
            continue
        if studio_run:
            units.append('<div class="turn-studio" role="group" aria-label="' + escape_html(studio_label) + '">'
                         '<p class="turn-studio-label">' + escape_html(studio_label) + '</p>'
                         + ''.join(studio_run) + '</div>')
            studio_run = []
        units.append(render_turn(turn, page_dir))
    if studio_run:
        units.append('<div class="turn-studio" role="group" aria-label="' + escape_html(studio_label) + '">'
                     '<p class="turn-studio-label">' + escape_html(studio_label) + '</p>'
                     + ''.join(studio_run) + '</div>')

    chunks = [units[i:i + CHUNK_SIZE] for i in range(0, len(units), CHUNK_SIZE)]
    return ''.join('<div class="transcript-chunk">' + ''.join(c) + '</div>' for c in chunks)


# ---------------------------------------------------------------------------
# Page chrome, built from content/site-chrome.json so the nav stays in one place
# ---------------------------------------------------------------------------

def render_header(lang, toggle_href):
    chrome = CHROME[lang]
    conf = LANGS[lang]
    other = 'ar' if lang == 'en' else 'en'
    nav = '\n'.join(
        '        <a href="' + conf['own_prefix'] + item['href'] + '"'
        + (' aria-current="page"' if item['key'] == SECTION else '') + '>' + item['label'] + '</a>'
        for item in chrome['nav'])
    brand = chrome['brand']
    return (
        '    <header class="site-header">\n'
        '      <a class="brand" href="' + conf['own_prefix'] + brand['href'] + '" aria-label="' + brand['ariaLabel'] + '">\n'
        '        <span class="brand-mark">' + brand['mark'] + '</span>\n'
        '        <span>\n'
        '          <strong>' + brand['line1'] + '</strong>\n'
        '          <small>' + brand['line2'] + '</small>\n'
        '        </span>\n'
        '      </a>\n'
        '      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav-panel" aria-label="Menu">\n'
        '        <span></span><span></span><span></span>\n'
        '      </button>\n'
        '      <a class="language-toggle" href="' + escape_html(toggle_href) + '" lang="' + LANGS[other]['html_lang']
        + '" dir="' + LANGS[other]['html_dir'] + '">' + conf['toggle_label'] + '</a>\n'
        '      <div class="site-nav-panel" id="site-nav-panel">\n'
        '      <nav class="primary-nav" aria-label="Primary navigation">\n'
        + nav + '\n'
        '      </nav>\n'
        '      <a class="header-action" href="' + conf['own_prefix'] + 'contact.html#general">' + chrome['headerCta'] + '</a>\n'
        '      </div>\n'
        '    </header>\n'
    )


def render_footer(lang):
    chrome = CHROME[lang]
    conf = LANGS[lang]
    footer = chrome['footer']
    brand = chrome['brand']
    network = '\n'.join(
        '          <a href="' + conf['own_prefix'] + item['href'] + '">' + item['label'] + '</a>'
        for item in footer['networkLinks'])
    connect = []
    for item in footer['connectLinks']:
        if item.get('external'):
            connect.append('            <a href="' + item['href'] + '" target="_blank" rel="noopener">' + item['label'] + '</a>')
        else:
            connect.append('            <a href="' + conf['own_prefix'] + item['href'] + '">' + item['label'] + '</a>')
    return (
        '    <footer class="site-footer">\n'
        '      <div class="footer-primary">\n'
        '        <a class="brand footer-brand" href="' + conf['own_prefix'] + brand['href'] + '">\n'
        '          <span class="brand-mark">' + brand['mark'] + '</span>\n'
        '          <span>\n'
        '            <strong>' + brand['line1'] + '</strong>\n'
        '            <small>' + brand['line2'] + '</small>\n'
        '          </span>\n'
        '        </a>\n'
        '        <p>' + footer['tagline'] + '</p>\n'
        '      </div>\n'
        '      <nav class="footer-links" aria-label="Footer navigation">\n'
        '        <div>\n'
        '          <h2>' + footer['networkHeading'] + '</h2>\n'
        + network + '\n'
        '        </div>\n'
        '        <div class="footer-connect">\n'
        '          <div class="footer-connect-links">\n'
        '            <h2>' + footer['connectHeading'] + '</h2>\n'
        + '\n'.join(connect) + '\n'
        '          </div>\n'
        '          <a class="footer-cta" href="' + conf['own_prefix'] + 'contact.html#general">' + footer['footerCta'] + '</a>\n'
        '        </div>\n'
        '      </nav>\n'
        '      <div class="footer-bottom">\n'
        '        <p>' + footer['copyright'] + '</p>\n'
        '        <p>' + footer['subtagline'] + '</p>\n'
        '      </div>\n'
        '    </footer>\n'
    )


NAV_SCRIPT = """    <script>
      (function () {
        var toggle = document.querySelector('.nav-toggle');
        var panel = document.getElementById('site-nav-panel');
        if (!toggle || !panel) return;
        toggle.addEventListener('click', function () {
          var open = toggle.getAttribute('aria-expanded') === 'true';
          toggle.setAttribute('aria-expanded', String(!open));
          panel.classList.toggle('is-open', !open);
        });
        document.addEventListener('keydown', function (event) {
          if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
            toggle.setAttribute('aria-expanded', 'false');
            panel.classList.remove('is-open');
            toggle.focus();
          }
        });
        document.addEventListener('click', function (event) {
          if (toggle.getAttribute('aria-expanded') !== 'true') return;
          if (panel.contains(event.target) || toggle.contains(event.target)) return;
          toggle.setAttribute('aria-expanded', 'false');
          panel.classList.remove('is-open');
        });
      })();
    </script>
"""


# ---------------------------------------------------------------------------
# Session page
# ---------------------------------------------------------------------------

def asset_href(path, conf):
    if not path:
        return ''
    if re.match(r'^(https?:)?//', path):
        return path
    return conf['true_prefix'] + path


def render_main(entry, lang):
    conf = LANGS[lang]
    s = conf['strings']
    block = entry.get(lang) or {}

    session_no = (entry.get('sessionNumber') or '').strip()
    meta_parts = [bdi(format_date(entry.get('date'), lang))]
    if session_no:
        meta_parts.append(escape_html(s['session']) + ' ' + bdi(session_no))
    meta = ' <span>&middot;</span> '.join(p for p in meta_parts if p)

    banner = ''
    if entry.get('placeholder'):
        # The CMS path is English in both languages; isolate it so it stays
        # in one piece inside the Arabic sentence.
        cms_path = '<bdi dir="ltr">Pages CMS → Parliamentary Record → “PLACEHOLDER – delete me”</bdi>'
        banner = ('<p class="record-placeholder-banner" role="note">'
                  + escape_html(s['placeholder_banner']).replace('{cms_path}', cms_path) + '</p>')

    note = (
        '<aside class="record-note" aria-label="' + escape_html(s['note_label']) + '">'
        '<p class="record-note-label">' + escape_html(s['note_label']) + '</p>'
        '<p dir="auto">' + inline_markdown(block.get('accuracyNote')) + '</p>'
        '</aside>'
    )

    actions = []
    pdf_path = block.get('pdf')
    if pdf_path:
        actions.append(
            '<a class="button primary" href="' + escape_html(asset_href(pdf_path, conf)) + '" download="'
            + escape_html(os.path.basename(pdf_path)) + '" target="_blank" rel="noopener">'
            + escape_html(block.get('pdfLabel') or s['download_pdf']) + '</a>')
    if entry.get('sourceVideoUrl'):
        actions.append(
            '<a class="button secondary" href="' + escape_html(entry['sourceVideoUrl'])
            + '" target="_blank" rel="noopener">' + escape_html(s['watch_video']) + '</a>')
    actions_html = '<div class="record-actions">' + ''.join(actions) + '</div>' if actions else ''

    aside_parts = []
    speakers = [x for x in (block.get('speakers') or []) if x]
    if speakers:
        aside_parts.append(
            '<div class="publication-detail-note"><p>' + escape_html(s['speakers_label']) + '</p><ul class="record-list">'
            + ''.join('<li dir="auto">' + escape_html(x) + '</li>' for x in speakers) + '</ul></div>')
    tags = [x for x in (block.get('tags') or []) if x]
    if tags:
        aside_parts.append(
            '<div class="publication-detail-note"><p>' + escape_html(s['tags_label']) + '</p><div class="record-tags">'
            + ''.join('<a href="' + conf['own_prefix'] + SECTION + '.html?tag=' + escape_html(quote(x, safe=''))
                      + '#record-list" dir="auto">' + escape_html(x) + '</a>' for x in tags) + '</div></div>')
    if block.get('sourceCredit'):
        aside_parts.append(
            '<div class="publication-detail-note"><p>' + escape_html(s['source_label']) + '</p>'
            '<span class="record-source" dir="auto">' + inline_markdown(block['sourceCredit']) + '</span></div>')

    return (
        banner
        + '<header class="publication-detail-hero">'
        '<a class="publication-back" href="' + conf['own_prefix'] + SECTION + '.html">' + escape_html(s['back']) + '</a>'
        '<span class="publication-pill publication-detail-label">' + escape_html(type_label(entry, lang)) + '</span>'
        '<h1 dir="auto">' + escape_html(block.get('title')) + '</h1>'
        '<p class="publication-detail-deck" dir="auto">' + escape_html(block.get('summary') or '') + '</p>'
        '<p class="publication-meta">' + meta + '</p>'
        '</header>'
        + note + actions_html
        + '<div class="publication-detail-grid">'
        '<section class="publication-detail-body record-transcript" aria-labelledby="transcript-title">'
        '<h2 id="transcript-title">' + escape_html(s['transcript_heading']) + '</h2>'
        + render_transcript(block.get('transcript'), lang)
        + '</section>'
        '<div class="publication-detail-aside">' + ''.join(aside_parts) + '</div>'
        '</div>'
    )


def hreflang_links(entry):
    langs = published_langs(entry)
    lines = ['    <link rel="alternate" hreflang="' + lang + '" href="' + page_url(entry, lang) + '">' for lang in langs]
    default = 'en' if 'en' in langs else langs[0]
    lines.append('    <link rel="alternate" hreflang="x-default" href="' + page_url(entry, default) + '">')
    return '\n'.join(lines)


def build_page(entry, lang):
    conf = LANGS[lang]
    s = conf['strings']
    block = entry.get(lang) or {}
    other = 'ar' if lang == 'en' else 'en'

    if is_published(entry, other):
        toggle_href = conf['other_lang_prefix'] + SECTION + '/' + entry['slug'] + '/'
    else:
        toggle_href = conf['other_lang_prefix'] + SECTION + '.html'

    title = block.get('title') + ' | ' + s['record_name'] + ' | ' + conf['site_name']
    description = block.get('summary') or s['default_description']
    robots = '\n    <meta name="robots" content="noindex">' if entry.get('placeholder') else ''

    return (
        '<!doctype html>\n'
        '<html lang="' + conf['html_lang'] + '" dir="' + conf['html_dir'] + '">\n'
        '  <head>\n'
        '    <meta charset="utf-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '    <title>' + escape_html(title) + '</title>\n'
        '    <meta name="description" content="' + escape_html(description) + '">' + robots + '\n'
        '    <link rel="canonical" href="' + page_url(entry, lang) + '">\n'
        + hreflang_links(entry) + '\n'
        '    <link rel="icon" href="' + conf['true_prefix'] + 'favicon.ico">\n'
        '    <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap" rel="stylesheet">'
        + conf['arabic_font_link'] + '\n'
        '    <link rel="stylesheet" href="' + conf['true_prefix'] + 'styles.css?v=final-actions-1">\n'
        '  </head>\n'
        '  <body class="isl-page publication-detail-page record-session-page' + conf['body_extra_class'] + '">\n'
        + render_header(lang, toggle_href)
        + NAV_SCRIPT + '\n'
        '    <main id="top">\n'
        '      <article class="publication-detail" lang="' + conf['html_lang'] + '" dir="' + conf['html_dir'] + '">\n'
        '        ' + render_main(entry, lang) + '\n'
        '      </article>\n'
        '    </main>\n\n'
        + render_footer(lang)
        + '  </body>\n'
        '</html>\n'
    )


# ---------------------------------------------------------------------------
# Listing data (no transcripts) and sitemap
# ---------------------------------------------------------------------------

def listing_record(entry):
    record = {
        'slug': entry['slug'],
        'date': entry.get('date') or '',
        'sessionNumber': entry.get('sessionNumber') or '',
        'type': entry.get('type') or 'other',
        'placeholder': bool(entry.get('placeholder')),
    }
    for lang in published_langs(entry):
        block = entry[lang]
        record[lang] = {
            'title': block.get('title') or '',
            'typeLabel': type_label(entry, lang),
            'summary': block.get('summary') or '',
            'speakers': [x for x in (block.get('speakers') or []) if x],
            'tags': [x for x in (block.get('tags') or []) if x],
        }
    return record


def write_data_js(items):
    records = [listing_record(e) for e in items if published_langs(e)]
    DATA_JS.write_text(
        '// Generated by scripts/generate-parliamentary-record.py -- do not edit by hand.\n'
        'window.NSLS_PARLIAMENTARY_RECORD = ' + json.dumps(records, ensure_ascii=False, indent=2) + ';\n',
        encoding='utf-8')
    print('Wrote ' + str(DATA_JS.relative_to(ROOT)) + ' (' + str(len(records)) + ' session(s)).')


def update_sitemap(items):
    text = SITEMAP.read_text(encoding='utf-8')
    pattern = re.compile(re.escape(SITEMAP_BEGIN_MARKER) + r'.*?' + re.escape(SITEMAP_END_MARKER), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit('sitemap.xml is missing the ' + SITEMAP_BEGIN_MARKER + ' / ' + SITEMAP_END_MARKER + ' markers.')

    entries = []
    for entry in items:
        if entry.get('placeholder'):
            continue
        for lang in published_langs(entry):
            lines = ['  <url>', '    <loc>' + pubgen.xml_escape(page_url(entry, lang)) + '</loc>']
            if entry.get('date'):
                lines.append('    <lastmod>' + entry['date'] + '</lastmod>')
            lines += ['    <changefreq>monthly</changefreq>', '    <priority>0.6</priority>', '  </url>']
            entries.append('\n'.join(lines))
    body = '\n'.join(entries)
    block = SITEMAP_BEGIN_MARKER + ('\n' + body + '\n' if body else '\n') + SITEMAP_END_MARKER
    new_text = pattern.sub(lambda _: block, text)
    if new_text != text:
        SITEMAP.write_text(new_text, encoding='utf-8')
        print('Updated ' + str(SITEMAP.relative_to(ROOT)) + ' with ' + str(len(entries)) + ' session URL(s).')
    else:
        print(str(SITEMAP.relative_to(ROOT)) + ' already up to date.')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
DATE_RE = re.compile(r'^\d{4}-\d{2}(?:-\d{2})?$')


def validate(items):
    errors = []
    seen = set()
    for i, entry in enumerate(items):
        label = entry.get('slug') or ('entry #' + str(i + 1))
        slug = entry.get('slug') or ''
        if not SLUG_RE.match(slug):
            errors.append(label + ': slug must be lowercase words separated by hyphens.')
        if slug in seen:
            errors.append(label + ': duplicate slug.')
        seen.add(slug)
        if not DATE_RE.match(entry.get('date') or ''):
            errors.append(label + ': date must be YYYY-MM-DD or YYYY-MM.')
        for lang in published_langs(entry):
            if not (entry[lang].get('accuracyNote') or '').strip():
                errors.append(label + ': the ' + ('English' if lang == 'en' else 'Arabic')
                              + ' transcript needs an accuracy/translation note.')
    if errors:
        for e in errors:
            print('::error::' + e if os.environ.get('GITHUB_ACTIONS') else 'ERROR: ' + e, file=sys.stderr)
        raise SystemExit('Parliamentary Record not generated: fix the errors above.')


def read_items():
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    items = data.get('sessions', []) if isinstance(data, dict) else data
    def newest_first(e):
        number = str(e.get('sessionNumber') or '')
        return (e.get('date') or '', int(number) if number.isdigit() else -1, number)
    return sorted(items, key=newest_first, reverse=True)


def main():
    items = read_items()
    validate(items)

    for lang, conf in LANGS.items():
        output_dir = conf['output_root'] / SECTION
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for entry in items:
            if not is_published(entry, lang):
                continue
            page_dir = output_dir / entry['slug']
            page_dir.mkdir(parents=True, exist_ok=True)
            out_file = page_dir / 'index.html'
            out_file.write_text(build_page(entry, lang), encoding='utf-8')
            print('Wrote ' + str(out_file.relative_to(ROOT)))

    write_data_js(items)
    update_sitemap(items)


if __name__ == '__main__':
    main()

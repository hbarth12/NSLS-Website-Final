#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates one static HTML page per publication, in both English and
Arabic, from ISLS/content/publications-bilingual.json:

  ISLS/publications/<slug>/index.html      (English)
  ISLS/ar/publications/<slug>/index.html   (Arabic)

Each page has a real <title>, <meta name="description">,
<link rel="canonical">, and the title/description/body/PDF link
rendered directly into the HTML -- visible without running any
JavaScript. Both language variants are produced by the same renderer
(parameterized by a small per-language strings/prefix table), rather
than by separate English/Arabic implementations.

When a publication has both an English and an Arabic PDF (and they're
different files), the page renders a small language picker next to
the download button; ISLS/pdf-picker.js (shared by both languages)
wires the picker to the download link.

Also keeps ISLS/sitemap.xml in sync: the block of <url> entries
between the <!-- BEGIN GENERATED PUBLICATIONS --> / <!-- END GENERATED
PUBLICATIONS --> markers is regenerated (both languages) on every run,
using each publication's shared, already-ISO `date` field for
<lastmod>. Everything else in sitemap.xml is left untouched.

Run: python3 ISLS/scripts/generate-publication-pages.py
"""
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content' / 'publications-bilingual.json'
SITEMAP = ROOT / 'sitemap.xml'
SITE_URL = 'https://www.nsls.network'
SITEMAP_BEGIN_MARKER = '<!-- BEGIN GENERATED PUBLICATIONS -->'
SITEMAP_END_MARKER = '<!-- END GENERATED PUBLICATIONS -->'

MONTHS_EN = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]
MONTHS_AR = [
    'كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران',
    'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول',
]


# ---------------------------------------------------------------------------
# Text helpers (ported 1:1 from the old publication-detail.js)
# ---------------------------------------------------------------------------

def escape_html(value):
    return (str(value or '')
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;'))


LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\s)]+)\)')
BOLD_RE = re.compile(r'\*\*([^\*]+)\*\*')
ITALIC_STAR_RE = re.compile(r'\*([^\*]+)\*')
ITALIC_UNDERSCORE_RE = re.compile(r'_([^_]+)_')


def inline_markdown(value):
    escaped = escape_html(value)

    # Links are pulled out into placeholders first so bold/italic markers
    # can't accidentally match underscores/asterisks inside a URL (common
    # in DOI links) and corrupt the href.
    links = []

    def store_link(m):
        links.append(
            '<a href="' + m.group(2) + '" target="_blank" rel="noopener">' + m.group(1) + '</a>'
        )
        return '\x00LINK%d\x00' % (len(links) - 1)

    text = LINK_RE.sub(store_link, escaped)
    text = BOLD_RE.sub(lambda m: '<strong>' + m.group(1) + '</strong>', text)
    text = ITALIC_STAR_RE.sub(lambda m: '<em>' + m.group(1) + '</em>', text)
    text = ITALIC_UNDERSCORE_RE.sub(lambda m: '<em>' + m.group(1) + '</em>', text)

    for i, link_html in enumerate(links):
        text = text.replace('\x00LINK%d\x00' % i, link_html)

    return text


def markdown_to_html(value):
    raw_blocks = re.split(r'\n{2,}', str(value or '').strip())
    blocks = [b for b in raw_blocks if b != '']
    if not blocks:
        return ''
    parts = []
    for block in blocks:
        text = block.strip()
        if re.match(r'^###\s+', text):
            parts.append('<h3>' + inline_markdown(re.sub(r'^###\s+', '', text)) + '</h3>')
        elif re.match(r'^##\s+', text):
            parts.append('<h2>' + inline_markdown(re.sub(r'^##\s+', '', text)) + '</h2>')
        elif re.match(r'^#\s+', text):
            parts.append('<h2>' + inline_markdown(re.sub(r'^#\s+', '', text)) + '</h2>')
        else:
            parts.append('<p>' + inline_markdown(text).replace('\n', '<br>') + '</p>')
    return ''.join(parts)


def format_date(iso_date, lang):
    if not iso_date:
        return ''
    parts = iso_date.split('-')
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2]) if len(parts) > 2 else None
    if lang == 'ar':
        month_name = MONTHS_AR[month - 1]
        return (str(day) + ' ' + month_name + ' ' + str(year)) if day else (month_name + ' ' + str(year))
    month_name = MONTHS_EN[month - 1]
    return (month_name + ' ' + str(day) + ', ' + str(year)) if day else (month_name + ' ' + str(year))


def pub_format(entry):
    fmt = entry.get('publicationFormat')
    if fmt:
        return fmt
    if entry.get('en', {}).get('pdf') or entry.get('ar', {}).get('pdf'):
        return 'pdf'
    if entry.get('external'):
        return 'external'
    return 'page'


# ---------------------------------------------------------------------------
# Per-language configuration: prefixes (relative-path depth from the
# generated file) and UI strings. This table is the entire "translation
# layer" -- the rendering logic below runs once for both languages.
# ---------------------------------------------------------------------------

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
        'strings': {
            'nav_home': 'Home',
            'nav_what_we_do': 'What We Do',
            'nav_publications': 'Publications',
            'nav_our_team': 'Our Team',
            'nav_contact': 'Contact',
            'get_in_touch': 'Get in Touch',
            'brand_line1': 'Network for Syrian',
            'brand_line2': 'Legislative Studies',
            'footer_tagline': "Independent research and practical legislative support for Syria's Parliament.",
            'footer_network_heading': 'Network',
            'footer_about': 'About',
            'footer_connect_heading': 'Connect',
            'footer_linkedin': 'LinkedIn',
            'footer_privacy': 'Privacy',
            'footer_copyright': '&copy; 2026 Network for Syrian Legislative Studies.',
            'footer_supporting': 'Supporting independent legislative research in Syria.',
            'language_toggle_label': 'العربية',
            'breadcrumb_home': 'Home',
            'breadcrumb_publications': 'Publications',
            'breadcrumb_policy_papers': 'Policy Papers',
            'back_to_publications': 'Back to publications',
            'download_pdf': 'Download PDF',
            'read_time_label': 'Read time',
            'file_size_label': 'File size',
            'report_fallback': 'Report',
            'recent_work_kicker': 'Recent Work',
            'other_recent_publications': 'Other Recent Publications',
            'download_label': 'Download',
            'read_more_at': 'Read more at ',
            'publication_format_label': 'Publication format',
            'format_pdf': 'PDF report',
            'format_external': 'External commentary',
            'format_page': 'Website article',
            'publication_fallback': 'Publication',
            'pdf_language_label': 'Language',
            'pdf_option_en': 'English',
            'pdf_option_ar': 'Arabic',
            'default_description': 'Publication from the Network for Syrian Legislative Studies.',
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
        'arabic_font_link': (
            '\n    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700'
            '&family=Noto+Naskh+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">'
        ),
        'site_name': 'الشبكة السورية للدراسات التشريعية',
        'strings': {
            'nav_home': 'الرئيسية',
            'nav_what_we_do': 'ماذا نفعل',
            'nav_publications': 'المنشورات',
            'nav_our_team': 'فريقنا',
            'nav_contact': 'اتصل بنا',
            'get_in_touch': 'تواصل معنا',
            'brand_line1': 'Network for Syrian',
            'brand_line2': 'Legislative Studies',
            'footer_tagline': 'بحث مستقل ودعم تشريعي عملي للبرلمان السوري.',
            'footer_network_heading': 'الشبكة',
            'footer_about': 'عن الشبكة',
            'footer_connect_heading': 'تواصل',
            'footer_linkedin': 'لينكدإن',
            'footer_privacy': 'الخصوصية',
            'footer_copyright': '&copy; 2026 الشبكة السورية للدراسات التشريعية.',
            'footer_supporting': 'دعم البحث التشريعي المستقل في سوريا.',
            'language_toggle_label': 'English',
            'breadcrumb_home': 'الرئيسية',
            'breadcrumb_publications': 'المنشورات',
            'breadcrumb_policy_papers': 'أوراق سياسات',
            'back_to_publications': 'العودة إلى المنشورات',
            'download_pdf': 'تحميل PDF',
            'read_time_label': 'مدة القراءة',
            'file_size_label': 'حجم الملف',
            'report_fallback': 'تقرير',
            'recent_work_kicker': 'أحدث الأعمال',
            'other_recent_publications': 'منشورات حديثة أخرى',
            'download_label': 'تحميل',
            'read_more_at': 'اقرأ المزيد على ',
            'publication_format_label': 'نوع المنشور',
            'format_pdf': 'تقرير PDF',
            'format_external': 'تعليق خارجي',
            'format_page': 'مقال على الموقع',
            'publication_fallback': 'منشور',
            'pdf_language_label': 'اللغة',
            'pdf_option_en': 'الإنجليزية',
            'pdf_option_ar': 'العربية',
            'default_description': 'منشور من الشبكة السورية للدراسات التشريعية.',
        },
    },
}


def asset_href(path, lang_conf):
    if not path:
        return ''
    if path.startswith('http://') or path.startswith('https://') or path.startswith('//'):
        return path
    return lang_conf['true_prefix'] + path


def own_href(page, lang_conf):
    return lang_conf['own_prefix'] + page


# ---------------------------------------------------------------------------
# PDF language-picker
# ---------------------------------------------------------------------------

def pdf_options(entry):
    """Returns [(lang, pdf_path), ...] for languages that actually have a
    PDF, collapsed to a single option if both languages point at the same
    file (nothing meaningful to pick between)."""
    opts = []
    for lang in ('en', 'ar'):
        pdf = entry.get(lang, {}).get('pdf')
        if pdf:
            opts.append((lang, pdf))
    if len(opts) == 2 and opts[0][1] == opts[1][1]:
        opts = opts[:1]
    return opts


def pdf_action_html(entry, lang, lang_conf, tile_class):
    opts = pdf_options(entry)
    if not opts:
        return ''

    strings = lang_conf['strings']
    opt_by_lang = dict(opts)

    # Default to this page's own language when it has a PDF; otherwise
    # fall back to whichever language does.
    default_lang = lang if lang in opt_by_lang else opts[0][0]
    default_href = asset_href(opt_by_lang[default_lang], lang_conf)
    default_filename = os.path.basename(opt_by_lang[default_lang])

    download_link = (
        '<a class="button primary policy-paper-download ' + tile_class + '" data-pdf-download '
        'href="' + escape_html(default_href) + '" download="' + escape_html(default_filename)
        + '" target="_blank" rel="noopener">' + escape_html(strings['download_pdf']) + '</a>'
    )

    if len(opts) < 2:
        return download_link

    option_tags = []
    for opt_lang, pdf_path in opts:
        href = asset_href(pdf_path, lang_conf)
        filename = os.path.basename(pdf_path)
        label = strings['pdf_option_en'] if opt_lang == 'en' else strings['pdf_option_ar']
        selected = ' selected' if opt_lang == default_lang else ''
        option_tags.append(
            '<option value="' + escape_html(href) + '" data-filename="' + escape_html(filename) + '"' + selected + '>'
            + escape_html(label) + '</option>'
        )

    select_control = (
        '<div class="policy-paper-pdf-select ' + tile_class + '">'
        '<label class="policy-paper-pdf-picker-label" for="pdf-language-select">' + escape_html(strings['pdf_language_label']) + '</label>'
        '<select id="pdf-language-select" data-pdf-select>' + ''.join(option_tags) + '</select>'
        '</div>'
    )
    return '<div class="policy-paper-pdf-picker" data-pdf-picker>' + select_control + download_link + '</div>'


# ---------------------------------------------------------------------------
# Body rendering (mirrors the old publication-detail.js render()/renderPdf())
# ---------------------------------------------------------------------------

def topic_line(entry, lang):
    parts = [escape_html(t) for t in (entry.get(lang, {}).get('topics') or []) if t]
    return ', '.join(parts)


def recent_items(current, items):
    return [x for x in items if x.get('slug') != current.get('slug')][:3]


def recent_card(item, lang, lang_conf):
    strings = lang_conf['strings']
    block = item.get(lang, {})
    href = '../' + item['slug'] + '/'
    meta = ' · '.join(p for p in [item.get('source'), format_date(item.get('date'), lang)] if p)
    return (
        '<a class="publication-recent-card" href="' + escape_html(href) + '">'
        '<span class="publication-pill">' + escape_html(block.get('label') or item.get('type') or strings['publication_fallback']) + '</span>'
        '<h3>' + escape_html(block.get('title')) + '</h3>'
        '<p>' + escape_html(meta) + '</p>'
        '</a>'
    )


def render_pdf_body(entry, items, lang, lang_conf):
    strings = lang_conf['strings']
    block = entry.get(lang, {})
    body = block.get('body') or block.get('description') or ''
    article = markdown_to_html(body)
    recent = ''.join(recent_card(x, lang, lang_conf) for x in recent_items(entry, items))
    read_time = block.get('readTime') or ''
    pdf_actions = pdf_action_html(entry, lang, lang_conf, 'policy-paper-action-tile')

    file_size = strings['report_fallback']
    pdf_label = block.get('pdfLabel') or ''
    if pdf_label:
        file_size = re.sub(r'^(Download PDF|تحميل PDF)\s*', '', pdf_label)
        file_size = re.sub(r'[()]', '', file_size).strip() or strings['report_fallback']

    return (
        '<nav class="publication-breadcrumb" aria-label="Breadcrumb">'
        '<a href="' + own_href('index.html', lang_conf) + '">' + escape_html(strings['breadcrumb_home']) + '</a><span>/</span>'
        '<a href="' + own_href('publications.html', lang_conf) + '">' + escape_html(strings['breadcrumb_publications']) + '</a><span>/</span>'
        '<a href="' + own_href('publications.html', lang_conf) + '#policy-paper">' + escape_html(strings['breadcrumb_policy_papers']) + '</a>'
        '</nav>'
        '<section class="policy-paper-hero">'
        '<div class="policy-paper-copy">'
        '<span class="publication-pill policy-paper-pill">' + escape_html(block.get('label') or strings['format_pdf']) + '</span>'
        '<h1>' + escape_html(block.get('title')) + '</h1>'
        '<div class="policy-paper-rule" aria-hidden="true"></div>'
        '<p class="policy-paper-meta"><span>' + escape_html(block.get('author') or '') + '</span>'
        '<span>' + escape_html(format_date(entry.get('date'), lang)) + '</span></p>'
        '<div class="policy-paper-summary">' + article + '</div>'
        '<div class="policy-paper-actions policy-paper-actions-final">'
        + pdf_actions
        + '<div class="policy-paper-stat policy-paper-action-tile"><span>' + escape_html(strings['read_time_label']) + '</span><strong>'
        + escape_html(read_time or strings['report_fallback']) + '</strong></div>'
        + '<div class="policy-paper-stat policy-paper-action-tile"><span>' + escape_html(strings['file_size_label']) + '</span><strong>'
        + escape_html(file_size) + '</strong></div>'
        + '</div>'
        '</div>'
        '<aside class="publication-paper-preview policy-paper-cover" aria-label="Policy paper cover preview"><div><h2>'
        + escape_html(block.get('title')) + '</h2><p>' + escape_html(block.get('author') or '') + '</p><hr><strong>'
        + escape_html(block.get('label') or strings['format_pdf']) + '</strong><span>' + escape_html(format_date(entry.get('date'), lang))
        + '</span><em>NSLS</em></div></aside>'
        '</section>'
        '<section class="other-publications" aria-labelledby="other-publications-title">'
        '<div class="other-publications-heading">'
        '<p class="section-kicker">' + escape_html(strings['recent_work_kicker']) + '</p>'
        '<h2 id="other-publications-title">' + escape_html(strings['other_recent_publications']) + '</h2>'
        '</div>'
        '<div class="other-publications-grid">' + recent + '</div>'
        '</section>'
    )


def render_body(entry, items, lang, lang_conf):
    strings = lang_conf['strings']
    block = entry.get(lang, {})
    fmt = pub_format(entry)
    body = block.get('body') or ''

    meta_parts = [
        format_date(entry.get('date'), lang), block.get('author'), block.get('readTime'),
        entry.get('source'), topic_line(entry, lang),
    ]
    meta_items = ' <span>&middot;</span> '.join(escape_html(p) for p in meta_parts if p)

    image_html = ''
    if entry.get('image'):
        image_html = (
            '<figure class="publication-detail-image"><img src="' + escape_html(asset_href(entry['image'], lang_conf))
            + '" alt="' + escape_html(block.get('imageAlt') or block.get('title')) + '"></figure>'
        )

    pdf_actions = pdf_action_html(entry, lang, lang_conf, 'button')
    pdf_block = ''
    if pdf_actions:
        pdf_block = '<aside class="publication-download"><p>' + escape_html(strings['download_label']) + '</p>' + pdf_actions + '</aside>'

    external_block = ''
    if fmt == 'external' and entry.get('url'):
        external_block = (
            '<p><a class="button primary" href="' + escape_html(entry['url'])
            + '" target="_blank" rel="noopener">' + escape_html(strings['read_more_at'])
            + escape_html(entry.get('source') or 'source') + '</a></p>'
        )

    article = markdown_to_html(body) if body else '<p>' + escape_html(block.get('description') or '') + '</p>'

    paper_preview = ''
    if fmt == 'pdf':
        paper_preview = (
            '<aside class="publication-paper-preview" aria-label="Policy paper cover preview"><div><h2>'
            + escape_html(block.get('title')) + '</h2><p>' + escape_html(block.get('author') or '') + '</p><hr><strong>'
            + escape_html(block.get('label') or strings['format_pdf']) + '</strong><span>' + escape_html(format_date(entry.get('date'), lang))
            + '</span><em>NSLS</em></div></aside>'
        )

    format_label = strings['format_pdf'] if fmt == 'pdf' else strings['format_external'] if fmt == 'external' else strings['format_page']

    return (
        '<header class="publication-detail-hero">'
        '<a class="publication-back" href="' + own_href('publications.html', lang_conf) + '">' + escape_html(strings['back_to_publications']) + '</a>'
        '<span class="publication-pill publication-detail-label">'
        + escape_html(block.get('label') or entry.get('type') or strings['publication_fallback']) + '</span>'
        '<h1>' + escape_html(block.get('title')) + '</h1>'
        '<p class="publication-detail-deck">' + escape_html(block.get('description') or '') + '</p>'
        '<p class="publication-meta">' + meta_items + '</p>'
        '</header>'
        + image_html +
        '<div class="publication-detail-grid">'
        '<div class="publication-detail-body">' + article + external_block + '</div>'
        '<div class="publication-detail-aside">' + paper_preview + pdf_block
        + '<div class="publication-detail-note"><p>' + escape_html(strings['publication_format_label']) + '</p><strong>'
        + escape_html(format_label) + '</strong></div></div>'
        '</div>'
    )


PAGE_TEMPLATE = """<!doctype html>
<html lang="{html_lang}" dir="{html_dir}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap" rel="stylesheet">{arabic_font_link}
    <link rel="stylesheet" href="{true_prefix}styles.css?v=final-actions-1">
  </head>
  <body class="{body_classes}">
    <header class="site-header">
      <a class="brand" href="{own_prefix}index.html" aria-label="Network for Syrian Legislative Studies home">
        <span class="brand-mark">NSLS</span>
        <span>
          <strong>{brand_line1}</strong>
          <small>{brand_line2}</small>
        </span>
      </a>
      <nav class="primary-nav" aria-label="Primary navigation">
        <a href="{own_prefix}index.html">{nav_home}</a>
        <a href="{own_prefix}what-we-do.html">{nav_what_we_do}</a>
        <a href="{own_prefix}publications.html" aria-current="page">{nav_publications}</a>
        <a href="{own_prefix}our-team.html">{nav_our_team}</a>
        <a href="{own_prefix}contact.html">{nav_contact}</a>
      </nav>
      <a class="language-toggle" href="{toggle_href}" lang="{toggle_lang}" dir="{toggle_dir}">{language_toggle_label}</a>
      <a class="header-action" href="{own_prefix}contact.html#general">{get_in_touch}</a>
    </header>

    <main id="top">
      <article class="publication-detail" data-publication-detail>
        {content}
      </article>
    </main>

    <footer class="site-footer">
      <div class="footer-primary">
        <a class="brand footer-brand" href="{own_prefix}index.html">
          <span class="brand-mark">NSLS</span>
          <span>
            <strong>{brand_line1}</strong>
            <small>{brand_line2}</small>
          </span>
        </a>
        <p>{footer_tagline}</p>
      </div>
      <nav class="footer-links" aria-label="Footer navigation">
        <div>
          <h2>{footer_network_heading}</h2>
          <a href="{own_prefix}index.html">{footer_about}</a>
          <a href="{own_prefix}what-we-do.html">{nav_what_we_do}</a>
          <a href="{own_prefix}publications.html">{nav_publications}</a>
          <a href="{own_prefix}our-team.html">{nav_our_team}</a>
        </div>
        <div class="footer-connect">
          <div class="footer-connect-links">
            <h2>{footer_connect_heading}</h2>
            <a href="{own_prefix}contact.html">{nav_contact}</a>
            <a href="https://www.linkedin.com/" target="_blank" rel="noopener">{footer_linkedin}</a>
            <a href="{own_prefix}privacy.html">{footer_privacy}</a>
          </div>
          <a class="footer-cta" href="{own_prefix}contact.html#general">{get_in_touch}</a>
        </div>
      </nav>
      <div class="footer-bottom">
        <p>{footer_copyright}</p>
        <p>{footer_supporting}</p>
      </div>
    </footer>
    <script src="{true_prefix}pdf-picker.js"></script>
  </body>
</html>
"""


def build_page(entry, items, lang):
    lang_conf = LANGS[lang]
    strings = lang_conf['strings']
    slug = entry['slug']
    fmt = pub_format(entry)
    block = entry.get(lang, {})

    title = (block.get('title') or '') + ' | ' + lang_conf['site_name']
    description = block.get('description') or strings['default_description']
    canonical = SITE_URL + '/' + lang_conf['url_path'] + 'publications/' + slug + '/'

    body_classes = 'isl-page publication-detail-page' + lang_conf['body_extra_class']
    if fmt == 'pdf':
        body_classes += ' pdf-publication-page'
    elif fmt == 'external':
        body_classes += ' external-publication-page'

    content = render_pdf_body(entry, items, lang, lang_conf) if fmt == 'pdf' else render_body(entry, items, lang, lang_conf)

    other_lang = 'ar' if lang == 'en' else 'en'
    other_conf = LANGS[other_lang]
    toggle_href = lang_conf['other_lang_prefix'] + 'publications/' + slug + '/'

    template_fields = dict(strings)
    template_fields.update({
        'html_lang': lang_conf['html_lang'],
        'html_dir': lang_conf['html_dir'],
        'title': escape_html(title),
        'description': escape_html(description),
        'canonical': canonical,
        'arabic_font_link': lang_conf['arabic_font_link'],
        'true_prefix': lang_conf['true_prefix'],
        'own_prefix': lang_conf['own_prefix'],
        'body_classes': body_classes,
        'site_name': escape_html(lang_conf['site_name']),
        'toggle_href': escape_html(toggle_href),
        'toggle_lang': other_conf['html_lang'],
        'toggle_dir': other_conf['html_dir'],
        'content': content,
    })

    return PAGE_TEMPLATE.format(**template_fields)


# ---------------------------------------------------------------------------
# Sitemap sync
# ---------------------------------------------------------------------------

def xml_escape(value):
    return (str(value or '')
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def sitemap_url_entry(entry, lang):
    lang_conf = LANGS[lang]
    loc = SITE_URL + '/' + lang_conf['url_path'] + 'publications/' + entry['slug'] + '/'
    lastmod = entry.get('date')

    lines = ['  <url>', '    <loc>' + xml_escape(loc) + '</loc>']
    if lastmod:
        lines.append('    <lastmod>' + lastmod + '</lastmod>')
    lines.append('    <changefreq>monthly</changefreq>')
    lines.append('    <priority>0.6</priority>')
    lines.append('  </url>')
    return '\n'.join(lines)


def update_sitemap(items):
    text = SITEMAP.read_text(encoding='utf-8')
    pattern = re.compile(re.escape(SITEMAP_BEGIN_MARKER) + r'.*?' + re.escape(SITEMAP_END_MARKER), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(
            'sitemap.xml is missing the ' + SITEMAP_BEGIN_MARKER + ' / ' + SITEMAP_END_MARKER + ' markers.'
        )

    entry_lines = []
    for item in items:
        entry_lines.append(sitemap_url_entry(item, 'en'))
        entry_lines.append(sitemap_url_entry(item, 'ar'))
    entries = '\n'.join(entry_lines)
    block = SITEMAP_BEGIN_MARKER + ('\n' + entries + '\n' if entries else '\n') + SITEMAP_END_MARKER
    new_text = pattern.sub(lambda _: block, text)

    if new_text != text:
        SITEMAP.write_text(new_text, encoding='utf-8')
        print('Updated ' + str(SITEMAP.relative_to(ROOT)) + ' with ' + str(len(items) * 2) + ' publication URL(s).')
    else:
        print(str(SITEMAP.relative_to(ROOT)) + ' already up to date.')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def read_items():
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    if isinstance(data, dict) and isinstance(data.get('publications'), list):
        return data['publications']
    return data


def main():
    items = read_items()

    seen = set()
    for it in items:
        if it['slug'] in seen:
            raise SystemExit('Duplicate publication slug: ' + it['slug'])
        seen.add(it['slug'])

    for lang, lang_conf in LANGS.items():
        output_dir = lang_conf['output_root'] / 'publications'
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for it in items:
            page_dir = output_dir / it['slug']
            page_dir.mkdir(parents=True, exist_ok=True)
            out_file = page_dir / 'index.html'
            out_file.write_text(build_page(it, items, lang), encoding='utf-8')
            print('Wrote ' + str(out_file.relative_to(ROOT)))

    print('Generated ' + str(len(items)) + ' publication(s) in ' + str(len(LANGS)) + ' language(s).')

    update_sitemap(items)


if __name__ == '__main__':
    main()

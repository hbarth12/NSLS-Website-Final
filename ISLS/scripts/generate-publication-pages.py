#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates one static HTML page per publication (ISLS/publications/<slug>/index.html)
from ISLS/content/publications.json, with a real <title>, <meta name="description">,
<link rel="canonical">, and the title/description/body/PDF link rendered directly
into the HTML. Mirrors the markup produced by publication-detail.js so the static
pages match the site's existing styling/layout.

Run: python3 ISLS/scripts/generate-publication-pages.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content' / 'publications.json'
OUTPUT_DIR = ROOT / 'publications'
SITE_URL = 'https://nsls.network'
UP = '../../'


def escape_html(value):
    return (str(value or '')
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;'))


LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\s)]+)\)')


def inline_markdown(value):
    escaped = escape_html(value)
    return LINK_RE.sub(
        lambda m: '<a href="' + m.group(2) + '" target="_blank" rel="noopener">' + m.group(1) + '</a>',
        escaped,
    )


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


def asset_href(path):
    if not path:
        return ''
    if path.startswith('http://') or path.startswith('https://') or path.startswith('//'):
        return path
    return UP + path


def file_url(item):
    return item.get('pdf') or item.get('file') or item.get('downloadUrl') or ''


def pub_format(item):
    fmt = item.get('publicationFormat')
    if fmt:
        return fmt
    if item.get('pdf'):
        return 'pdf'
    if item.get('external'):
        return 'external'
    return 'page'


def topic_line(item):
    parts = [escape_html(t) for t in (item.get('topics') or []) if t]
    return ', '.join(parts)


def recent_items(current, items):
    return [x for x in items if x.get('slug') != current.get('slug')][:3]


def publication_href(item):
    if item.get('slug'):
        return '../' + item['slug'] + '/'
    return item.get('url') or '#'


def recent_card(item):
    meta = ' · '.join(p for p in [item.get('source'), item.get('date')] if p)
    return (
        '<a class="publication-recent-card" href="' + escape_html(publication_href(item)) + '">'
        '<span class="publication-pill">' + escape_html(item.get('label') or item.get('type') or 'Publication') + '</span>'
        '<h3>' + escape_html(item.get('title')) + '</h3>'
        '<p>' + escape_html(meta) + '</p>'
        '</a>'
    )


def render_pdf_body(item, items):
    download = file_url(item)
    body = item.get('body') or item.get('content') or item.get('articleBody') or item.get('description') or ''
    article = markdown_to_html(body)
    recent = ''.join(recent_card(x) for x in recent_items(item, items))
    pdf_label = item.get('pdfLabel') or ''
    file_size = 'PDF'
    if pdf_label:
        file_size = re.sub(r'^تحميل PDF\s*', '', pdf_label, flags=re.I)
        file_size = re.sub(r'^Download PDF\s*', '', file_size, flags=re.I)
        file_size = re.sub(r'[()]', '', file_size)
    read_time = item.get('readTime') or ''
    download_action = ''
    if download:
        download_action = (
            '<a class="button primary policy-paper-download policy-paper-action-tile" href="'
            + escape_html(asset_href(download)) + '" target="_blank" rel="noopener">Download PDF</a>'
        )

    return (
        '<nav class="publication-breadcrumb" aria-label="Breadcrumb">'
        '<a href="' + UP + 'index.html">Home</a><span>/</span>'
        '<a href="' + UP + 'publications.html">Publications</a><span>/</span>'
        '<a href="' + UP + 'publications.html#policy-paper">Policy Papers</a>'
        '</nav>'
        '<section class="policy-paper-hero">'
        '<div class="policy-paper-copy">'
        '<span class="publication-pill policy-paper-pill">' + escape_html(item.get('label') or 'Policy Paper') + '</span>'
        '<h1>' + escape_html(item.get('title')) + '</h1>'
        '<div class="policy-paper-rule" aria-hidden="true"></div>'
        '<p class="policy-paper-meta"><span>' + escape_html(item.get('author') or '') + '</span>'
        '<span>' + escape_html(item.get('date') or '') + '</span></p>'
        '<div class="policy-paper-summary">' + article + '</div>'
        '<div class="policy-paper-actions policy-paper-actions-final">'
        + download_action
        + '<div class="policy-paper-stat policy-paper-action-tile"><span>Read time</span><strong>'
        + escape_html(read_time or 'Report') + '</strong></div>'
        + '<div class="policy-paper-stat policy-paper-action-tile"><span>File size</span><strong>'
        + escape_html(file_size or 'PDF') + '</strong></div>'
        + '</div>'
        '</div>'
        '<aside class="publication-paper-preview policy-paper-cover" aria-label="Policy paper cover preview"><div><h2>'
        + escape_html(item.get('title')) + '</h2><p>' + escape_html(item.get('author') or '') + '</p><hr><strong>'
        + escape_html(item.get('label') or 'Policy Paper') + '</strong><span>' + escape_html(item.get('date') or '')
        + '</span><em>NSLS</em></div></aside>'
        '</section>'
        '<section class="other-publications" aria-labelledby="other-publications-title">'
        '<div class="other-publications-heading">'
        '<p class="section-kicker">Recent Work</p>'
        '<h2 id="other-publications-title">Other Recent Publications</h2>'
        '</div>'
        '<div class="other-publications-grid">' + recent + '</div>'
        '</section>'
    )


def render_body(item, items):
    fmt = pub_format(item)
    download = file_url(item)
    body = item.get('body') or item.get('content') or item.get('articleBody') or ''
    meta_parts = [item.get('date'), item.get('author'), item.get('readTime'), item.get('source'), topic_line(item)]
    meta_items = ' <span>&middot;</span> '.join(escape_html(p) for p in meta_parts if p)

    image_html = ''
    if item.get('image'):
        image_html = (
            '<figure class="publication-detail-image"><img src="' + escape_html(asset_href(item['image']))
            + '" alt="' + escape_html(item.get('imageAlt') or item.get('title')) + '"></figure>'
        )

    pdf_block = ''
    if download:
        pdf_block = (
            '<aside class="publication-download"><p>Download</p><a class="button primary" href="'
            + escape_html(asset_href(download)) + '" target="_blank" rel="noopener">'
            + escape_html(item.get('pdfLabel') or 'Download PDF') + '</a></aside>'
        )

    external_block = ''
    if fmt == 'external' and item.get('url'):
        external_block = (
            '<p><a class="button primary" href="' + escape_html(item['url'])
            + '" target="_blank" rel="noopener">Read more at ' + escape_html(item.get('source') or 'source')
            + '</a></p>'
        )

    article = markdown_to_html(body) if body else '<p>' + escape_html(item.get('description') or '') + '</p>'

    paper_preview = ''
    if fmt == 'pdf':
        paper_preview = (
            '<aside class="publication-paper-preview" aria-label="Policy paper cover preview"><div><h2>'
            + escape_html(item.get('title')) + '</h2><p>' + escape_html(item.get('author') or '') + '</p><hr><strong>'
            + escape_html(item.get('label') or 'Policy Paper') + '</strong><span>' + escape_html(item.get('date') or '')
            + '</span><em>NSLS</em></div></aside>'
        )

    format_label = 'PDF report' if fmt == 'pdf' else 'External commentary' if fmt == 'external' else 'Website article'

    return (
        '<header class="publication-detail-hero">'
        '<a class="publication-back" href="' + UP + 'publications.html">Back to publications</a>'
        '<span class="publication-pill publication-detail-label">'
        + escape_html(item.get('label') or item.get('type') or 'Publication') + '</span>'
        '<h1>' + escape_html(item.get('title')) + '</h1>'
        '<p class="publication-detail-deck">' + escape_html(item.get('description') or '') + '</p>'
        '<p class="publication-meta">' + meta_items + '</p>'
        '</header>'
        + image_html +
        '<div class="publication-detail-grid">'
        '<div class="publication-detail-body">' + article + external_block + '</div>'
        '<div class="publication-detail-aside">' + paper_preview + pdf_block
        + '<div class="publication-detail-note"><p>Publication format</p><strong>'
        + escape_html(format_label) + '</strong></div></div>'
        '</div>'
    )


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../styles.css?v=final-actions-1">
  </head>
  <body class="{body_classes}">
    <header class="site-header">
      <a class="brand" href="../../index.html" aria-label="Network for Syrian Legislative Studies home">
        <span class="brand-mark">NSLS</span>
        <span>
          <strong>Network for Syrian</strong>
          <small>Legislative Studies</small>
        </span>
      </a>
      <nav class="primary-nav" aria-label="Primary navigation">
        <a href="../../index.html">Home</a>
        <a href="../../what-we-do.html">What We Do</a>
        <a href="../../publications.html" aria-current="page">Publications</a>
        <a href="../../our-team.html">Our Team</a>
        <a href="../../contact.html">Contact</a>
      </nav>
      <a class="language-toggle" href="../../ar/publications.html" lang="ar" dir="rtl">العربية</a>
      <a class="header-action" href="../../contact.html#request">Get in Touch</a>
    </header>

    <main id="top">
      <article class="publication-detail" data-publication-detail>
        {content}
      </article>
    </main>

    <footer class="site-footer">
      <div class="footer-primary">
        <a class="brand footer-brand" href="../../index.html">
          <span class="brand-mark">NSLS</span>
          <span>
            <strong>Network for Syrian</strong>
            <small>Legislative Studies</small>
          </span>
        </a>
        <p>Independent research and practical legislative support for Syria's Parliament.</p>
      </div>
      <nav class="footer-links" aria-label="Footer navigation">
        <div>
          <h2>Network</h2>
          <a href="../../index.html">About</a>
          <a href="../../what-we-do.html">What We Do</a>
          <a href="../../publications.html">Publications</a>
          <a href="../../our-team.html">Our Team</a>
        </div>
        <div class="footer-connect">
          <div class="footer-connect-links">
            <h2>Connect</h2>
            <a href="../../contact.html">Contact</a>
            <a href="https://www.linkedin.com/" target="_blank" rel="noopener">LinkedIn</a>
            <a href="../../privacy.html">Privacy</a>
          </div>
          <a class="footer-cta" href="../../contact.html#request">Get in Touch</a>
        </div>
      </nav>
      <div class="footer-bottom">
        <p>&copy; 2026 Network for Syrian Legislative Studies.</p>
        <p>Supporting independent legislative research in Syria.</p>
      </div>
    </footer>
  </body>
</html>
"""


def build_page(item, items):
    slug = item['slug']
    fmt = pub_format(item)
    title = (item.get('title') or '') + ' | Network for Syrian Legislative Studies'
    description = item.get('description') or 'Publication from the Network for Syrian Legislative Studies.'
    canonical = SITE_URL + '/publications/' + slug + '/'

    body_classes = 'isl-page publication-detail-page'
    if fmt == 'pdf':
        body_classes += ' pdf-publication-page'
    elif fmt == 'external':
        body_classes += ' external-publication-page'

    content = render_pdf_body(item, items) if fmt == 'pdf' else render_body(item, items)

    return PAGE_TEMPLATE.format(
        title=escape_html(title),
        description=escape_html(description),
        canonical=canonical,
        body_classes=body_classes,
        content=content,
    )


def read_items():
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    if isinstance(data, dict) and isinstance(data.get('publications'), list):
        return data['publications']
    return data


def main():
    items = read_items()
    slugged = [it for it in items if it.get('slug')]

    seen = set()
    for it in slugged:
        if it['slug'] in seen:
            raise SystemExit('Duplicate publication slug: ' + it['slug'])
        seen.add(it['slug'])

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for it in slugged:
        page_dir = OUTPUT_DIR / it['slug']
        page_dir.mkdir(parents=True, exist_ok=True)
        out_file = page_dir / 'index.html'
        out_file.write_text(build_page(it, items), encoding='utf-8')
        print('Wrote ' + str(out_file.relative_to(ROOT)))

    print('Generated ' + str(len(slugged)) + ' publication page(s).')


if __name__ == '__main__':
    main()

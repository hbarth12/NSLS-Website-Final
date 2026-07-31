#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerates the <header class="site-header"> and <footer class="site-footer">
blocks of every hand-authored page (English and Arabic) from a single
bilingual source, ISLS/content/site-chrome.json, instead of each page
carrying its own hand-copied, hand-translated chrome.

Everything else in each page -- <head>, the per-page <main> content, and
any trailing scripts after </footer> -- is left byte-for-byte untouched.
Only the header/footer blocks are replaced.

Per-page specifics that the shared chrome still needs (which nav item is
"current", whether this page IS contact.html so its own CTAs should be a
same-page "#general" fragment instead of "contact.html#general", whether
the footer's Network column includes an "Our Team" link, and the exact
language-toggle target) are read back out of each page's *existing*
header/footer before it gets replaced, so a first run is a no-behavior-
change formatting pass: identical hrefs and identical "current page"
state, just sourced from one JSON file instead of twenty-nine hand-edited
copies.

Run: python3 ISLS/scripts/generate-site-pages.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME = json.loads((ROOT / 'content' / 'site-chrome.json').read_text(encoding='utf-8'))

PAGES = [
    'index.html',
    'what-we-do.html',
    'publications.html',
    'publication.html',
    'our-team.html',
    'our-model.html',
    'contact.html',
    'privacy.html',
    'alice-mccarthy.html',
    'cameron-hume.html',
    'cooper-austen.html',
    'haddon-barth.html',
    'hannah-hoeselbarth.html',
    'max-weiss.html',
    'zaid-al-ali.html',
]

HEADER_RE = re.compile(r'[ \t]*<header class="site-header">.*?</header>\n', re.S)
FOOTER_RE = re.compile(r'[ \t]*<footer class="site-footer">.*?</footer>\n', re.S)
NAV_LINK_RE = re.compile(r'<a href="([^"]+)"( aria-current="page")?>')
LANG_TOGGLE_RE = re.compile(r'<a class="language-toggle" href="([^"]+)"')
HEADER_CTA_RE = re.compile(r'<a class="header-action" href="([^"]+)"')
FOOTER_CTA_RE = re.compile(r'<a class="footer-cta" href="([^"]+)"')
NETWORK_BLOCK_RE = re.compile(r'<nav class="footer-links".*?<div class="footer-connect">', re.S)


def extract_chrome_params(text, chrome_lang):
    header_match = HEADER_RE.search(text)
    footer_match = FOOTER_RE.search(text)
    if not header_match or not footer_match:
        raise ValueError('could not locate header/footer block')

    header_text = header_match.group(0)
    footer_text = footer_match.group(0)

    current_nav_key = None
    for href, current in NAV_LINK_RE.findall(header_text):
        if current:
            for item in chrome_lang['nav']:
                if item['href'] == href:
                    current_nav_key = item['key']

    lang_toggle_href = LANG_TOGGLE_RE.search(header_text).group(1)
    header_cta_href = HEADER_CTA_RE.search(header_text).group(1)
    footer_cta_href = FOOTER_CTA_RE.search(footer_text).group(1)

    network_block = NETWORK_BLOCK_RE.search(footer_text).group(0)
    footer_includes_our_team = 'href="our-team.html"' in network_block

    return {
        'current_nav_key': current_nav_key,
        'lang_toggle_href': lang_toggle_href,
        'header_cta_href': header_cta_href,
        'footer_cta_href': footer_cta_href,
        'footer_includes_our_team': footer_includes_our_team,
    }, header_match.span(), footer_match.span()


def render_header(chrome_lang, params):
    nav_lines = []
    for item in chrome_lang['nav']:
        current = ' aria-current="page"' if item['key'] == params['current_nav_key'] else ''
        nav_lines.append('        <a href="{href}"{current}>{label}</a>'.format(
            href=item['href'], current=current, label=item['label']))
    nav_html = '\n'.join(nav_lines)

    brand = chrome_lang['brand']
    return (
        '    <header class="site-header">\n'
        '      <a class="brand" href="{brand_href}" aria-label="{brand_aria}">\n'
        '        <span class="brand-mark">{brand_mark}</span>\n'
        '        <span>\n'
        '          <strong>{brand_l1}</strong>\n'
        '          <small>{brand_l2}</small>\n'
        '        </span>\n'
        '      </a>\n'
        '      <nav class="primary-nav" aria-label="Primary navigation">\n'
        '{nav_html}\n'
        '      </nav>\n'
        '      <a class="language-toggle" href="{toggle_href}" lang="{toggle_lang}" dir="{toggle_dir}">{toggle_label}</a>\n'
        '      <a class="header-action" href="{cta_href}">{cta_label}</a>\n'
        '    </header>\n'
    ).format(
        brand_href=brand['href'], brand_aria=brand['ariaLabel'], brand_mark=brand['mark'],
        brand_l1=brand['line1'], brand_l2=brand['line2'], nav_html=nav_html,
        toggle_href=params['lang_toggle_href'],
        toggle_lang=params['toggle_lang'], toggle_dir=params['toggle_dir'],
        toggle_label=params['toggle_label'],
        cta_href=params['header_cta_href'], cta_label=chrome_lang['headerCta'],
    )


def render_footer(chrome_lang, params):
    footer = chrome_lang['footer']
    brand = chrome_lang['brand']

    network_links = footer['networkLinks']
    if not params['footer_includes_our_team']:
        network_links = [item for item in network_links if item['key'] != 'our-team']
    network_lines = '\n'.join(
        '          <a href="{href}">{label}</a>'.format(href=item['href'], label=item['label'])
        for item in network_links
    )

    connect_lines = []
    for item in footer['connectLinks']:
        if item.get('external'):
            connect_lines.append('            <a href="{href}" target="_blank" rel="noopener">{label}</a>'.format(
                href=item['href'], label=item['label']))
        else:
            connect_lines.append('            <a href="{href}">{label}</a>'.format(
                href=item['href'], label=item['label']))
    connect_html = '\n'.join(connect_lines)

    return (
        '    <footer class="site-footer">\n'
        '      <div class="footer-primary">\n'
        '        <a class="brand footer-brand" href="{brand_href}">\n'
        '          <span class="brand-mark">{brand_mark}</span>\n'
        '          <span>\n'
        '            <strong>{brand_l1}</strong>\n'
        '            <small>{brand_l2}</small>\n'
        '          </span>\n'
        '        </a>\n'
        '        <p>{tagline}</p>\n'
        '      </div>\n'
        '      <nav class="footer-links" aria-label="Footer navigation">\n'
        '        <div>\n'
        '          <h2>{network_heading}</h2>\n'
        '{network_lines}\n'
        '        </div>\n'
        '        <div class="footer-connect">\n'
        '          <div class="footer-connect-links">\n'
        '            <h2>{connect_heading}</h2>\n'
        '{connect_html}\n'
        '          </div>\n'
        '          <a class="footer-cta" href="{footer_cta_href}">{footer_cta_label}</a>\n'
        '        </div>\n'
        '      </nav>\n'
        '      <div class="footer-bottom">\n'
        '        <p>{copyright}</p>\n'
        '        <p>{subtagline}</p>\n'
        '      </div>\n'
        '    </footer>\n'
    ).format(
        brand_href=brand['href'], brand_mark=brand['mark'], brand_l1=brand['line1'], brand_l2=brand['line2'],
        tagline=footer['tagline'], network_heading=footer['networkHeading'], network_lines=network_lines,
        connect_heading=footer['connectHeading'], connect_html=connect_html,
        footer_cta_href=params['footer_cta_href'], footer_cta_label=footer['footerCta'],
        copyright=footer['copyright'], subtagline=footer['subtagline'],
    )


def process_file(path, chrome_lang, toggle_lang, toggle_dir, toggle_label):
    text = path.read_text(encoding='utf-8')
    params, header_span, footer_span = extract_chrome_params(text, chrome_lang)
    params['toggle_lang'] = toggle_lang
    params['toggle_dir'] = toggle_dir
    params['toggle_label'] = toggle_label

    new_header = render_header(chrome_lang, params)
    new_footer = render_footer(chrome_lang, params)

    old_header_text = text[header_span[0]:header_span[1]]
    old_footer_text = text[footer_span[0]:footer_span[1]]

    new_text = text.replace(old_header_text, new_header, 1)
    new_text = new_text.replace(old_footer_text, new_footer, 1)
    path.write_text(new_text, encoding='utf-8')


def main():
    for filename in PAGES:
        en_path = ROOT / filename
        ar_path = ROOT / 'ar' / filename
        process_file(en_path, CHROME['en'], toggle_lang='ar', toggle_dir='rtl', toggle_label='العربية')
        process_file(ar_path, CHROME['ar'], toggle_lang='en', toggle_dir='ltr', toggle_label='English')
    print('Regenerated header/footer for {} page pairs.'.format(len(PAGES)))


if __name__ == '__main__':
    main()

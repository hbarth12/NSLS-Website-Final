#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerates ISLS/publications-data.js, the `file://`-preview fallback for
publications.js / home-publications.js (both languages). Since
content/publications-bilingual.json already holds both languages in one
file, there is only one fallback file now -- English pages load it
directly, Arabic pages load it via `../publications-data.js`.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read_publications(source):
    data = json.loads(source.read_text(encoding='utf-8'))
    return data.get('publications', data) if isinstance(data, dict) else data


def write_js(source, output, var_name):
    data = read_publications(source)
    js = 'window.' + var_name + ' = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';' + chr(10)
    output.write_text(js, encoding='utf-8')
    print('Wrote ' + str(output.relative_to(ROOT)))


write_js(ROOT / 'content' / 'publications-bilingual.json', ROOT / 'publications-data.js', 'NSLS_PUBLICATIONS_BILINGUAL')

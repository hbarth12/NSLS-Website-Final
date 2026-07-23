#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

write_js(ROOT / 'content' / 'publications.json', ROOT / 'publications-data.js', 'NSLS_PUBLICATIONS')
write_js(ROOT / 'content' / 'publications-ar.json', ROOT / 'ar' / 'publications-data.js', 'NSLS_PUBLICATIONS')

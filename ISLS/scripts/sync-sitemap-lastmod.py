#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keeps the <lastmod> of every static-page <url> entry in
ISLS/sitemap.xml synced to that page's actual last-modified date.

This only touches entries OUTSIDE the generated blocks -- <!-- BEGIN
GENERATED PUBLICATIONS --> / <!-- END GENERATED PUBLICATIONS -->
(owned by scripts/generate-publication-pages.py) and <!-- BEGIN
GENERATED PARLIAMENTARY RECORD --> / <!-- END GENERATED PARLIAMENTARY
RECORD --> (owned by scripts/generate-parliamentary-record.py). Those
generators date their entries from each item's own `date` field, not
file mtime, so this script leaves them alone.

For each remaining entry's file, "last-modified" means:
  - if the file has no uncommitted changes (matches HEAD), the date of
    the last git commit that touched it -- this is what survives a
    fresh clone or a `git checkout`, both of which reset filesystem
    mtimes to "now" without the content actually changing. (A local
    `git checkout <file>` mid-session, e.g. to revert a bad generator
    run, produced exactly that false "changed today" signal the first
    time this ran -- see TEMPLATES_README.md.)
  - otherwise (the file has a real uncommitted edit right now), the
    filesystem mtime, since there's no commit yet to date it by.

Falls back to filesystem mtime outright if this isn't a git checkout,
or git isn't available.

Run: python3 ISLS/scripts/sync-sitemap-lastmod.py

Also runs automatically as a pre-commit hook (see scripts/hooks/pre-commit)
so sitemap.xml can't go stale again, no matter whether a page was
edited by hand or through generate-site-pages.py. See
TEMPLATES_README.md for how the hook gets installed.
"""
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / 'sitemap.xml'
SITE_URL = 'https://www.nsls.network'
GENERATED_BLOCKS = [
    ('<!-- BEGIN GENERATED PUBLICATIONS -->', '<!-- END GENERATED PUBLICATIONS -->'),
    ('<!-- BEGIN GENERATED PARLIAMENTARY RECORD -->', '<!-- END GENERATED PARLIAMENTARY RECORD -->'),
]


def git_repo_root():
    # Git exports GIT_DIR to hooks run from a linked worktree (`git worktree
    # add`). With GIT_DIR set, `rev-parse --show-toplevel` reports the
    # current directory (ISLS/) instead of the real top level, every git
    # lookup below then misses, and every page falls back to its mtime --
    # stamping unchanged pages with today's date. Look the top level up
    # without the inherited GIT_DIR / GIT_WORK_TREE.
    env = {k: v for k, v in os.environ.items() if k not in ('GIT_DIR', 'GIT_WORK_TREE')}
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=ROOT, env=env, capture_output=True, text=True, check=True)
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


REPO_ROOT = git_repo_root()


def file_date(path):
    if REPO_ROOT is not None:
        rel = path.relative_to(REPO_ROOT)
        unchanged = subprocess.run(
            ['git', 'diff', '--quiet', 'HEAD', '--', str(rel)],
            cwd=REPO_ROOT).returncode == 0
        if unchanged:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cs', '--', str(rel)],
                cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            commit_date = result.stdout.strip()
            if commit_date:
                return commit_date
    return date.fromtimestamp(path.stat().st_mtime).isoformat()

URL_ENTRY_RE = re.compile(
    r'(?P<prefix><loc>(?P<loc>[^<]+)</loc>\s*<lastmod>)'
    r'(?P<lastmod>[^<]*)'
    r'(?P<suffix></lastmod>)'
)


def loc_to_path(loc):
    if not loc.startswith(SITE_URL):
        return None
    rel = loc[len(SITE_URL):].lstrip('/')
    if rel == '' or rel.endswith('/'):
        rel += 'index.html'
    return ROOT / rel


def sync():
    if not SITEMAP.is_file():
        print(f'ERROR: {SITEMAP} not found', file=sys.stderr)
        return False

    text = SITEMAP.read_text(encoding='utf-8')

    # Split the sitemap into alternating unmanaged / generated segments, so
    # only the unmanaged ones are rewritten below.
    spans = []
    for begin_marker, end_marker in GENERATED_BLOCKS:
        if begin_marker not in text or end_marker not in text:
            print(f'ERROR: sitemap.xml is missing the {begin_marker} / '
                  f'{end_marker} markers.', file=sys.stderr)
            return False
        spans.append((text.index(begin_marker), text.index(end_marker) + len(end_marker)))
    spans.sort()

    changes = []
    warnings = []

    def replace(match):
        loc = match.group('loc').strip()
        old = match.group('lastmod').strip()
        path = loc_to_path(loc)
        if path is None or not path.is_file():
            warnings.append(loc)
            return match.group(0)
        new = file_date(path)
        if new != old:
            changes.append((loc, old, new))
        return match.group('prefix') + new + match.group('suffix')

    pieces = []
    pos = 0
    for begin, end in spans:
        pieces.append(URL_ENTRY_RE.sub(replace, text[pos:begin]))
        pieces.append(text[begin:end])
        pos = end
    pieces.append(URL_ENTRY_RE.sub(replace, text[pos:]))

    for loc in warnings:
        print(f'  WARNING: no local file found for {loc} -- left lastmod as-is', file=sys.stderr)

    if changes:
        SITEMAP.write_text(''.join(pieces), encoding='utf-8')
        print(f'Updated {len(changes)} lastmod date(s):')
        for loc, old, new in changes:
            print(f'  {loc}: {old} -> {new}')
    else:
        print('sitemap.xml lastmod dates already match file mtimes -- no changes.')

    return True


if __name__ == '__main__':
    if not sync():
        sys.exit(1)

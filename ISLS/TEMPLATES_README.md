# Site-Wide Templates (Chrome, Team, Publications Scripts)

Most of the site's English/Arabic duplication has been replaced by shared bilingual data files plus a generator, the same pattern `PUBLICATIONS_README.md` describes for publications. This covers the other three pieces: site chrome, team bios, and the publications JavaScript.

## Site Chrome (header/footer)

Source of truth: `content/site-chrome.json` -- one `en` block and one `ar` block, each holding the brand text, the 5-item primary nav (`key`/`href`/`label`), the header "Get in Touch" CTA text, and the footer (tagline, Network column links, Connect column links, footer CTA, copyright, subtagline).

To change nav wording, footer links, the header/footer CTA text, or the copyright line, edit `content/site-chrome.json` and run:

```bash
python3 scripts/generate-site-pages.py
```

This replaces only the `<header class="site-header">` and `<footer class="site-footer">` block on every page (English and Arabic) -- it does not touch `<head>`, page-specific `<main>` content, or trailing scripts. Per-page specifics the chrome still needs (which nav item is "current," `contact.html`'s own CTAs using a same-page `#general` fragment instead of `contact.html#general`, whether a page's footer Network column includes "Our Team," and each page's language-toggle target) are read back out of that page's *existing* header/footer before it's replaced, so the generator adapts to each page rather than assuming they're all identical.

The generator rewrites the header/footer of pages that already exist -- it reads each page's *current* header/footer to work out page-specific details first, so it can't create a page from nothing. Adding a new top-level page (not a publication or team member) means creating `<file>.html` and `ar/<file>.html` by hand first (copying an existing page's header/footer structure is the easiest starting point), adding its filename to the `PAGES` list near the top of `scripts/generate-site-pages.py`, then running the generator.

## Team Bios

Source of truth: `content/team-bilingual.json` -- one entry per person, in the order they should appear. Shared fields: `slug` (used for the filename and cross-references), `section` (`"staff"` or `"advisory"` -- controls which list on `our-team.html` they render into and what fields they need), and `initials` (shown on their individual page; use `null` for someone who shouldn't get a photo/initials mark, like Haddon Barth today).

Staff members (`section: "staff"`) need, per language:
- `name`
- `rosterRole` -- the title shown on their `our-team.html` card
- `profileRole` -- the eyebrow shown on their own page (usually the same as `rosterRole`, but doesn't have to be -- see Cooper Austen and Hannah Höselbarth for real examples where these differ today)
- `bio` -- an array of paragraph strings for their individual page. Inline HTML like `<a href="mailto:...">` is fine; each string becomes one `<p>`.

Advisory board members (`section: "advisory"`) need, per language:
- `name`, `role`
- `rosterShortBio` -- the always-visible sentence on their `our-team.html` card
- `rosterLongBio` -- the sentence revealed by the "Read full bio" toggle
- `individualBio` -- paragraph array for their own page (today these are short placeholder bios, not full profiles -- expand them here if that changes)

### Editing an existing team member

Edit their entry in `content/team-bilingual.json` (both languages) and run:

```bash
python3 scripts/generate-site-pages.py
```

This regenerates `<slug>.html` and `ar/<slug>.html` in full, and regenerates the `.staff-list`/`.advisory-list` block on `our-team.html` and `ar/our-team.html` to match. Reordering someone, or moving them between staff and advisory, is just moving/editing their entry in the JSON and re-running the generator.

### Adding a brand new team member

The generator rewrites existing pages -- it doesn't create a page from nothing, because it reads each page's *current* header/footer to figure out page-specific details (see Site Chrome above) before replacing them. For a new person:

1. Copy an existing individual bio page of the same kind (a staff page like `cooper-austen.html`, or an advisory page like `max-weiss.html`) to `<new-slug>.html`, and do the same for the Arabic counterpart in `ar/`. The copied `<main>` content will be thrown away by the generator, so it doesn't matter what it says -- only the `<head>` (title, canonical, meta description) and the `<html lang>`/`dir` attributes need to be correct for the new person, since those aren't regenerated.
2. Add `<new-slug>.html` to the `PAGES` list in `scripts/generate-site-pages.py`.
3. Add their entry to `content/team-bilingual.json` (both languages).
4. Run `python3 scripts/generate-site-pages.py`.

What's *not* covered by this file, and stays hand-authored on `our-team.html`: the page's own headings, the "University Network" prose (Princeton Summer Research Cohort / University Chapters), and the "Research Network" section -- those aren't per-person data.

## Publications Scripts

`publications.js` (used by `publications.html`), `home-publications.js` (used by `index.html`), and `publication-detail.js` (used by `publication.html`) are each a single file shared by both languages -- there's no `ar/` copy to keep in sync anymore. Each script reads `document.documentElement.lang` at runtime and picks a small config object (month names, date-order formatting, which of `item.en`/`item.ar` to read, the Arabic asset-path prefixer, the `content/publications-bilingual.json` fetch path, and the translated UI strings) based on it. If you need to change wording in these scripts (the "no publications in this category" message, "read the latest work..." links, etc.), edit the relevant language's block directly in the script -- there's nothing to regenerate here, and no second file to remember to update.

## Keeping sitemap.xml's lastmod Dates Accurate

`sitemap.xml` has two independently-maintained regions:

- The block between `<!-- BEGIN GENERATED PUBLICATIONS -->` and `<!-- END GENERATED PUBLICATIONS -->` is rewritten by `scripts/generate-publication-pages.py` on every run, dated from each publication's own `date` field.
- Everything else -- every top-level page and every `ar/` page, including all the individual bio pages -- is synced by `scripts/sync-sitemap-lastmod.py`, which sets each entry's `<lastmod>` to that page's actual file-modification date on disk.

You shouldn't need to run `sync-sitemap-lastmod.py` by hand: it also runs as a **pre-commit hook**, so any commit that touches a page automatically re-syncs and stages `sitemap.xml` alongside it, whether the page was hand-edited or produced by a generator. Since `.git/hooks/` isn't tracked by git, each clone needs to install it once:

```bash
sh ISLS/scripts/hooks/install.sh
```

If `sitemap.xml` ever looks stale (e.g. you skipped the hook, or edited a file's mtime some other way), just run:

```bash
python3 scripts/sync-sitemap-lastmod.py
```

## Workflow Summary

After editing `content/site-chrome.json` and/or `content/team-bilingual.json`:

```bash
python3 scripts/generate-site-pages.py
```

Then upload whichever files it changed. If you're not sure what changed, `git status` / `git diff` after running it will show exactly which pages were touched -- a chrome-only edit typically only changes `<header>`/`<footer>` blocks; a team edit only changes the affected person's page plus `our-team.html`.

## What's Still Hand-Authored

The `<main>` content of `index.html`, `what-we-do.html`, `our-model.html`, `contact.html`, and `privacy.html` (in both languages) is bespoke page layout and copy, not modeled as data -- edit those directly. Their `<head>` (title, canonical, meta description) and the shared chrome around them are still handled as described above.

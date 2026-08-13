# Adding Publications

The source of truth is `content/publications-bilingual.json` -- one entry per publication, holding both languages' translatable fields (`en` / `ar`) plus shared fields (like `slug`, `type`, `date`, `featured`) once. The homepage and Publications page (both languages) read from this file on Vercel. For local `file://` previews, the site also uses a generated fallback file: `publications-data.js` (shared by both languages; Arabic pages load it via `../publications-data.js`).

Each publication also gets a real static page generated at build time, in both languages: `publications/<slug>/index.html` and `ar/publications/<slug>/index.html`.

## Future PDF Workflow with Codex

When you give Codex a PDF, ask:

> Add this PDF as the newest publication. Type: Policy Paper. Title (EN/AR): ... Author (EN/AR): ... Date: ... Summary (EN/AR): ... Topics (EN/AR): ...

Codex should then do these things:

1. Copy the PDF(s) into `assets/uploads/` using a clean lowercase filename (English and Arabic PDFs can be different files -- see "Two PDFs" below).
2. Add a new entry at the top of `content/publications-bilingual.json`, following the shape in `templates/pdf-publication-entry.json`.
3. Set `featured: true` on the new entry and set older entries to `featured: false` if this should be the large homepage publication.
4. Run `python3 scripts/sync-publications.py` so the local preview fallback file matches the JSON.
5. Run `python3 scripts/generate-publication-pages.py` to regenerate both languages' static pages and the sitemap.

After that, upload these changed files to GitHub:

- `content/publications-bilingual.json`
- `publications-data.js`
- `publications/<slug>/index.html` and `ar/publications/<slug>/index.html` (new and any regenerated ones)
- `sitemap.xml`
- the new file(s) inside `assets/uploads/`

Usually no other HTML or CSS change is needed.

## Publication Types

Use `type` to control filters and ordering (shared, not per-language):

- `policy-paper`
- `memo`
- `commentary`
- `institutional-note`

Use `label` (inside `en` and `ar`) for what appears visually on the card, for example `Policy Paper` / `ورقة سياسات`.

## Publication Formats

Use `publicationFormat` (shared) to control how the detail page behaves:

- `pdf` - creates a publication page with a PDF preview card and download button.
- `external` - creates a local commentary page with intro text, then a `Read more at [source]` button.
- `page` - creates a full article page on the NSLS website.

## Two PDFs (English + Arabic)

Set `pdf` inside `en` and inside `ar` independently. The Download PDF button always links to the PDF matching the page's own language -- the English page links `en.pdf`, the Arabic page links `ar.pdf` -- with no picker. If the page's own language doesn't have a PDF, the button falls back to whichever language does; if neither language has a PDF, the download button doesn't render.

## PDF Entry Template

A reusable JSON template is available at:

`templates/pdf-publication-entry.json`

Important fields for PDFs:

- `slug` - the URL identifier for both `publications/<slug>/` and `ar/publications/<slug>/`.
- `en.pdf` / `ar.pdf` - path to the uploaded PDF for each language, usually `assets/uploads/name.pdf`.
- `en.body` / `ar.body` - short intro text shown before the download area.
- `featured` - set to `true` if it should become the large homepage publication.

## External Commentary Template

For commentaries published elsewhere, use:

```json
{
  "slug": "short-url-slug",
  "type": "commentary",
  "publicationFormat": "external",
  "source": "Al-Monitor",
  "date": "2026-05-21",
  "url": "https://external-site.com/article",
  "external": true,
  "featured": false,
  "en": {
    "label": "Commentary",
    "title": "Title",
    "description": "Short summary.",
    "topics": ["Topic"],
    "imageAlt": "Image description",
    "body": "First intro paragraph.\n\nSecond intro paragraph."
  },
  "ar": {
    "label": "تعليق",
    "title": "العنوان",
    "description": "ملخص قصير.",
    "topics": ["الموضوع"],
    "imageAlt": "وصف الصورة",
    "body": "الفقرة التمهيدية الأولى.\n\nالفقرة الثانية."
  }
}
```

Add `"image"` at the top level (shared by both languages) if there's a cover image. The generated detail page shows the `body` text and then a "Read more at [source]" button.

## Date format

`date` is shared (not per-language) and stored as ISO: `YYYY-MM-DD`, or `YYYY-MM` if only the month is known. Each language's page formats it for display itself (e.g. `May 21, 2026` / `21 أيار 2026`).

## Sync Commands

After editing `content/publications-bilingual.json`, run:

```bash
python3 scripts/sync-publications.py
python3 scripts/generate-publication-pages.py
```

Then validate:

```bash
python3 -m json.tool content/publications-bilingual.json > /tmp/nsls-publications-check.json
```

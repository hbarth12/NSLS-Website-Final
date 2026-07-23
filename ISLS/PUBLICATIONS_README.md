# Adding Publications

The source of truth is `content/publications.json`. The homepage and Publications page both read from this file on Vercel. For local `file://` previews, the site also uses generated fallback files: `publications-data.js` and `ar/publications-data.js`.

## Future PDF Workflow with Codex

When you give Codex a PDF, ask:

> Add this PDF as the newest publication. Type: Policy Paper. Title: ... Author: ... Date: ... Summary: ... Topics: ...

Codex should then do four things:

1. Copy the PDF into `assets/uploads/` using a clean lowercase filename.
2. Add a new entry at the top of `content/publications.json`.
3. Set `featured: true` on the new entry and set older entries to `featured: false` if this should be the large homepage publication.
4. Run `python3 scripts/sync-publications.py` so local preview fallback files match the JSON.

After that, upload these changed files to GitHub:

- `content/publications.json`
- `publications-data.js`
- `ar/publications-data.js`
- the new file inside `assets/uploads/`

Usually no HTML or CSS change is needed.

## Publication Types

Use `type` to control filters and ordering:

- `policy-paper`
- `memo`
- `commentary`
- `institutional-note`

Use `label` for what appears visually on the card, for example `Policy Paper`, `Memo`, or `Commentary`.

## Publication Formats

Use `publicationFormat` to control how the detail page behaves:

- `pdf` - creates a publication page with a PDF preview card and download button.
- `external` - creates a local commentary page with intro text, then a `Read more at [source]` button.
- `page` - creates a full article page on the NSLS website.

## PDF Entry Template

A reusable JSON template is available at:

`templates/pdf-publication-entry.json`

Important fields for PDFs:

- `slug` - the URL identifier used by `publication.html?slug=...`
- `pdf` - path to the uploaded PDF, usually `assets/uploads/name.pdf`
- `body` - short intro text shown before the download area
- `featured` - set to `true` if it should become the large homepage publication

## External Commentary Template

For commentaries published elsewhere, use:

```json
{
  "slug": "short-url-slug",
  "type": "commentary",
  "label": "Commentary",
  "publicationFormat": "external",
  "title": "Title",
  "description": "Short summary.",
  "source": "Al-Monitor",
  "date": "Month Day, Year",
  "topics": ["Topic"],
  "image": "https://...",
  "imageAlt": "Image description",
  "url": "https://external-site.com/article",
  "external": true,
  "featured": false,
  "body": "First intro paragraph.\n\nSecond intro paragraph."
}
```

The local detail page will show the `body` text and then a button reading `Read more at [source]`.

## Sync Command

After editing `content/publications.json`, run:

```bash
python3 scripts/sync-publications.py
```

Then validate:

```bash
python3 -m json.tool content/publications.json > /tmp/nsls-publications-check.json
```

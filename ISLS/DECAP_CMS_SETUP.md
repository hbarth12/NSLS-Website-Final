# Decap CMS Setup

The Publications page reads from `content/publications.json`. Decap CMS edits that file through `/admin/`.

## Files

- `admin/index.html` - loads Decap CMS.
- `admin/config.yml` - defines the Publications editor.
- `content/publications.json` - publication entries edited by Decap.
- `publication.html` - reusable on-site publication detail page.
- `publication-detail.js` - renders on-site articles and PDF download pages.
- `assets/uploads/` - uploaded publication images and PDFs.

## Before deploying

Open `admin/config.yml` and replace:

```yml
repo: YOUR-GITHUB-USERNAME/YOUR-REPO-NAME
```

with your actual GitHub repo, for example:

```yml
repo: haddonbarth/nsls
```

## Publication formats

Go to `/admin/` on the deployed site. Add or reorder publications in the Publications list.

Choose one publication format:

- `External link` - for pieces hosted at another publication. Add the external URL.
- `Website article` - for text that should live directly on the NSLS site. Add a slug and write the body in Markdown.
- `PDF download` - for reports or papers where the page shows a summary and a PDF download button. Add a slug and upload the PDF.

The category buttons on `publications.html` filter by `type`:

- `analysis`
- `policy-paper`
- `institutional-note`

The first visible featured entry becomes the large card on the Publications page.

## Authentication note

The GitHub backend also needs an OAuth flow/provider for Decap CMS to commit changes back to the repo. On Vercel, this is usually handled with a small OAuth provider service or a Decap-compatible auth integration. Once that is configured, `/admin/` can commit changes directly to GitHub.

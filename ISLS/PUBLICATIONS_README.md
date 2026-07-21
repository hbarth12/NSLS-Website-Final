# Adding Publications

The Publications page reads from `content/publications.json`. The easiest way to add an item is through Decap CMS at `/admin/` once GitHub authentication is configured.

Each publication can be one of three formats:

- `external` - links to an article hosted somewhere else, such as Al-Monitor or MEI.
- `page` - creates a publication page on this website at `publication.html?slug=your-slug`.
- `pdf` - creates a summary page with a download button for an uploaded PDF.

Use `type` to control the Publications page filters:

- `analysis`
- `policy-paper`
- `institutional-note`

## Required fields

- `title` - publication title.
- `description` - short summary shown on cards and detail pages.
- `source` - publisher or source, usually `NSLS` for internal work.
- `date` - display date, for example `May 21, 2026`.
- `type` and `label` - category/filter.
- `slug` - needed for on-site articles and PDFs.

## External article

Set `publicationFormat` to `external`, add the external `url`, and set `external` to `true` for compatibility.

## Website article

Set `publicationFormat` to `page`, add a `slug`, and write the article in `body`. The body field supports simple Markdown headings and links, including `[link text](https://example.com)`.

## PDF report

Set `publicationFormat` to `pdf`, add a `slug`, upload the PDF in `pdf`, and use `description` for the summary. You can also add body text if you want a longer introduction before the download button.

For images you upload yourself, Decap saves them in `assets/uploads/` and writes the path into `content/publications.json`.

# Parliamentary Record

Transcripts of public parliament sessions, in English and Arabic. Built the same way as publications (see `PUBLICATIONS_README.md`), with its own content file, generator and listing.

- Source of truth: `content/parliamentary-record-bilingual.json`, edited in Pages CMS under **Parliamentary Record**.
- Generator: `scripts/generate-parliamentary-record.py` writes:
  - `parliamentary-record/<slug>/index.html` and `ar/parliamentary-record/<slug>/index.html`
  - `parliamentary-record-data.js`, the listing pages' only data source (no transcript text)
  - the `<!-- BEGIN/END GENERATED PARLIAMENTARY RECORD -->` block of `sitemap.xml`
- Listing pages: `parliamentary-record.html` and `ar/parliamentary-record.html`, rendered by `parliamentary-record.js` (one file for both languages).
- CI: `.github/workflows/sync-parliamentary-record.yml` runs the generator after a CMS edit lands on `main` and opens a `sync-parliamentary-record` PR.

## Before launch: delete the placeholders

The section ships with two sample entries, both with `placeholder: true` and titles starting **PLACEHOLDER – delete me**:

- `placeholder-sample-session`, a bilingual sample showing every feature
- `placeholder-english-only-session`, which shows how a one-language session looks

Placeholders are `noindex`, left out of the sitemap, and show a banner on the page. Delete both entries in Pages CMS. The sync PR then removes their pages.

## When a session appears on the site

A language is published once it has a **Title** and a **Transcript**. Until then:

- no page is generated for that language, and there is no sitemap entry or hreflang link for it;
- the listing in that language still shows the session, as a card in the language that exists, marked "English only" / "بالعربية فقط" and linking to that page;
- the existing page's language switch goes to the other language's listing.

Every published language must have an **Accuracy / Translation Note**. If one is missing, the generator stops with an error naming the session, and nothing is regenerated. A Pages CMS edit then shows up as a failed "Sync Parliamentary Record" run in GitHub Actions.

New sessions appear on the listing only when the sync PR is merged. The listing reads only `parliamentary-record-data.js`, which is generated in the same run as the pages, so it can't link to a page that doesn't exist yet. This is the same safeguard publications use (see commit `c8481c3`).

## Transcript format

One speaker turn per paragraph, with a blank line between turns:

```
[00:00:45] Member A (Damascus): Thank you, Mr. Speaker. The draft allocates 31% ...

[00:03:05] [Studio] Studio presenter: For viewers just joining ...

(The draft law is referred to the Budget Committee by majority vote.)
```

- `[00:00:45]` is an optional timestamp, shown small and muted. `[0:45]` and `[01:02:03]` also work.
- `[Studio]` (or `[استوديو]`) marks broadcaster commentary rather than the hearing. Consecutive studio turns are grouped into one shaded block labelled "Studio commentary" / "تعليق الاستوديو".
- `Name:` becomes the bold speaker name. The name can be up to 60 characters and 8 words.
- A paragraph in parentheses is a procedural note, shown in italics.
- Any other paragraph is shown as plain text, so start every turn with the speaker's name.
- Inline Markdown works as in publications: `**bold**`, `*italic*`, `[link](https://...)`.

Each paragraph's text direction comes from its own text (ignoring the speaker name), so an English quote in an Arabic transcript reads left to right and vice versa. Names, numbers and dates are kept in order with `<bdi>`.

## Long transcripts

The transcript is part of the page's HTML, so search engines can index it and Ctrl+F finds anything in it, without JavaScript. Turns are grouped into blocks of 40 with `content-visibility: auto`, so the browser only lays out the part on screen. PDFs are linked, not embedded.

## Running locally

```bash
python3 scripts/generate-parliamentary-record.py
```

Changing the nav or footer means editing `content/site-chrome.json`, then running `generate-site-pages.py`, `generate-publication-pages.py` (whose page template has its own copy of the nav) and this generator.

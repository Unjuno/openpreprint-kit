#!/usr/bin/env python3
"""Build a static reader view. No JavaScript, scientific approval or deployment.

The research record is an unsigned operational snapshot separate from the original
RFC 3161 bundle. Original paper bytes remain unchanged, including after retraction.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import shutil
import sys

from preflight import validate_repository
from research_record import read_json, validate_record, status_for, evidence_path, version_ok
from verify_release import verify, unique_object


def build_site(bundle: Path, root: Path, output: Path, repository: str) -> None:
    validate_repository(repository)
    errors = verify(bundle, None)
    if errors:
        raise ValueError('; '.join(errors))
    metadata = json.loads((bundle / 'preprint-metadata.json').read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    for key in ('title', 'abstract', 'license'):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f'invalid metadata field: {key}')
    version, digest = metadata.get('version'), metadata['paper_sha256']
    if not version_ok(version):
        raise ValueError('invalid version for reader view')
    authors = metadata.get('authors')
    if not isinstance(authors, list) or not authors:
        raise ValueError('author list is required')
    names = []
    for author in authors:
        if not isinstance(author, dict):
            raise ValueError('invalid author')
        if 'name' in author:
            name = author['name']
        else:
            parts = [author.get('given_names'), author.get('family_names')]
            if not all(isinstance(x, str) and x.strip() for x in parts):
                raise ValueError('invalid author name')
            name = ' '.join(parts)
        if not isinstance(name, str) or not name.strip():
            raise ValueError('invalid author name')
        names.append(name)
    record = read_json(root / 'reviews/record.json')
    errors = validate_record(record, root)
    if errors:
        raise ValueError('; '.join(errors))
    # A record cannot transfer a same-tag review to altered paper bytes.
    if any(e['version'] == version and e['paper_sha256'] != digest for e in record['events']):
        raise ValueError('research record binds this version to a different PDF')
    state = status_for(record, version, digest)
    events = [e for e in record['events'] if e['version'] == version and e['paper_sha256'] == digest]
    if output.is_symlink():
        raise ValueError('output cannot be a symlink')
    out = output.resolve()
    if out.is_relative_to(bundle.resolve()) or root.resolve().is_relative_to(out):
        raise ValueError('output cannot contain the source repository or be inside the bundle')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('output must be a new or empty directory')

    release = f'https://github.com/{repository}/releases/tag/{version}'
    rows = ''.join(f'<li><a href="assets/{escape(p.name, quote=True)}" download>{escape(p.name)}</a></li>'
                   for p in sorted(bundle.iterdir()))
    notices = []
    for event in events:
        reports = []
        for evidence in event['evidence']:
            path = evidence_path(root, evidence['path'])
            reports.append('<details><summary>Evidence (plain text)</summary><pre>' +
                           escape(path.read_text(encoding='utf-8')) + '</pre></details>')
        replacement = event.get('replacement')
        replacement_html = ''
        if replacement:
            url = f'https://github.com/{repository}/releases/tag/{replacement["version"]}'
            replacement_html = f'<p>Replacement record: <a href="{escape(url, quote=True)}">{escape(replacement["version"])}</a> — PDF SHA-256 <code>{replacement["paper_sha256"]}</code>. Publication of that link is not verified here.</p>'
        notices.append(f'<article><h3>{escape(event["kind"])}</h3><p>{escape(event["summary"])}</p>'
                       f'<p>Claimed actor: {escape(event["actor"])} · Claimed UTC: {escape(event["recorded_at"])}</p>'
                       f'<p>Declared conflicts: {escape(event["conflicts"])}</p>{replacement_html}{"".join(reports)}</article>')
    title = escape(metadata['title'])
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{title} — {escape(version)}</title>
<meta name="citation_title" content="{escape(metadata['title'], quote=True)}">
<meta name="citation_pdf_url" content="https://github.com/{repository}/releases/download/{version}/paper.pdf">
<style>body{{font:17px/1.65 system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#172331}}h1{{line-height:1.25}}.notice{{border:3px solid #8a3d17;padding:18px;margin:24px 0}}pre,code{{overflow-wrap:anywhere;white-space:pre-wrap}}article{{border-top:1px solid #bac4cc;padding:18px 0}}a{{color:#165683}}footer{{border-top:1px solid #bac4cc;margin-top:30px;padding-top:15px}}</style></head>
<body><header><p>OPENPREPRINT KIT · {escape(version)}</p><h1>{title}</h1><p>{escape('; '.join(names))}</p></header>
<section class="notice" aria-label="Publication status"><h2>{state}</h2>
<p>This is a preprint, not an independently certified peer-reviewed publication. Review records are human assertions, not proof of scientific correctness or reviewer identity.</p></section>
<main><h2>Abstract</h2><p>{escape(metadata['abstract'])}</p>
<p>Paper license: {escape(metadata['license'])}. This is separate from the toolkit software license.</p>
<p><a href="assets/paper.pdf" download>Download this version's PDF</a> · <a href="{release}">Version-specific GitHub Release</a></p>
<h2>Integrity and time evidence</h2><p>PDF SHA-256: <code>{digest}</code></p>
<p>Bundled checksums matched when this page was built; authenticity requires a separately trusted source.</p>
<p>Timestamp status: <strong>NOT_VERIFIED</strong> by this page. Downloaded timestamp files, if listed, must be verified with an independently selected CA/CRL policy. General public availability time and authorship are not proven.</p>
<ul>{rows}</ul><h2>Review and post-publication notices</h2>
{''.join(notices) if notices else '<p>No records for these exact paper bytes.</p>'}
<p><a href="research-record.json">Unsigned operational record snapshot</a>. This snapshot is not covered by the original paper timestamp. Consult the repository for later notices; a downloaded page can become stale.</p>
<h2>BibTeX</h2><pre>{escape((bundle/'citation.bib').read_text(encoding='utf-8'))}</pre></main>
<footer>Original paper assets are retained after corrections or retractions. Public report text must not contain confidential reviewer or participant information.</footer></body></html>
'''
    out.mkdir(parents=True, exist_ok=True)
    (out / 'assets').mkdir()
    for file in bundle.iterdir():
        shutil.copyfile(file, out / 'assets' / file.name)
    (out / 'research-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Preserve the relative paths referenced in the downloaded record.
    for event in record['events']:
        for evidence in event['evidence']:
            dest = out / evidence['path'];dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(evidence_path(root, evidence['path']), dest)
    (out / 'index.html').write_text(html, encoding='utf-8')
    (out / '.nojekyll').touch()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, default=Path('site'))
    parser.add_argument('--repository', required=True)
    args = parser.parse_args()
    try:
        build_site(args.bundle, args.root, args.output, args.repository)
        print('PASS: static reader view generated; no deployment or peer-review certification performed')
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())

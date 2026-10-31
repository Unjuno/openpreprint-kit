# Contributing

Use a feature branch and a pull request. Before changing behavior, add a failing
regression test, implement the smallest correction, then run the complete suite:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/research_record.py
```

Record runtime versions and actual outcomes. Do not report skipped/queued tests as passes.
Use full commit SHAs for Actions. Never run untrusted fork code with write tokens or
`pull_request_target` secrets. No TSA private keys, personal tokens or sensitive research data.

Scientific review records require human consent and conflict disclosures; see
[review policy](docs/REVIEW_POLICY.md). Append corrections rather than editing old events.
Breaking evidence formats require versioned schemas and compatibility tests.
A tool release and a paper release are distinct; do not publish the template as a real paper.

"""End-to-end synthetic collaborative peer-review round; not a real review."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROUND = 'https://github.com/example/paper/issues/17'
PAPER_SHA = 'a' * 64


class PeerReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        evidence = self.root / 'reviews/evidence'
        evidence.mkdir(parents=True)
        self.report = evidence / 'synthetic-report.md'
        self.report.write_text('Synthetic fixture only; not an actual peer review.\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def event(self, event_id, kind, actor, *, decision=None):
        event = {
            'id': event_id,
            'kind': kind,
            'version': 'v1',
            'paper_sha256': PAPER_SHA,
            'round_issue': ROUND,
            'recorded_at': '2026-11-15T00:00:00Z',
            'actor': actor,
            'conflicts': 'Synthetic fixture; no real review or conflict assessment.',
            'summary': 'Synthetic workflow test event.',
            'evidence': [{
                'path': 'reviews/evidence/synthetic-report.md',
                'sha256': hashlib.sha256(self.report.read_bytes()).hexdigest(),
            }],
        }
        if decision:
            event['decision'] = decision
        return event

    def run_cli(self, events):
        record = self.root / 'reviews/record.json'
        record.write_text(json.dumps({'schema_version': 1, 'events': events}), encoding='utf-8')
        return subprocess.run(
            [sys.executable, str(ROOT / 'scripts/research_record.py'),
             '--root', str(self.root), '--round-issue', ROUND,
             '--version', 'v1', '--paper-sha256', PAPER_SHA],
            capture_output=True, text=True, check=False,
        )

    def test_issue_to_two_reviews_response_and_editor_decision_passes(self):
        events = [
            self.event('review-one', 'review', 'reviewer-one'),
            self.event('review-two', 'review', 'reviewer-two'),
            self.event('author-response', 'response', 'author'),
            self.event('editor-decision', 'editorial_decision', 'editor', decision='revise'),
        ]
        result = self.run_cli(events)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['round']['reviewers'], 2)
        self.assertEqual(report['round']['responses'], 1)
        self.assertEqual(report['round']['decision'], 'revise')
        self.assertEqual(report['peer_review_certification'], 'NOT_PROVIDED')

    def test_round_without_two_distinct_reviewers_is_rejected(self):
        events = [
            self.event('review-one', 'review', 'same-reviewer'),
            self.event('review-two', 'review', 'same-reviewer'),
            self.event('author-response', 'response', 'author'),
            self.event('editor-decision', 'editorial_decision', 'editor', decision='accept'),
        ]
        result = self.run_cli(events)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('two distinct reviewers', result.stderr)


if __name__ == '__main__':
    unittest.main()

"""GitHub forms and pull-request templates describe the same public workflow."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class PeerReviewTemplateTests(unittest.TestCase):
    def test_issue_forms_are_valid_and_pin_version_before_review(self):
        issue_dir = ROOT / '.github/ISSUE_TEMPLATE'
        for name in ('peer-review-round.yml', 'reviewer-interest.yml'):
            form = yaml.safe_load((issue_dir / name).read_text(encoding='utf-8'))
            self.assertTrue(form['name'])
            ids = [item['id'] for item in form['body'] if item.get('id')]
            self.assertEqual(len(ids), len(set(ids)))
        round_form = yaml.safe_load((issue_dir / 'peer-review-round.yml').read_text(encoding='utf-8'))
        required = {item['id'] for item in round_form['body']
                    if item.get('validations', {}).get('required') is True}
        self.assertTrue({'release_url', 'paper_sha256', 'review_deadline', 'review_scope', 'questions'} <= required)
        self.assertIn('Public', '\n'.join(str(item) for item in round_form['body']))

    def test_pull_request_templates_cover_each_actor_and_warn_about_publication(self):
        templates = ROOT / '.github/PULL_REQUEST_TEMPLATE'
        expected = {
            'peer-review-report.md': ('round issue', 'pdf sha-256', 'conflict', 'kind: "review"'),
            'author-response.md': ('kind: "response"', 'same version', 'append-only'),
            'editorial-decision.md': ('editorial_decision', 'distinct reviewer', 'AI'),
        }
        for name, phrases in expected.items():
            text = (templates / name).read_text(encoding='utf-8').lower()
            for phrase in phrases:
                self.assertIn(phrase.lower(), text)


if __name__ == '__main__':
    unittest.main()

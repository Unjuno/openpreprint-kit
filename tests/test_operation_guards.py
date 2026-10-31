"""Integration contracts across manual publishing and read-only CI."""
from pathlib import Path
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]
class OperationGuardTests(unittest.TestCase):
    def test_api_preflight_precedes_timestamp_and_release(self):
        text=(ROOT/'.github/workflows/publish.yml').read_text()
        self.assertLess(text.index('scripts/preflight.py --repository'),text.index('timestamp.py stamp'))
        self.assertIn('secrets.OPK_ADMIN_READ_TOKEN',text)
        self.assertLess(text.index('--immutable-only'),text.index('--draft=false'))
    def test_records_compared_with_real_base_commit(self):
        text=(ROOT/'.github/workflows/validate.yml').read_text()
        self.assertIn('research_record.py',text)
        self.assertIn('github.event.pull_request.base.sha',text)
        self.assertIn('fetch-depth: 0',text)
        self.assertIn('--baseline',text)
    def test_all_workflow_timeouts_are_bounded(self):
        for path in (ROOT/'.github/workflows').glob('*.yml'):
            doc=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
            for job in doc['jobs'].values():
                self.assertLessEqual(int(job['timeout-minutes']),15)

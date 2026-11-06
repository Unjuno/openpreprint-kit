"""Network acceptance needs explicit human dispatch and a separate clean verifier runner."""
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]

class LiveWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.path=ROOT/'.github/workflows/live-acceptance.yml'
        self.assertTrue(self.path.is_file())
        self.raw=self.path.read_text()
        self.workflow=yaml.load(self.raw,Loader=yaml.BaseLoader)

    def test_manual_synthetic_only(self):
        self.assertEqual(set(self.workflow['on']),{'workflow_dispatch'})
        self.assertEqual(self.workflow['permissions'],{'contents':'read'})
        self.assertNotIn('gh release create',self.raw)
        self.assertNotIn('gh release edit',self.raw)
        self.assertIn('scripts/acceptance.py live',self.raw)

    def test_outside_verification_job_and_explicit_pin(self):
        jobs=self.workflow['jobs']
        self.assertIn('public-tsa',jobs)
        self.assertIn('fresh-verification',jobs)
        self.assertIn('public-tsa',jobs['fresh-verification']['needs'])
        self.assertIn('2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438',self.raw)
        self.assertIn("'scripts/preserve.py','restore'",self.raw)
        self.assertIn('--policy',self.raw)
        self.assertIn('download-artifact@',self.raw)

    def test_jobs_read_only_and_pinned_actions(self):
        for job in self.workflow['jobs'].values():
            self.assertTrue(int(job['timeout-minutes'])<=15)
            for step in job['steps']:
                if 'uses' in step:
                    self.assertRegex(step['uses'],r'@[0-9a-f]{40}$')
                if 'run' in step:
                    self.assertNotIn('${{',step['run'])
        self.assertNotIn('secrets.',self.raw)
        self.assertNotIn('contents: write',self.raw)

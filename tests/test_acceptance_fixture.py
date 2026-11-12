"""The public demo must never ingest user data or publish its private fixture/key."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'acceptance.py'

class AcceptanceFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def run_fixture(self, version='v1'):
        self.assertTrue(SCRIPT.is_file(),'acceptance runner missing')
        return subprocess.run([sys.executable,str(SCRIPT),'fixture','--out',str(self.root/version),'--version',version],capture_output=True,text=True,timeout=30)

    def test_fixture_generates_verified_research_and_private_receipt(self):
        r=self.run_fixture(); self.assertEqual(r.returncode,0,r.stderr)
        bundle=self.root/'v1'/'bundle'; self.assertTrue((bundle/'paper.pdf').exists())
        record=json.loads((bundle/'preprint-metadata.json').read_text())
        self.assertIn('SYNTHETIC',record['title'])
        catalog=json.loads((bundle/'research-assets.json').read_text())
        self.assertEqual({x['role'] for x in catalog['entries']},{'dataset','analysis_code','private_commitment'})
        self.assertNotIn(b'NO_PATIENT_PRIVATE_FIXTURE',(bundle/'research-assets.tar').read_bytes())
        self.assertFalse(list((self.root/'v1').rglob('*.key')))
        check=json.loads((self.root/'v1'/'fixture-report.json').read_text())
        self.assertEqual(check['private_match'],'PASS'); self.assertEqual(check['private_tamper_rejected'],'PASS')

    def test_existing_output_never_overwritten(self):
        (self.root/'v1').mkdir(); (self.root/'v1'/'keep').write_text('yes')
        r=self.run_fixture(); self.assertNotEqual(r.returncode,0)
        self.assertEqual((self.root/'v1'/'keep').read_text(),'yes')

    def test_v1_remains_when_v2_built(self):
        self.assertEqual(self.run_fixture().returncode,0)
        old=(self.root/'v1'/'bundle'/'manifest.json').read_bytes()
        self.assertEqual(self.run_fixture('v2').returncode,0)
        self.assertEqual(old,(self.root/'v1'/'bundle'/'manifest.json').read_bytes())
        self.assertNotEqual(old,(self.root/'v2'/'bundle'/'manifest.json').read_bytes())

    def test_fixture_contains_no_user_files(self):
        r=self.run_fixture(); self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual({p.name for p in (self.root/'v1').iterdir()},{'bundle','fixture-report.json','site'})

    def test_opt_in_source_export_is_allowlisted_and_contains_no_secrets(self):
        r = subprocess.run([sys.executable, str(SCRIPT), 'fixture', '--out', str(self.root/'source-demo'), '--version', 'v1', '--export-source'], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        source = self.root/'source-demo'/'source'
        files = {str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
        public = {'preprint.yaml', 'research-assets.yaml', 'paper/paper.pdf', 'data/synthetic.csv', 'analysis/reproduce.py'}
        receipts = {p for p in files if p.startswith('evidence/commitments/') and p.endswith('.json')}
        self.assertEqual(files, public | receipts)
        self.assertEqual(len(receipts), 1)
        for p in source.rglob('*'):
            if p.is_file():
                self.assertNotIn(b'NO_PATIENT_PRIVATE_FIXTURE', p.read_bytes())
                self.assertNotIn(b'PRIVATE KEY', p.read_bytes())
        self.assertFalse(list(source.rglob('*.key')))

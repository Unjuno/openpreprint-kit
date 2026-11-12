"""The paper's data summary must be evidence-based and fail closed."""
import importlib.util
import pathlib
import unittest
import subprocess
import sys
import tempfile

PATH = pathlib.Path(__file__).resolve().parents[1]/'manuscripts/openpreprint-kit/analysis/summarize_ci.py'

class FirstPaperEvidenceTests(unittest.TestCase):
    def load(self):
        self.assertTrue(PATH.is_file(), 'First-paper evidence analyzer must exist')
        spec=importlib.util.spec_from_file_location('opk_paper_summary', PATH)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_successful_count_is_recomputed(self):
        text='Python 3.12.16\nOpenSSL 3.0.13\ntest_a (test_one.Example.test_a) ... ok\ntest_b (test_two.Example.test_b) ... ok\nRan 2 tests in 1.0s\nOK\n'
        result=self.load().summarize(text)
        self.assertEqual(result['tests'],2)
        self.assertEqual(result['modules'],{'test_one':1,'test_two':1})

    def test_wrong_total_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'count'):
            self.load().summarize('test_a (test_one.Example.test_a) ... ok\nRan 2 tests in 1.0s\nOK\n')

    def test_duplicate_test_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.load().summarize('test_a (test_one.Example.test_a) ... ok\n'*2+'Ran 2 tests in 1.0s\nOK\n')

    def test_failed_or_skipped_summary_is_rejected(self):
        for ending in ['FAILED (failures=1)', 'OK (skipped=1)', 'OK\nFORGED']:
            with self.subTest(ending=ending),self.assertRaises(ValueError):
                self.load().summarize('test_a (test_one.Example.test_a) ... ok\nRan 1 tests in 1.0s\n'+ending+'\n')

    def test_archived_data_reproduces_pinned_baseline(self):
        m=self.load(); result=m.inspect_archive(PATH.parents[1]/'data')
        self.assertEqual(result['tests'],274)
        self.assertEqual(result['evaluated_commit'],'940d0d06d957cd0708f644a595911bdbc3fffa64')

    def test_exported_csv_matches_retained_data_with_portable_lf(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=pathlib.Path(temporary)/'counts.csv'
            result=subprocess.run([sys.executable,str(PATH),'--csv',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertNotIn(b'\r',output.read_bytes())
            self.assertEqual(output.read_bytes(),(PATH.parents[1]/'data/test-counts.csv').read_bytes())

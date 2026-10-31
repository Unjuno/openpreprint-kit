"""Publication preflight, fake API for deterministic safety checks."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PreflightTests(unittest.TestCase):
    def module(self):
        p=ROOT/'scripts/preflight.py'
        self.assertTrue(p.is_file(), 'preflight is not implemented')
        spec=importlib.util.spec_from_file_location('opk_preflight',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def responses(self):
        return {'':(200,{'private':False,'default_branch':'main'}),
                '/immutable-releases':(200,{'enabled':True}),
                '/commits/main':(200,{'sha':'a'*40}),
                '/releases/tags/v1':(404,{}),'/git/ref/tags/v1':(404,{})}

    def run_check(self, changes=None):
        module=self.module(); mapping=self.responses();mapping.update(changes or {})
        return module.preflight('example/paper','v1','a'*40,lambda path:mapping[path])

    def test_positive_preflight(self):
        self.assertEqual(self.run_check()['status'],'PASS')

    def test_disabled_immutability(self):
        with self.assertRaises(ValueError): self.run_check({'/immutable-releases':(200,{'enabled':False})})

    def test_no_administration_permission(self):
        with self.assertRaises(ValueError): self.run_check({'/immutable-releases':(403,{})})

    def test_private_repository(self):
        with self.assertRaises(ValueError): self.run_check({'':(200,{'private':True,'default_branch':'main'})})

    def test_branch_moved(self):
        with self.assertRaises(ValueError): self.run_check({'/commits/main':(200,{'sha':'b'*40})})

    def test_server_failure_is_not_a_free_tag(self):
        with self.assertRaises(ValueError): self.run_check({'/git/ref/tags/v1':(503,{})})

    def test_existing_tag(self):
        with self.assertRaises(ValueError): self.run_check({'/git/ref/tags/v1':(200,{'ref':'refs/tags/v1'})})

    def test_existing_release(self):
        with self.assertRaises(ValueError): self.run_check({'/releases/tags/v1':(200,{'draft':True})})

    def test_malformed_response_is_rejected(self):
        with self.assertRaises(ValueError): self.run_check({'/immutable-releases':(200,{'enabled':'true'})})

    def test_untrusted_repository_string(self):
        module=self.module()
        with self.assertRaises(ValueError):
            module.preflight('../private/secrets','v1','a'*40,lambda _:self.fail('must not request'))

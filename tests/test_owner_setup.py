"""Owner configuration must be explicit, narrow, verified and non-destructive."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/owner_setup.py'

class OwnerSetupTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(),'owner setup command missing')
        sys.path.insert(0,str(ROOT/'scripts'))
        try:
            spec=importlib.util.spec_from_file_location('opk_owner_setup',SCRIPT)
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
        finally: sys.path.pop(0)

    def service(self,public=True,admin=True):
        state={'is_template':False,'immutable':False}; calls=[]
        def api(method,path,payload=None):
            calls.append((method,path,payload))
            if method=='GET' and path=='repos/example/research':
                return {'full_name':'example/research','private':not public,'permissions':{'admin':admin},'is_template':state['is_template']}
            if method=='GET' and path.endswith('immutable-releases'): return {'enabled':state['immutable']}
            if method=='PUT' and path.endswith('immutable-releases'): state['immutable']=True; return None
            if method=='PATCH': state['is_template']=payload['is_template']; return {'is_template':state['is_template']}
            raise AssertionError('unexpected API call')
        return api,calls,state

    def test_dry_run_does_not_modify_settings(self):
        mod=self.module(); api,calls,state=self.service()
        report=mod.configure('example/research',False,True,api)
        self.assertTrue(all(x[0]=='GET' for x in calls)); self.assertFalse(state['immutable'])
        self.assertEqual(report['mode'],'READ_ONLY'); self.assertFalse(report['release_created'])

    def test_apply_enables_only_requested_settings_and_reads_back(self):
        mod=self.module(); api,calls,state=self.service()
        report=mod.configure('example/research',True,True,api)
        self.assertTrue(state['immutable']); self.assertTrue(state['is_template']); self.assertEqual(report['status'],'PASS')
        writes=[(m,p,d) for m,p,d in calls if m!='GET']
        self.assertEqual(writes,[('PUT','repos/example/research/immutable-releases',None),('PATCH','repos/example/research',{'is_template':True})])
        self.assertFalse(report['release_created'])

    def test_without_template_flag_never_marks_paper_as_template(self):
        mod=self.module(); api,calls,state=self.service()
        mod.configure('example/research',True,False,api)
        self.assertFalse(state['is_template']); self.assertTrue(state['immutable'])

    def test_private_repo_requires_separate_explicit_visibility_decision(self):
        mod=self.module(); api,calls,_=self.service(public=False)
        with self.assertRaises(ValueError): mod.configure('example/research',True,True,api)
        self.assertTrue(all(x[0]=='GET' for x in calls))

    def test_no_admin_permission_stops_before_write(self):
        mod=self.module(); api,calls,_=self.service(admin=False)
        with self.assertRaises(ValueError): mod.configure('example/research',True,True,api)
        self.assertTrue(all(x[0]=='GET' for x in calls))

    def test_failed_readback_is_not_success(self):
        mod=self.module(); api,calls,state=self.service()
        def ignored_write(m,p,d=None):
            if m=='PUT': return None
            return api(m,p,d)
        with self.assertRaises(ValueError): mod.configure('example/research',True,False,ignored_write)

    def test_invalid_repo_causes_no_api_call(self):
        mod=self.module(); api,calls,_=self.service()
        with self.assertRaises(ValueError): mod.configure('../wrong/path',True,True,api)
        self.assertFalse(calls)

"""Human assertions remain assertions; record mutations must be visible."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ResearchRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'reviews/evidence').mkdir(parents=True)
        self.report=self.root/'reviews/evidence/report.md';self.report.write_text('Synthetic review for testing only.')
        self.data={'schema_version':1,'events':[]}
    def tearDown(self): self.temp.cleanup()
    def module(self):
        path=ROOT/'scripts/research_record.py'
        self.assertTrue(path.is_file(),'review record validation is not implemented')
        spec=importlib.util.spec_from_file_location('opk_record',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def event(self,kind='review',id='e1'):
        event={'id':id,'kind':kind,'version':'v1','paper_sha256':'a'*64,
               'recorded_at':'2026-01-01T00:00:00Z','actor':'Synthetic reviewer',
               'conflicts':'Synthetic fixture; no real review.', 'summary':'Test record',
               'evidence':[{'path':'reviews/evidence/report.md','sha256':hashlib.sha256(self.report.read_bytes()).hexdigest()}]}
        if kind=='correction': event['replacement']={'version':'v2','paper_sha256':'b'*64}
        return event
    def test_empty_record_is_not_peer_reviewed(self):
        m=self.module();self.assertEqual(m.validate_record(self.data,self.root),[])
        self.assertEqual(m.status_for(self.data,'v1','a'*64),'UNREVIEWED_PREPRINT')
    def test_review_records_are_not_a_certification(self):
        m=self.module();self.data['events'].append(self.event())
        self.assertEqual(m.validate_record(self.data,self.root),[])
        self.assertEqual(m.status_for(self.data,'v1','a'*64),'REVIEWS_RECORDED')
    def test_append_is_allowed(self):
        m=self.module();base=copy.deepcopy(self.data);self.data['events'].append(self.event())
        self.assertEqual(m.validate_record(self.data,self.root,base),[])
    def test_previous_event_edit_is_rejected(self):
        m=self.module();self.data['events'].append(self.event());base=copy.deepcopy(self.data)
        self.data['events'][0]['summary']='Rewritten'
        self.assertTrue(m.validate_record(self.data,self.root,base))
    def test_previous_event_deletion_is_rejected(self):
        m=self.module();base={'schema_version':1,'events':[self.event()]}
        self.assertTrue(m.validate_record(self.data,self.root,base))
    def test_evidence_rewrite_is_rejected(self):
        m=self.module();self.data['events'].append(self.event());self.report.write_text('Different')
        self.assertTrue(m.validate_record(self.data,self.root))
    def test_missing_evidence_is_rejected(self):
        m=self.module();self.data['events'].append(self.event());self.report.unlink()
        self.assertTrue(m.validate_record(self.data,self.root))
    def test_path_escape_is_rejected(self):
        m=self.module();e=self.event();e['evidence'][0]['path']='../private.txt';self.data['events']=[e]
        self.assertTrue(m.validate_record(self.data,self.root))
    def test_symlink_evidence_is_rejected(self):
        m=self.module();self.data['events']=[self.event()];other=self.root/'other.md';other.write_bytes(self.report.read_bytes())
        self.report.unlink();self.report.symlink_to(other)
        self.assertTrue(m.validate_record(self.data,self.root))
    def test_conflicting_hash_for_same_version_is_rejected(self):
        m=self.module();e=self.event(id='e2');e['paper_sha256']='b'*64
        self.data['events']=[self.event(),e];self.assertTrue(m.validate_record(self.data,self.root))
    def test_duplicate_ids_are_rejected(self):
        m=self.module();self.data['events']=[self.event(),self.event()]
        self.assertTrue(m.validate_record(self.data,self.root))
    def test_retraction_cannot_be_cleared_by_later_review(self):
        m=self.module();self.data['events']=[self.event('retraction'),self.event(id='e2')]
        self.assertEqual(m.validate_record(self.data,self.root),[])
        self.assertEqual(m.status_for(self.data,'v1','a'*64),'RETRACTED')
    def test_other_versions_do_not_inherit_review(self):
        m=self.module();self.data['events']=[self.event()]
        self.assertEqual(m.status_for(self.data,'v2','b'*64),'UNREVIEWED_PREPRINT')
    def test_correction_requires_new_version_and_hash(self):
        m=self.module();e=self.event('correction');e['replacement']['version']='v1';self.data['events']=[e]
        self.assertTrue(m.validate_record(self.data,self.root))
    def test_unknown_kind_and_naive_time_are_rejected(self):
        m=self.module();e=self.event();e['kind']='peer_reviewed';e['recorded_at']='2026-01-01'
        self.data['events']=[e];self.assertTrue(m.validate_record(self.data,self.root))
    def test_boolean_schema_is_rejected(self):
        m=self.module();self.data['schema_version']=True;self.assertTrue(m.validate_record(self.data,self.root))

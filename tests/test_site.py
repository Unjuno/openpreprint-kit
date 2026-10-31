"""Reader-facing claims must not outrun available evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import test_research_record

ROOT=Path(__file__).resolve().parents[1]

class SiteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.bundle=self.root/'bundle';self.bundle.mkdir();self.output=self.root/'site'
        (self.root/'reviews').mkdir();self.record=self.root/'reviews/record.json'
        self.record.write_text('{"schema_version":1,"events":[]}')
        paper=b'%PDF-1.7\nSynthetic fixture\n%%EOF\n'
        digest=hashlib.sha256(paper).hexdigest()
        metadata={'title':'<script>alert(1)</script>', 'version':'v1','authors':[{'name':'A & B'}],
                  'abstract':'A synthetic abstract', 'license':'CC-BY-4.0', 'paper_sha256':digest}
        self.digest=digest
        payload={'paper.pdf':paper,'CITATION.cff':b'cff-version: 1.2.0\n',
                 'citation.bib':b'@misc{test,title={Test}}\n', 'RELEASE_NOTES.md':b'Notes\n',
                 'preprint-metadata.json':json.dumps(metadata).encode()}
        files={}
        for name,raw in payload.items():
            (self.bundle/name).write_bytes(raw);files[name]={'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)}
        (self.bundle/'manifest.json').write_text(json.dumps({'schema_version':1,'algorithm':'sha256','files':files}))
        names=sorted(set(files)|{'manifest.json'})
        (self.bundle/'SHA256SUMS').write_text(''.join(hashlib.sha256((self.bundle/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in names))
    def tearDown(self): self.temp.cleanup()
    def module(self):
        p=ROOT/'scripts/build_site.py';self.assertTrue(p.is_file(),'reader view is not implemented')
        if str(ROOT/'scripts') not in sys.path:sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location('opk_site',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def build(self):
        self.module().build_site(self.bundle,self.root,self.output,'example/paper')
        return (self.output/'index.html').read_text()
    def test_default_is_unreviewed_and_not_time_verified(self):
        text=self.build();self.assertIn('UNREVIEWED_PREPRINT',text);self.assertIn('NOT_VERIFIED',text)
    def test_untrusted_html_is_escaped(self):
        text=self.build();self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)
        self.assertIn('A &amp; B',text)
    def test_retraction_is_prominent_and_original_pdf_remains(self):
        helper=test_research_record.ResearchRecordTests();helper.setUp()
        try:
            import shutil
            shutil.copytree(helper.root/'reviews/evidence',self.root/'reviews/evidence')
            e=helper.event('retraction');e['paper_sha256']=self.digest
            self.record.write_text(json.dumps({'schema_version':1,'events':[e]}))
            text=self.build();self.assertIn('RETRACTED',text);self.assertTrue((self.output/'assets/paper.pdf').is_file())
        finally:helper.tearDown()
    def test_present_timestamp_is_not_claimed_verified(self):
        (self.bundle/'timestamp.tsq').write_bytes(b'not verified');(self.bundle/'timestamp.tsr').write_bytes(b'not verified')
        text=self.build();self.assertIn('NOT_VERIFIED',text);self.assertIn('timestamp.tsr',text)
    def test_tampered_pdf_prevents_site_creation(self):
        (self.bundle/'paper.pdf').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.build()
        self.assertFalse(self.output.exists())
    def test_output_cannot_be_inside_bundle(self):
        with self.assertRaises(ValueError):self.module().build_site(self.bundle,self.root,self.bundle/'site','example/paper')
    def test_unsafe_repository_is_rejected(self):
        with self.assertRaises(ValueError):self.module().build_site(self.bundle,self.root,self.output,'javascript:alert(1)')

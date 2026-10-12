import json
import hashlib
from unittest.mock import patch
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from .server import make_server, PUBLIC, ROOT, FILES

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=make_server(0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_address[1]}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)

    def get(self,path,method='GET',headers=None):
        return urlopen(Request(self.base+path,method=method,headers=headers or {}))

    def rejected(self,path,code,**kwargs):
        with self.assertRaises(HTTPError) as error:self.get(path,**kwargs)
        self.assertEqual(error.exception.code,code)

    def test_static_snapshot_and_sources(self):
        for path in ['/','/app.js','/core.mjs','/styles.css','/data.json','/sources/current','/sources/purple','/sources/migration']:
            with self.get(path) as response:self.assertEqual(response.status,200);self.assertGreater(len(response.read()),20)
        with self.get('/data.json') as response:
            self.assertEqual(json.load(response)['schema'],'homelab-evidence-map-v1')

    def test_loopback_and_security_headers(self):
        self.assertEqual(self.server.server_address[0],'127.0.0.1')
        with self.get('/') as response:
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
            self.assertIn("form-action 'none'",response.headers['Content-Security-Policy'])
            self.assertEqual(response.headers['X-Frame-Options'],'DENY')
            self.assertIsNone(response.headers.get('Access-Control-Allow-Origin'))
        with self.get('/',method='HEAD') as response:self.assertEqual(response.read(),b'')

    def test_host_and_cross_origin_requests_rejected(self):
        self.rejected('/',403,headers={'Host':'attacker.invalid'})
        self.rejected('/data.json',403,headers={'Origin':'https://example.invalid'})
        for site in ['same-site','cross-site']:
            self.rejected('/data.json',403,headers={'Sec-Fetch-Site':site})

    def test_no_mutation_upload_scan_or_arbitrary_file_routes(self):
        before=(PUBLIC/'data.json').read_bytes()
        for method in ['POST','PUT','PATCH','DELETE','OPTIONS']:self.rejected('/data.json',405,method=method)
        for path in ['/api/scan','/api/hosts','/api/upload','/../AGENTS.md','/sources/../../AGENTS.md','/.env','/sources/current?file=/etc/passwd']:self.rejected(path,404)
        self.assertEqual((PUBLIC/'data.json').read_bytes(),before)

    def test_changed_document_cannot_impersonate_pinned_evidence(self):
        with patch.dict(FILES, {'/sources/current': (PUBLIC / 'index.html', 'text/plain; charset=utf-8')}):
            self.rejected('/sources/current',409)

    def test_snapshot_qualifies_current_and_historical_evidence(self):
        data=json.loads((PUBLIC/'data.json').read_text());nodes={n['id']:n for n in data['nodes']}
        self.assertEqual(nodes['dc']['status'],'BLOCKED');self.assertEqual(nodes['win']['status'],'BLOCKED')
        self.assertEqual(nodes['lab']['status'],'NOT_RUN');self.assertEqual(nodes['sec']['status'],'REVIEW')
        self.assertTrue(any(c['status']=='OBSERVED' and c['date']=='2026-10-11' for c in nodes['logs']['claims']))
        self.assertEqual(nodes['ufw']['status'],'HISTORICAL')
        for ident in ['soc','audit','ir','prompt']:self.assertEqual(nodes[ident]['status'],'OPEN_PR')
        for key in ['current','purple','migration']:
            source=data['sources'][key]
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        self.assertIn('Fresh UBUNTU01', (ROOT/data['sources']['current']['path']).read_text())

if __name__=='__main__':unittest.main()

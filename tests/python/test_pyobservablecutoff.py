"""Observable frontend agreement with the shared Python engine and local-asset contract."""
import importlib.util
import hashlib
import json
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path
from cpjtest import ROOT, factor, number, rows, run_analysis
sys.path.insert(0, str(ROOT / "inst/python"))

spec=importlib.util.spec_from_file_location('observablecutoff',ROOT/'inst/python/analyses/meddecide/pyobservablecutoff.py')
observable=importlib.util.module_from_spec(spec);spec.loader.exec_module(observable)


class ObservableCutoff(unittest.TestCase):
    def test_native_results_identical_to_d3(self):
        data={'x':number([1,2,2,4,5,6,None,8]),'g':factor(['N','N','P','N','P','P','P',None])}
        for direction,method,criterion in [('ge','exact','errors'),('le','wilson','youden'),('ge','wilson','cost')]:
            options=dict(marker='x',reference='g',positive='P',direction=direction,ciMethod=method,criterion=criterion,ciWidth=90,fpCost=2,fnCost=7,cutoff='2')
            a=run_analysis('pyd3cutoff',data,options);b=run_analysis('pyobservablecutoff',data,options)
            self.assertEqual(b['status'],'ok',b.get('error'))
            for field in ['tables','plots','texts','notices']:
                self.assertEqual(a[field],b[field],field)
            html=b['htmls']['explorer']
            self.assertIn('"excluded": 2',html)
            self.assertIn('"row": "1"',html)
            self.assertIn('Observable cutoff lab',html)

    def test_automatic_undefined_and_missing_event(self):
        data={'x':number([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])}
        for cutoff in ['', '100', '-100']:
            options=dict(marker='x',reference='g',positive='P',cutoff=cutoff)
            a=run_analysis('pyd3cutoff',data,options);b=run_analysis('pyobservablecutoff',data,options)
            self.assertEqual(a['tables'],b['tables'])
        self.assertIsNone(rows(b,'metrics')[3]['estimate'])
        b=run_analysis('pyobservablecutoff',data,dict(marker='x',reference='g'))
        self.assertEqual(b['status'],'input_error')

    def test_maximum_payload_and_invalid_settings(self):
        data={'x':number(range(1000)),'g':factor(['N']*500+['P']*500)}
        options=dict(marker='x',reference='g',positive='P')
        result=run_analysis('pyobservablecutoff',data,options)
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertLess(len(result['htmls']['explorer'].encode()),1500000)
        for invalid in [dict(cutoff='nan'),dict(ciWidth=100),dict(fpCost=-1),dict(direction='bad')]:
            result=run_analysis('pyobservablecutoff',data,dict(options,**invalid))
            self.assertEqual(result['status'],'input_error')

    def test_offline_assets_escaping_and_syntax(self):
        document=observable.html_document(dict(label='</script><img src=x onerror="alert(1)">'))
        self.assertNotIn('<img src=x',document)
        self.assertEqual(document.count('</script>'),5)
        self.assertNotIn('<script src=',document)
        template=(ROOT/'inst/python/templates/observablecutoff.html').read_text()
        for feature in ['Inputs.range','Inputs.select','Inputs.search','Inputs.table','Plot.crosshair','Plot.pointer','d3.drag','Apply to HTML tables']:
            self.assertIn(feature,template)
        for forbidden in ['setOption','fetch(','XMLHttpRequest','innerHTML','function interval']:
            self.assertNotIn(forbidden,template)
        with tempfile.TemporaryDirectory() as directory:
            scripts=[s.split('</script>')[0] for s in document.split('<script>')[1:]]
            for i,script in enumerate(scripts):
                file=Path(directory)/f'{i}.js';file.write_text(script)
                subprocess.run(['node','--check',str(file)],capture_output=True,check=True)

    def test_reviewed_vendor_assets_match_manifest(self):
        base=ROOT/'inst/python/vendor'
        manifest=json.loads((base/'observable-manifest.json').read_text())
        self.assertFalse(manifest['runtime_network_required'])
        for library in manifest['libraries']:
            self.assertEqual(hashlib.sha256((base/library['file']).read_bytes()).hexdigest(),library['sha256'])
        for license in ['observable-plot-LICENSE.txt','observable-inputs-LICENSE.txt','htl-LICENSE.txt']:
            self.assertIn('Permission to use, copy, modify', (base/license).read_text())

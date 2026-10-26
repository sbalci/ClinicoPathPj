"""Native SVG transport, escaping and shared numerical-contract regression checks."""
import copy
import importlib.util
import json
import unittest
from html.parser import HTMLParser
from cpjtest import ROOT, factor, number, rows, run_analysis


class Markup(HTMLParser):
    def __init__(self, content):
        super().__init__(); self.svg = []; self.tags = []; self.feed(content)
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'svg': self.svg.append(dict(attrs))


class SvgCutoff(unittest.TestCase):
    def data(self):
        return {'x': number([1,2,2,4,5,6,None,8]), 'g': factor(['N','N','P','N','P','P','P',None])}

    def test_shared_results_both_directions_methods_and_criteria(self):
        for direction in ['ge','le']:
            for method in ['exact','wilson']:
                for criterion in ['errors','youden','cost']:
                    opts=dict(marker='x',reference='g',positive='P',direction=direction,ciMethod=method,
                              criterion=criterion,cutoff='2',fpCost=2,fnCost=7,ciWidth=90)
                    a=run_analysis('pyd3cutoff',self.data(),opts)
                    b=run_analysis('pysvgcutoff',self.data(),opts)
                    self.assertEqual(b['status'],'ok',b.get('error'))
                    for field in ['tables','plots','notices']: self.assertEqual(a[field],b[field],field)
                    self.assertFalse(b['htmls'])
                    doc=Markup(b['svgs']['explorer']); self.assertEqual(len(doc.svg),1)
                    p=json.loads(doc.svg[0]['data-payload'])
                    self.assertEqual(p['expected'],dict(tp=3,fp=2,fn=0,tn=1) if direction=='ge' else dict(tp=1,fp=2,fn=2,tn=1))
                    self.assertEqual(p['excluded'],2)
                    self.assertEqual([r['row'] for r in p['rows']],list(map(str,range(1,7))))

    def test_endpoint_and_automatic_rules(self):
        for cutoff in ['', '-100', '100']:
            opts=dict(marker='x',reference='g',positive='P',cutoff=cutoff)
            a=run_analysis('pyd3cutoff',self.data(),opts); b=run_analysis('pysvgcutoff',self.data(),opts)
            self.assertEqual(a['tables'],b['tables'])

    def test_payload_limits_and_missing_event(self):
        opts=dict(marker='x',reference='g',positive='P')
        data={'x':number(range(1000)),'g':factor(['N']*500+['P']*500)}
        result=run_analysis('pysvgcutoff',data,opts)
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertLess(len(result['svgs']['explorer'].encode()),1500000)
        for bad in [dict(positive=None),dict(cutoff='nan'),dict(direction='bad')]:
            self.assertEqual(run_analysis('pysvgcutoff',self.data(),dict(opts,**bad))['status'],'input_error')

    def test_labels_cannot_inject_markup(self):
        name='</svg><script>alert(1)</script>&"'
        result=run_analysis('pysvgcutoff',{name:number([1,2]),'g':factor(['N','P'])},dict(marker=name,reference='g',positive='P'))
        doc=Markup(result['svgs']['explorer'])
        self.assertNotIn('script',doc.tags)
        self.assertEqual(json.loads(doc.svg[0]['data-payload'])['measurement'],name)

    def test_generator_accepts_only_local_script_files(self):
        sp=importlib.util.spec_from_file_location('gen',ROOT/'tools/generate.py')
        gen=importlib.util.module_from_spec(sp);sp.loader.exec_module(gen)
        source=ROOT/'inst/python/analyses/meddecide/pysvgcutoff.py'
        spec=gen.read_spec(source); gen.validate(spec,'pysvgcutoff')
        for bad in [['../escape.js'],['https://example.org/x.js'],['js/missing.js']]:
            changed=copy.deepcopy(spec);changed['results'][1]['scripts']=bad
            with self.assertRaises(gen.SpecError):gen.validate(changed,'pysvgcutoff')
        generated=gen.b_r(spec,'test')
        self.assertIn('setScripts(c("js/pysvgcutoff.js"))',generated)
        self.assertLess(generated.index('.init = function()'),generated.index('setScripts('))
        self.assertLess(generated.index('setScripts('),generated.index('.run = function()'))

    def test_svg_transport_rejects_wrong_names_and_large_content(self):
        import sys
        sys.path.insert(0,str(ROOT/'inst/python'))
        from cpj_runtime import Output
        out=Output(dict(results=[dict(name='s',type='Svg')]))
        with self.assertRaises(KeyError):out.svg('bad','<svg/>')
        with self.assertRaises(ValueError):out.svg('s','x'*1500001)
        out.svg('s','<svg/>');self.assertEqual(out.svgs,dict(s='<svg/>'))

"""Validate GUI-saved ROC artifacts without executing their serialized analyses."""
import base64
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import zipfile
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'
sys.path.insert(0,str(ROOT/'inst/python/_vendor'))
from PIL import Image
spec=importlib.util.spec_from_file_location('native_tables',ROOT/'tools/check-summary-service-artifacts.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def require(ok,message):
    if not ok:raise ValueError(message)


def inspect(html,z=None):
    tables=module.Tables(html).tables;require(len(tables)==5,'Expected five ROC tables')
    require(tables[0]==[['Common Complete-Case Cohort'],['Source Rows','Retained','Excluded','Reference Positive','Reference Negative'],['12','8','4','4','4']],'Wrong common cohort')
    require(tables[1][2:4]==[['Measurement_A','>=','0.656','0.215','0.235','1.000','Approximate normal CI'],['Measurement_B','>=','0.719','0.196','0.335','1.000','Approximate normal CI']],'Wrong displayed AUC/intervals')
    require('empty cells do not mean certainty' in tables[1][-1][0],'Missing uncertainty disclosure')
    reference=json.loads((EXPORTS/'python-roc-example-reference-20261111.json').read_text())
    expected=['Measurement_A','Measurement_B','-0.0625',f"{reference['se']:.3f}",f"{reference['lower']:.3f}",f"{reference['upper']:.3f}",f"{reference['z']:.3f}",f"{reference['p']:.3f}"[1:],'Approximate paired DeLong test']
    require(tables[2][2]==expected,'Wrong paired contrast/uncertainty/p-value')
    require('unadjusted' in tables[2][-1][0],'Missing multiplicity disclosure')
    with (ROOT/'data/python_roc_examples.csv').open() as f:source=list(csv.DictReader(f))
    retained=[(i,r) for i,r in enumerate(source) if r['Reference'] and r['Measurement_A'] and r['Measurement_B']]
    expected_thresholds=[]
    for name in ['Measurement_A','Measurement_B']:
        values=[float(r[name]) for _,r in retained];truth=[r['Reference']=='Positive' for _,r in retained]
        for cutoff in [None]+sorted(set(values),reverse=True):
            pred=[False if cutoff is None else x>=cutoff for x in values]
            tp=sum(a and b for a,b in zip(pred,truth));fp=sum(a and not b for a,b in zip(pred,truth));fn=4-tp;tn=4-fp
            expected_thresholds.append([name,'none positive' if cutoff is None else '>=','.' if cutoff is None else f'{cutoff:.2f}',str(tp),str(fp),str(fn),str(tn),f'{tp/4*100:.1f} %',f'{tn/4*100:.1f} %'])
    require([[re.sub(r'\s+%', '%', c) for c in row] for row in tables[3][2:-1]]==
            [[re.sub(r'\s+%', '%', c) for c in row] for row in expected_thresholds],
            'Wrong observed-threshold classifications')
    expected_cases=[[str(i+1),r['Reference'],f"{float(r['Measurement_A']):.2f}",f"{float(r['Measurement_B']):.2f}",'.'] for i,r in retained]
    require(tables[4][2:-1]==expected_cases,'Wrong original source rows')
    if z is None:
        resources=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)
        require(len(resources)==1,'Expected one embedded PNG');png=base64.b64decode(re.sub(r'\s','',resources[0]),validate=True)
    else:
        resources=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        require(len(resources)==1,'Expected one cached PNG');png=z.read(unquote(resources[0]))
    with Image.open(io.BytesIO(png)) as image:
        require(image.width>=400 and image.height>=300,'Plot dimensions too small')
        pixels=hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest();dimensions=[image.width,image.height]
    return dict(png_sha256=hashlib.sha256(png).hexdigest(),pixel_sha256=pixels,dimensions=dimensions)


def check():
    report={};source_bytes=[]
    for suffix in ['comparison','reopened']:
        path=EXPORTS/f'python-roc-0.3.64-{suffix}.omv'
        with zipfile.ZipFile(path) as z:
            require(z.testzip() is None,'OMV CRC failed')
            report[suffix]=inspect(z.read('index.html').decode(),z)
            report[suffix]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            source_bytes.append({n:z.read(n) for n in ['data.bin','metadata.json','xdata.json']})
        html=EXPORTS/f'python-roc-0.3.64-{suffix}.html';html_text=html.read_text()
        report[suffix]['HTML']=inspect(html_text)
        require(report[suffix]['HTML']['pixel_sha256']==report[suffix]['pixel_sha256'],'HTML plot pixels differ from saved plot')
    pending=EXPORTS/'python-roc-0.3.64-incomplete.omv'
    with zipfile.ZipFile(pending) as z:
        require(z.testzip() is None,'Incomplete OMV CRC failed')
        html=z.read('index.html').decode();tables=module.Tables(html).tables
        require(len(tables)==5 and all(len(t)==3 and all(not cell.strip() for cell in t[2]) for t in tables),'Incomplete analysis retained computed table rows')
        require(not any(n.endswith('.png') for n in z.namelist()),'Incomplete analysis retained cached plot')
        require('also choose' in html and 'Score 1' in html,'Missing incomplete-role guidance')
        source_bytes.append({n:z.read(n) for n in ['data.bin','metadata.json','xdata.json']})
    require(all(x==source_bytes[0] for x in source_bytes),'GUI lifecycle changed dataset bytes/metadata')
    report['source_bytes_and_metadata_unchanged']=True
    report['incomplete_tables_and_plot_cleared']=True
    report['equivalent_saved_plot_pixels_identical']=report['comparison']['pixel_sha256']==report['reopened']['pixel_sha256']
    require(report['equivalent_saved_plot_pixels_identical'],'Equivalent-input saved plot changed')
    exported=EXPORTS/'python-roc-0.3.64-reopened.png'
    with Image.open(exported) as image:
        pixels=hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest();dims=[image.width,image.height]
    report['native_PNG']=dict(sha256=hashlib.sha256(exported.read_bytes()).hexdigest(),dimensions=dims,pixel_sha256=pixels)
    with Image.open(EXPORTS/'python-roc-native-example-20261111.png') as reference_image:
        reference_dimensions=[reference_image.width,reference_image.height]
        reference_pixels=hashlib.sha256(reference_image.convert('RGBA').tobytes()).hexdigest()
    require(dims==reference_dimensions and pixels==reference_pixels,
            'Native PNG differs from independently rendered same-resolution reference')
    report['native_PNG']['matches_same_resolution_native_reference']=True
    report['native_PNG']['matches_saved_pixels']=pixels==report['reopened']['pixel_sha256']
    report['native_PNG']['resolution_note']='GUI PNG export uses 1300x900; saved/HTML plot uses 1038x718. Same-size independent native reference is pixel-identical.'
    probes={'AUC':html_text.replace('0.656','0.556',1),'paired_p':html_text.replace('.789','.689',1),
            'row_value':html_text.replace('5.00','6.00',1),'missing_plot':re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html_text,count=1)}
    for name,changed in probes.items():
        require(changed!=html_text,'No-op corruption probe '+name)
        try:inspect(changed)
        except (ValueError,IndexError):continue
        raise ValueError('Accepted artifact corruption '+name)
    report['corruption_probes_rejected']=list(probes)
    report['scope']='GUI-saved/recalculated/exported ROC artifacts; no clinical or cross-platform qualification'
    (EXPORTS/'python-roc-0.3.64-artifacts-20261111.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()

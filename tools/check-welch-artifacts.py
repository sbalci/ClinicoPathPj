"""Validate 0.3.69 native GUI saves/exports against independent R fixtures."""
import base64
import importlib.util
import json
from pathlib import Path
import re
import zipfile
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT/'docs/validation-exports'
spec = importlib.util.spec_from_file_location('standardized_artifacts',ROOT/'tools/check-standardized-artifacts.py')
std = importlib.util.module_from_spec(spec);spec.loader.exec_module(std)
base, require, displayed = std.base, std.require, std.displayed
REF = next(f for f in json.loads((ROOT/'tests/fixtures/welch-standardized-effects.json').read_text())['fixtures']
           if f['id']=='hand_unequal_variance')
POINT = next(r for r in REF['runs'] if r['confidence']==.95)
MODES = ('compatibility','valid','off','incomplete','recovered','reopened')


def inspect(html, mode, archive=None):
    if mode=='compatibility':return std.inspect(html,'reopened',archive)
    tables = base.module.Tables(html).tables
    require(len(tables)==(13 if mode=='off' else 15),'Wrong native table count '+mode)
    chunks = re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    welch_chunks = [c for c in chunks if 'Welch RMS Standardizer' in c or 'RMS Standardized Difference (Point Only)' in c]
    require(len(welch_chunks)==(0 if mode=='off' else 2),'Wrong Welch table count')
    if mode=='incomplete':
        require(all(len(t)==3 and all(not c.strip() for c in t[2]) for t in tables[:7]),
                'Incomplete independent analysis retained values/notes')
        # Validate the unaffected paired results against the qualified original artifact.
        with zipfile.ZipFile(EXPORTS/'python-standardized-0.3.68-reopened.omv') as old:
            require(tables[7:]==base.module.Tables(old.read('index.html').decode()).tables[8:],
                    'Incomplete input changed paired results')
        paths = re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        require(archive is not None and len(paths)==2,'Incomplete retained raw/standardized independent image')
        require(len([n for n in archive.namelist() if n.endswith('.png')])==2,'Stale cached independent image')
        return {k:base.image_info(archive.read(unquote(p))) for k,p in zip(('paired_raw','paired_standardized'),paths)}
    if mode!='off':
        model, point = tables[5:7]
        require(model[1]==['Standardizer','RMS SD','Welch SE df','SD Moment df'],'Wrong denominator columns')
        require(model[2][0]=='Root mean of the two sample variances','Wrong RMS denominator label')
        for value,key in zip(model[2][1:],('standardizer_sd','welch_df','sd_moment_df')):displayed(value,POINT[key])
        require(point[1]==['First','Second','RMS Effect','Status'],'Unexpected standardized inference columns')
        require(point[2][:2]==['First','Second'],'Wrong point orientation')
        displayed(point[2][2],POINT['d_rms']);require(point[2][3]=='point_only','Wrong point status')
        require('no standardized confidence interval' in point[-1][0],'Missing uncertainty omission')
        require('Welch SE df and SD moment df describe different quantities' in model[-1][0],'Missing df distinction')
    # Reuse the independently qualified raw/paired validator after removing only
    # the separately validated Welch tables. Plot resources remain untouched.
    cleaned = html
    for chunk in welch_chunks: cleaned = cleaned.replace(chunk,'',1)
    return std.inspect(cleaned,'welch',archive)


def check():
    report, tables, data = {}, {}, []
    for mode in MODES:
        path = EXPORTS/f'python-welch-0.3.69-{mode}.omv'
        with zipfile.ZipFile(path) as z:
            require(z.testzip() is None,'Invalid saved archive '+mode)
            html = z.read('index.html').decode()
            report[mode]=inspect(html,mode,z)
            tables[mode]=base.module.Tables(html).tables
            data.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    for mode in ('recovered','reopened'):
        require(tables[mode]==tables['valid'],'Equivalent tables changed '+mode)
        require({k:std.pixels(v) for k,v in report[mode].items()}==
                {k:std.pixels(v) for k,v in report['valid'].items()},'Equivalent plot pixels changed '+mode)
    require(tables['off'][:5]==tables['valid'][:5],'Raw results changed on standardized off')
    require(tables['off'][5:]==tables['valid'][7:],'Paired results changed on standardized off')
    require(all(d==data[0] for d in data),'GUI lifecycle changed dataset bytes/metadata')
    with zipfile.ZipFile(EXPORTS/'python-standardized-0.3.68-reopened.omv') as z:
        require(all(z.read(k)==data[0][k] for k in data[0]),'Compatibility changed original dataset')
    html = (EXPORTS/'python-welch-0.3.69-reopened.html').read_text()
    report['HTML']=inspect(html,'reopened')
    require({k:std.pixels(v) for k,v in report['HTML'].items()}==
            {k:std.pixels(v) for k,v in report['valid'].items()},'HTML plot pixels changed')
    png = base.image_info((EXPORTS/'python-welch-0.3.69-raw-plot.png').read_bytes())
    require(png['dimensions']==[1300,600],'Unexpected direct raw plot size')
    source_png=base.image_info((EXPORTS/'python-estimation-independent-native-20261112.png').read_bytes())
    require(std.pixels(png)==std.pixels(source_png),'Direct PNG differs from source-native Welch plot')
    with zipfile.ZipFile(EXPORTS/'python-standardized-0.3.68-defaults.omv') as old:
        # The same Welch raw estimate/confidence/roles must produce identical pixels.
        prior=std.inspect(old.read('index.html').decode(),'defaults',old)
        require(std.pixels(report['valid']['independent_raw'])==std.pixels(prior['independent_raw']),
                'Same raw Welch plot changed from 0.3.68')
    chunks = re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    point_chunk = next(c for c in chunks if 'RMS Standardized Difference (Point Only)' in c)
    model_chunk = next(c for c in chunks if 'Welch RMS Standardizer' in c)
    point_value = tables['valid'][6][2][2]; sd_value=tables['valid'][5][2][1]
    probes = dict(point=html.replace(point_chunk,point_chunk.replace('>'+point_value+'<','>9.99<',1),1),
                  denominator=html.replace(model_chunk,model_chunk.replace('>'+sd_value+'<','>99.9<',1),1),
                  uncertainty=html.replace('no standardized confidence interval','standardized confidence interval supplied',1),
                  missing_plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name, changed in probes.items():
        require(changed!=html,'No-op corruption '+name)
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):continue
        raise ValueError('Accepted corrupted artifact '+name)
    report.update(scope='Local macOS arm64 native GUI artifacts; no other-platform/clinical qualification',
        R_tables_agree_at_display_precision=True,source_data_unchanged=True,
        equivalent_tables_and_plot_pixels_preserved=True,corruption_probes_rejected=list(probes),direct_PNG=png)
    (EXPORTS/'python-welch-0.3.69-artifacts-20261112.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()

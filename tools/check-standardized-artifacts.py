"""Check 0.3.68 GUI-saved raw/standardized results against independent R fixtures."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
spec=importlib.util.spec_from_file_location('estimation_artifacts',ROOT/'tools/check-estimation-artifacts.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
require,displayed,image_info=base.require,base.displayed,base.image_info
STD=json.loads((ROOT/'tests/fixtures/standardized-effects.json').read_text())['fixtures']
PROFILES={
 'defaults':(False,False,False,False),
 'valid':(True,True,True,False),
 'welch':(False,True,False,False),
 'off':(True,False,True,False),
 'incomplete':(True,True,True,True),
 'recovered':(True,True,True,False),
 'reopened':(True,True,True,False),
}


def inspect(html,mode,archive=None):
    independent_std,paired_std,student,paired_missing=PROFILES[mode]
    tables=base.module.Tables(html).tables
    require(len(tables)==10+3*int(independent_std)+3*int(paired_std),'Wrong native table count for '+mode)
    offset=0;plot_keys=[]
    for paired,enabled in ((False,independent_std),(True,paired_std)):
        fixture_name='paired_missing_alignment' if paired else 'hand_unequal_variance'
        case=next(f for f in base.FIXTURES if f['id']==fixture_name)
        method='paired_t' if paired else 'student' if student else 'welch'
        ref=next(r for r in case['expected']['runs'] if r['confidence']==.95 and r['method']==method)
        count=8 if enabled else 5
        group=tables[offset:offset+count]
        if paired and paired_missing:
            require(all(len(t)==3 and all(not cell.strip() for cell in t[2]) for t in group),
                    'Incomplete paired result retained computed rows or notes')
            offset+=count
            continue
        label='paired' if paired else 'independent'
        require(group[0][2]==(['13','5','8'] if paired else ['13','13','0']),'Wrong cohort')
        expected_missing=([['First measurement','FirstMeasurement','7'],['Second measurement','SecondMeasurement','6']]
            if paired else [['Outcome','Outcome','0'],['Group','IndependentGroup','0']])
        require(group[1][2:4]==expected_missing,'Wrong role missingness')
        names=['FirstMeasurement','SecondMeasurement'] if paired else ['First','Second']
        for row,key,role,name in zip(group[2][2:4],('first','second'),('First','Second'),names):
            require(row[:3]==[role,name,str(case['expected']['summaries'][key]['n'])],'Wrong descriptive role/N')
            for value,k in zip(row[3:],('mean','sd')):displayed(value,case['expected']['summaries'][key][k])
        row=group[3][2]
        require(row[:2]==names,'Wrong raw orientation')
        require(row[2]=={'paired_t':'Paired t-test','student':'Student pooled-variance t-test','welch':'Welch independent t-test'}[method], 'Wrong raw method')
        for value,k in zip(row[3:10],('difference','stderr','df','statistic','p','lower','upper')):displayed(value,ref[k])
        displayed(row[10],.95);require(row[11]=='ok','Wrong raw status')
        require('does not establish equivalence' in group[3][-1][0],'Missing raw interpretation boundary')
        indices=case['expected']['retained_indices'];rows=group[4][2:]
        require(len(rows)==len(indices),'Wrong source-row count')
        for row,i in zip(rows,indices):
            require(row[:2]==[str(i+1),base.SOURCE[i]['Subject']],'Changed source/subject identity')
            if paired:
                for value,key in zip(row[2:4],('FirstMeasurement','SecondMeasurement')):displayed(value,float(base.SOURCE[i][key]))
                displayed(row[4],float(base.SOURCE[i]['FirstMeasurement'])-float(base.SOURCE[i]['SecondMeasurement']))
            else:
                require(row[2]==base.SOURCE[i]['IndependentGroup'],'Changed group label')
                displayed(row[3],float(base.SOURCE[i]['Outcome']))
        plot_keys.append(label+'_raw')
        if enabled:
            target=next(f for f in STD if f['id']==fixture_name)
            sr=next(r for r in target['runs'] if r['confidence']==.95)
            model,cohen,g=group[5:8]
            require(model[2][0]==('Within-row difference SD' if paired else 'Sample-size-weighted pooled SD'),'Wrong standardizer')
            displayed(model[2][1],sr['standardizer_sd']);displayed(model[2][2],sr['df'])
            require(cohen[2][0]==('Cohen d_z' if paired else 'Cohen d'),'Wrong standardized estimand')
            for value,k in zip(cohen[2][1:4],('cohens_d','delta_lower','delta_upper')):displayed(value,sr[k])
            displayed(cohen[2][4],.95);require(cohen[2][5]=='ok','Wrong standardized status')
            require('Population delta_z' in cohen[-1][0] if paired else 'Population delta:' in cohen[-1][0], 'Missing population target')
            require('not raw-mean or J-scaled g intervals' in cohen[-1][0],'Missing interval distinction')
            require(g[1]==['Estimator','Point Estimate','Exact J(df)','Point Status'],'Unexpected g interval columns')
            require(g[2][0]==('Hedges g_z (point only)' if paired else 'Hedges g (point only)'),'Wrong g label')
            displayed(g[2][1],sr['hedges_g']);displayed(g[2][2],sr['correction'])
            require(g[2][3]=='point_available','Missing corrected point')
            require('No g-specific confidence interval' in g[-1][0],'Missing point-only disclosure')
            plot_keys.append(label+'_standardized')
        offset+=count
    if archive is None:
        paths=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)
        require(len(paths)==len(plot_keys),'Wrong embedded plot count')
        blobs=[base64.b64decode(re.sub(r'\s','',p),validate=True) for p in paths]
    else:
        paths=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        require(len(paths)==len(plot_keys),'Wrong cached plot count')
        blobs=[archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(plot_keys),'Stale unused cached plot')
    return dict(zip(plot_keys,[image_info(b) for b in blobs]))


def pixels(info):return info['dimensions'],info['pixel_sha256']


def check():
    report={};datasets=[];all_tables={}
    for mode in PROFILES:
        p=EXPORTS/f'python-standardized-0.3.68-{mode}.omv'
        with zipfile.ZipFile(p) as z:
            require(z.testzip() is None,'OMV CRC failed '+mode)
            html=z.read('index.html').decode();report[mode]=inspect(html,mode,z)
            all_tables[mode]=base.module.Tables(html).tables
            datasets.append({n:z.read(n) for n in ('data.bin','metadata.json','xdata.json')})
    for mode in ('recovered','reopened'):
        require(all_tables[mode]==all_tables['valid'],'Equivalent-input tables changed '+mode)
        require({k:pixels(v) for k,v in report[mode].items()}=={k:pixels(v) for k,v in report['valid'].items()},'Equivalent-input plot pixels changed')
    require(all_tables['welch'][:5]==all_tables['defaults'][:5],'Welch raw tables changed')
    require(all_tables['off'][:8]==all_tables['valid'][:8],'Unaffected independent results changed on paired off')
    require(all_tables['incomplete'][:8]==all_tables['valid'][:8],'Unaffected independent results changed on paired incomplete')
    require(pixels(report['welch']['independent_raw'])==pixels(report['defaults']['independent_raw']),'Welch raw image changed')
    for mode in ('off','incomplete'):
        for key in ('independent_raw','independent_standardized'):
            require(pixels(report[mode][key])==pixels(report['valid'][key]),'Unaffected independent image changed')
    require(all(d==datasets[0] for d in datasets),'Lifecycle changed dataset bytes/metadata')
    original=EXPORTS/'python-estimation-0.3.67-reopened.omv'
    with zipfile.ZipFile(original) as z:
        require(all(z.read(n)==datasets[0][n] for n in datasets[0]),'Compatibility reopening changed dataset')
    html=(EXPORTS/'python-standardized-0.3.68-reopened.html').read_text()
    report['HTML']=inspect(html,'reopened')
    require({k:pixels(v) for k,v in report['HTML'].items()}=={k:pixels(v) for k,v in report['valid'].items()},'HTML plot pixels changed')
    for name in ('independent','paired'):
        exported=image_info((EXPORTS/f'python-standardized-0.3.68-{name}-plot.png').read_bytes())
        source=image_info((EXPORTS/f'python-standardized-{name}-native-20261112.png').read_bytes())
        require(pixels(exported)==pixels(source),'Same-resolution source/export plot mismatch '+name)
        report[name+'_PNG']=exported
    probes=dict(cohort=html.replace('>13<','>12<',1),cohen=html.replace('>0.204<','>0.304<',1),
                hedges=html.replace('>0.189<','>0.289<',1),missing_plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed!=html,'No-op corruption probe '+name)
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):continue
        raise ValueError('Accepted corrupted artifact '+name)
    report.update(scope='Local GUI save/reopen/recalculation/export artifacts; no clinical/cross-platform qualification',
      independent_R_tables_agree_at_display_precision=True,compatibility_source_data_and_metadata_unchanged=True,
      equivalent_results_and_plot_pixels_preserved=True,Welch_and_off_clearing_verified=True,
      incomplete_paired_rows_notes_and_cached_images_cleared=True,corruption_probes_rejected=list(probes))
    (EXPORTS/'python-standardized-0.3.68-artifacts-20261112.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()

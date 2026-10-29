"""Read-only native HTML and OMV checks using source CSV and independent R p-values."""
import csv
import json
import math
import runpy
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT/'docs/validation-exports'
Tables = runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
saved_columns = runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
rounded_equal = runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']


def r_pvalues(exclude):
    script = '''
args <- commandArgs(TRUE)
d <- read.csv(args[1], stringsAsFactors=TRUE, na.strings=c("","NA"))
d <- d[if(args[2]=="true") complete.cases(d) else !is.na(d$Group),,drop=FALSE]
p <- c(Age=wilcox.test(Age~Group,data=d)$p.value)
for (name in c("Marker","Code")) {
    x <- d[[name]]; keep <- !is.na(x)
    t <- table(x[keep],droplevels(d$Group[keep]))
    t <- t[rowSums(t)>0,colSums(t)>0,drop=FALSE]
    test <- suppressWarnings(chisq.test(t,correct=FALSE))
    p[name] <- if(any(test$expected<5)) fisher.test(t)$p.value else test$p.value
}
cat(jsonlite::toJSON(as.list(p.adjust(p,"holm")),auto_unbox=TRUE,digits=17))
'''
    with tempfile.TemporaryDirectory(prefix='cpj-cross-oracle-') as directory:
        path = Path(directory)/'oracle.R';path.write_text(script)
        output = subprocess.run(['Rscript','--vanilla',str(path),
                    str(ROOT/'data/python_cross_table_examples.csv'),'true' if exclude else 'false'],
                    check=True,capture_output=True,text=True)
        return json.loads(output.stdout)


def check():
    with (ROOT/'data/python_cross_table_examples.csv').open() as handle:
        records = list(csv.DictReader(handle))
    evidence = {}
    typed,_,typed_columns = saved_columns('../../data/python_cross_table_examples.omv')
    typed_fields = {f['name']:f for f in typed['fields']}
    assert typed_fields['Age']['measureType']==typed_fields['Code']['measureType']=='Continuous'
    for label,exclude,display in [('available',False,'mean'),('complete',True,'median')]:
        cohort = [r for r in records if r['Group'] and (not exclude or all(r.values()))]
        parser = Tables();parser.feed((EXPORTS/f'python-cross-tables-0.3.42-{label}.html').read_text())
        numeric = next(t for t in parser.tables if len(t)>1 and 'Missing' in t[1] and 'Scope' in t[1])
        cats = next(t for t in parser.tables if len(t)>1 and 'Valid N' in t[1])
        tests = next(t for t in parser.tables if len(t)>1 and 'Adjusted p' in t[1])
        assert ('Mean' in numeric[1]) == (display=='mean')
        assert ('Median' in numeric[1]) == (display=='median')
        assert len(numeric[2:]) == 3
        for row in numeric[2:]:
            item = dict(zip(numeric[1],row))
            selected = [r for r in cohort if item['Scope']=='Overall' or r['Group']==item['Group']]
            values = [float(r[item['Variable']]) for r in selected if r[item['Variable']]]
            assert int(item['Valid']) == len(values)
            assert int(item['Missing']) == len(selected)-len(values)
            if display=='mean':
                rounded_equal(item['Mean'],statistics.mean(values))
                rounded_equal(item['SD'],statistics.stdev(values))
            else:
                q1,median,q3 = statistics.quantiles(values,n=4,method='inclusive')
                for name,value in [('Q1',q1),('Median',median),('Q3',q3)]:rounded_equal(item[name],value)
        for row in cats[2:]:
            item = dict(zip(cats[1],row));name=item['Variable']
            selected = [r for r in cohort if item['Scope']=='Overall' or r['Group']==item['Group']]
            valid = [r[name] for r in selected if r[name]]
            assert int(item['Valid N']) == len(valid)
            if item['Category']=='(Missing)':
                assert int(item['Count']) == len(selected)-len(valid)
                assert item['Valid (%)'] in ('','.');continue
            count = valid.count(item['Category']);assert int(item['Count']) == count
            rounded_equal(item['Valid (%)'].replace('%','').strip(),100*count/len(valid))
        oracle = r_pvalues(exclude)
        for row in tests[2:]:
            item = dict(zip(tests[1],row));value=oracle[item['Variable']]
            text = item['Adjusted p'].replace('\u2009','').replace(' ','')
            if text.startswith('<'):
                assert value < float(text[1:])
            else:rounded_equal(text,value)
        metadata,labels,columns = saved_columns(f'python-cross-tables-0.3.42-{label}.omv')
        assert metadata['rowCount']==25 and metadata['columnCount']==4
        assert columns == typed_columns
        for name in ('Group','Marker'):
            mapping={r[0]:r[1] for r in labels[name]['labels']}
            restored=['' if code==-2147483648 else mapping[code] for code in columns[name]]
            assert restored == [r[name] for r in records]
        for name in ('Age','Code'):
            for value,record in zip(columns[name],records):
                if record[name]:assert value==float(record[name])
                else:assert value==-2147483648 or math.isnan(value)
        evidence[label]=dict(retained=len(cohort),summary=display,numeric_strata=3,
                             categorical_rows=len(cats[2:]),adjustment='Holm',
                             adjusted_p='independent base-R tests at native display precision',
                             saved_input='all 25 source profiles and original row order retained')
    return dict(status='pass',states=evidence)


if __name__=='__main__':
    print(json.dumps(check(),indent=2))

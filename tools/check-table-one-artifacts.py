"""Read-only checks of native Table One HTML and saved source rows against CSV."""
import csv
import json
import math
import runpy
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT/'docs/validation-exports'
Tables = runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
saved_columns = runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
rounded_equal = runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']


def check():
    with (ROOT/'data/python_table_one_examples.csv').open() as handle:
        records = list(csv.DictReader(handle))
    typed, _, original = saved_columns('../../data/python_table_one_examples.omv')
    fields = {f['name']: f for f in typed['fields']}
    assert typed['rowCount'] == 25 and typed['columnCount'] == 5
    assert fields['Age']['measureType'] == fields['Code']['measureType'] == 'Continuous'
    evidence = {}
    for label, exclude in [('available', False), ('complete', True)]:
        cohort = [r for r in records if not exclude or all(r[v] for v in ('Group','Age','Marker','Code'))]
        path = EXPORTS/f'python-table-one-0.3.43-{label}.html'
        html = path.read_text()
        assert f"retained: {len(cohort)}" in html
        assert f"{len(cohort)} retained records" in html
        assert 'Omitted: all values missing' in html
        parser = Tables(); parser.feed(html)
        numeric = next(t for t in parser.tables if len(t)>1 and 'Valid' in t[1] and 'Variable' in t[1])
        cats = next(t for t in parser.tables if len(t)>1 and 'Counted Level' in t[1])
        assert ('Mean' in numeric[1]) == (not exclude)
        assert ('Median' in numeric[1]) == exclude
        assert len(numeric[2:]) == 2
        for row in numeric[2:]:
            item = dict(zip(numeric[1],row)); name = item['Variable']
            values = [float(r[name]) for r in cohort if r[name]]
            assert int(item['Valid']) == len(values)
            assert int(item['Missing']) == len(cohort)-len(values)
            rounded_equal(item['Missing (%)'].replace('%','').strip(),100*(len(cohort)-len(values))/len(cohort))
            if exclude:
                q1,median,q3 = statistics.quantiles(values,n=4,method='inclusive')
                for key,value in [('Q1',q1),('Median',median),('Q3',q3)]: rounded_equal(item[key],value)
            else:
                rounded_equal(item['Mean'],statistics.mean(values))
                rounded_equal(item['SD'],statistics.stdev(values))
        assert len(cats[2:]) == (4 if exclude else 2)
        for row in cats[2:]:
            item = dict(zip(cats[1],row)); name = item['Variable']
            valid = [r[name] for r in cohort if r[name]]
            count = valid.count(item['Counted Level'])
            assert int(item['Count']) == count
            assert int(item['Valid N']) == len(valid)
            assert int(item['Missing']) == len(cohort)-len(valid)
            rounded_equal(item['Valid (%)'].replace('%','').strip(),100*count/len(valid))
            rounded_equal(item['Missing (%)'].replace('%','').strip(),100*(len(cohort)-len(valid))/len(cohort))
            if not exclude: assert item['Counted Level'] == {'Group':'Intervention','Marker':'Positive'}[name]
        metadata, labels, columns = saved_columns(f'python-table-one-0.3.43-{label}.omv')
        assert metadata['rowCount'] == 25 and metadata['columnCount'] == 5
        assert columns == original
        for name in ('Group','Marker'):
            mapping = {r[0]:r[1] for r in labels[name]['labels']}
            assert ['' if v == -2147483648 else mapping[v] for v in columns[name]] == [r[name] for r in records]
        for name in ('Age','Code','NeverCollected'):
            for value, record in zip(columns[name],records):
                if record[name]: assert value == float(record[name])
                else: assert value == -2147483648 or math.isnan(value)
        evidence[label] = dict(retained=len(cohort),excluded=25-len(cohort),omitted=1,
            numeric_variables=2,categorical_rows=len(cats[2:]),
            oracle='CSV counts and Python statistics, native display precision',
            saved_input='all 25 source rows, original order, explicit continuous Age/Code')
    return dict(status='pass',states=evidence)


if __name__ == '__main__':
    print(json.dumps(check(),indent=2))

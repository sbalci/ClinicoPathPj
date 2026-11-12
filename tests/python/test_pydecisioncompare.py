"""Native paired-test adapter versus frozen R fixtures; source-row and option contracts."""
import ast
import json
import sys
import unittest

from cpjtest import ROOT, run_analysis
sys.path.insert(0, str(ROOT/'inst/python'))
import cpj_runtime

FIXTURES = json.loads((ROOT/'tests/fixtures/paired-decision.json').read_text())['fixtures']


def request(fixture=None, **overrides):
    f = fixture or FIXTURES[0]
    vector = lambda x: x if isinstance(x, list) else [x]
    encode = lambda x: dict(kind='factor', codes=[None if v < 0 else v for v in vector(x)], levels=f['levels'])
    columns = {'Reference': encode(f['reference'])}
    options = dict(gold='Reference', goldPositive=f['positive'], goldNegative=f['negative'],
        referenceType='disease', statComp=True, ci=True, plot=True, showCases=True, showPairCounts=True,
        excludeIndeterminate=f['exclude'])
    for i, (name, values) in enumerate(f['tests'].items(), 1):
        columns[name] = encode(values)
        options[f'test{i}'] = name
        options[f'test{i}Positive'] = f['positive']
        options[f'test{i}Negative'] = f['negative']
    options.update(overrides)
    return dict(analysis='pydecisioncompare', columns=columns, options=options,
                row_ids=[str(10+i*3) for i in range(len(vector(f['reference'])))])


def run(fixture=None, **overrides):
    result = cpj_runtime.execute(request(fixture, **overrides))
    json.dumps(result, allow_nan=False)
    return result


class PairedDecisionAdapter(unittest.TestCase):
    def test_public_defaults_and_omissions_match_frozen_contract(self):
        source = ROOT/'inst/python/analyses/meddecide/pydecisioncompare.py'
        spec = ast.literal_eval(next(n.value for n in ast.parse(source.read_text()).body
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SPEC' for t in n.targets)))
        options = {o['name']: o for o in spec['options']}
        frozen = json.loads((ROOT/'docs/baselines/released-2026-10-25.json').read_text())['decisioncompare']['definitions']['a']['options']
        baseline = {o['name']: o for o in frozen}
        for name in ('referenceType', 'mcnemarMethod', 'ci', 'plot', 'statComp', 'excludeIndeterminate'):
            self.assertEqual(options[name]['default'], baseline[name]['default'])
        self.assertEqual([x['name'] for x in options['mcnemarMethod']['options']], ['midp', 'asymptotic'])
        self.assertNotIn('difference_intervals', options)
        comparisons = next(x for x in spec['results'] if x['name'] == 'comparisons')
        self.assertFalse(any(x['name'] in ('lower', 'upper') for x in comparisons['columns']))

    def test_all_independent_R_fixtures_and_methods(self):
        for f in FIXTURES:
            for ref in f['expected']['runs']:
                if ref['method'] == 'exact': continue
                result = run(f, confLevel=ref['confidence'], mcnemarMethod=ref['method'])
                self.assertEqual(result['status'], 'ok', (f['id'], result.get('error')))
                cohort = result['tables']['cohort']['rows'][0]
                self.assertEqual(cohort['retained'], f['expected']['n_complete'])
                self.assertEqual(cohort['missing'], f['expected']['excluded_missing'])
                self.assertEqual(cohort['outside'], f['expected']['excluded_indeterminate'])
                for row, (name, model) in zip(result['tables']['counts']['rows'], ref['models'].items()):
                    self.assertEqual(row['test'], name)
                    self.assertEqual([row[k] for k in ('pp', 'np', 'pn', 'nn')], model['counts'])
                for row, expected in zip(result['tables']['estimates']['rows'],
                                          [p for m in ref['models'].values() for p in m['proportions']]):
                    for key in ('estimate', 'lower', 'upper'):
                        if expected[key] is None: self.assertIsNone(row[key])
                        else: self.assertAlmostEqual(row[key], expected[key], places=11)
                rows = result['tables']['comparisons']['rows']
                self.assertEqual(len(rows), len(ref['pairs'])*3)
                for row, (metric, expected) in zip(rows,
                        [(metric, pair[metric]) for pair in ref['pairs'] for metric in ('accuracy', 'sensitivity', 'specificity')]):
                    self.assertEqual(row['n'], expected['n'])
                    for key in ('difference', 'p'):
                        if expected[key] is None: self.assertIsNone(row[key])
                        else: self.assertAlmostEqual(row[key], expected[key], places=12)
                    target = expected.get('p_holm') if metric == 'accuracy' else None
                    if target is None: self.assertIsNone(row['adjusted'])
                    else: self.assertAlmostEqual(row['adjusted'], target, places=12)
                    self.assertNotIn('lower', row); self.assertNotIn('upper', row)
                expected_indices = f['expected']['retained_indices']
                expected_indices = expected_indices if isinstance(expected_indices, list) else [expected_indices]
                self.assertEqual([r['sourceID'] for r in result['tables']['cases']['rows']],
                                 [str(10+i*3) for i in expected_indices])

    def test_subprocess_contract_and_static_plot(self):
        req = request()
        result = run_analysis('pydecisioncompare', req['columns'], req['options'], row_ids=req['row_ids'])
        self.assertEqual(result['status'], 'ok', result.get('error'))
        plot = result['plots']['proportionPlot']['columns']
        rows = result['tables']['estimates']['rows']
        selected = [r for i, r in enumerate(rows) if i % 5 in (0, 1, 4) and r['estimate'] is not None]
        self.assertEqual(plot['estimate'], [r['estimate'] for r in selected])
        self.assertEqual(plot['lower'], [r['lower'] for r in selected])
        self.assertIn('common', result['texts']['summary'])

    def test_disabled_outputs_and_point_only_plot(self):
        result = run(statComp=False, ci=False, plot=False, showCases=False)
        self.assertFalse(result['plots'])
        for name in ('comparisons', 'discordance', 'cases'):
            self.assertNotIn(name, result['tables'])
        self.assertTrue(all(r['lower'] is None and r['upper'] is None for r in result['tables']['estimates']['rows']))
        result = run(ci=False)
        self.assertTrue(all(v is None for v in result['plots']['proportionPlot']['columns']['lower']))

    def test_comparator_wording_retains_numerical_results(self):
        original = run()
        for mode in ('consensus', 'method'):
            result = run(referenceType=mode)
            self.assertEqual(result['tables']['counts'], original['tables']['counts'])
            self.assertEqual([r['estimate'] for r in result['tables']['estimates']['rows']],
                             [r['estimate'] for r in original['tables']['estimates']['rows']])
            labels = [r['metric'] for r in result['tables']['estimates']['rows']]
            self.assertFalse(any('predictive value' in x.lower() or x == 'Sensitivity' for x in labels))
            self.assertIn('does not establish disease', result['texts']['summary'])
        unspecified = run(referenceType='legacy')
        self.assertTrue(any('not specified' in x['text'] for x in unspecified['notices']))

    def test_invalid_roles_levels_and_public_method(self):
        for options, message in [({'test2': 'A'}, 'distinct'), ({'test1': 'Reference'}, 'distinct'),
                                  ({'goldNegative': 'Positive'}, 'distinct'),
                                  ({'test3Negative': None}, 'explicit'),
                                  ({'mcnemarMethod': 'exact'}, 'public core'),
                                  ({'referenceType': 'unknown'}, 'interpretation')]:
            result = run(**options)
            self.assertEqual(result['status'], 'input_error')
            self.assertIn(message, result['error']['message'])

    def test_source_intervals_cannot_be_enabled_by_extra_option(self):
        original = run()
        changed = run(difference_intervals=True)
        self.assertEqual(original['tables'], changed['tables'])
        self.assertEqual(original['plots'], changed['plots'])
        self.assertIn('omits paired-difference intervals', changed['texts']['summary'].replace('\\', ''))

    def test_optional_third_test_uses_common_cohort(self):
        f = next(x for x in FIXTURES if x['id'] == 'different_missingness')
        req = request(f)
        req['columns']['C'] = dict(req['columns']['A'])
        req['columns']['C']['codes'] = list(req['columns']['A']['codes'])
        req['columns']['C']['codes'][0] = None
        req['options'].update(test3='C', test3Positive=f['positive'], test3Negative=f['negative'])
        added = cpj_runtime.execute(req)
        self.assertEqual(added['tables']['cohort']['rows'][0]['retained'], run(f)['tables']['cohort']['rows'][0]['retained']-1)
        self.assertEqual(len(added['tables']['comparisons']['rows']), 9)


if __name__ == '__main__': unittest.main()

import sys
import unittest
from datetime import datetime,timezone
import numpy as np
from cpjtest import ROOT, factor, number, text, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_datetime import parse_value,components,calculate,ORDERS
from cpj_runtime import _decode,InputError,Factor


class DateTimes(unittest.TestCase):
    def test_manual_date_orders_and_leap_calendar(self):
        for fmt,value in [('ymd','2024-02-29'),('dmy','29/02/2024'),('mdy','02/29/2024'),
                          ('ydm','2024-29-02'),('myd','02-2024-29'),('dym','29-2024-02')]:
            self.assertEqual(parse_value(value,fmt),datetime(2024,2,29,tzinfo=timezone.utc))
        for value in ['2023-02-29','1900-02-29','2024-04-31','2024-13-01','0000-01-01',
                      '24-02-29','01-02-03','2024-02/29','2024-02-29 garbage']:
            with self.assertRaises(ValueError):parse_value(value,'ymd')
        self.assertEqual(parse_value('2000-02-29','ymd').day,29)
        self.assertEqual(parse_value('0001-01-01','ymd').year,1)
        self.assertEqual(parse_value('9999-12-31','ymd').year,9999)

    def test_explicit_day_month_orientation_and_times(self):
        self.assertEqual(parse_value('01/02/2024','dmy').month,2)
        self.assertEqual(parse_value('01/02/2024','mdy').month,1)
        for fmt,value in [('ymdhms','2024-02-29T23:59:58.125Z'),('dmyhms','29/02/2024 23:59:58.125'),('mdyhms','02/29/2024 23:59:58.125')]:
            self.assertEqual(components(parse_value(value,fmt))['second'],58.125)
        for fmt,value in [('ymdhm','2024-02-29 23:59'),('dmyhm','29-02-2024 23:59'),('mdyhm','02-29-2024 23:59')]:
            self.assertEqual(parse_value(value,fmt).second,0)
        for value in ['2024-02-29 24:00:00','2024-02-29 23:59:60','2024-02-29T12:00:00+03:00','2024-02-29 12:00:00.1234567']:
            with self.assertRaises(ValueError):parse_value(value,'ymdhms')

    def test_excel_origins_and_all_minutes_without_float_drift(self):
        self.assertEqual(parse_value(0,'excel_serial').isoformat(),'1899-12-30T00:00:00+00:00')
        self.assertEqual(parse_value(60,'excel_serial').isoformat(),'1900-02-28T00:00:00+00:00')
        self.assertEqual(parse_value(61,'excel_serial').isoformat(),'1900-03-01T00:00:00+00:00')
        self.assertEqual((parse_value(0,'excel_serial_1904')-parse_value(0,'excel_serial')).days,1462)
        for minute in range(1440):
            value=45000+minute/1440
            got=parse_value(value,'excel_serial')
            self.assertEqual((got.hour,got.minute,got.second),(minute//60,minute%60,0))
        for seconds in [.5,1.5,2.5,-.5,-1.5]:
            got=parse_value(seconds/86400,'excel_serial')
            self.assertEqual((got-parse_value(0,'excel_serial')).total_seconds(),float(np.rint(seconds)))

    def test_unix_epoch_negative_fractional_and_numeric_range(self):
        for value,iso in [(0,'1970-01-01T00:00:00+00:00'),(-.25,'1969-12-31T23:59:59.750000+00:00'),(1.125,'1970-01-01T00:00:01.125000+00:00')]:
            self.assertEqual(parse_value(value,'unix_epoch').isoformat(),iso)
        for fmt in ('unix_epoch','excel_serial','excel_serial_1904'):
            for value in ['not numeric',float('inf'),float('nan'),1e100,True]:
                with self.assertRaises(ValueError):parse_value(value,fmt)

    def test_components_january_blocks_and_fixed_names(self):
        r=components(parse_value('2021-01-01','ymd'))
        self.assertEqual((r['dayname'],r['weeknum'],r['dayofyear'],r['quarter']),('Friday',1,1,1))
        self.assertEqual(components(parse_value('2020-12-31','ymd'))['weeknum'],53)
        self.assertEqual(components(parse_value('2024-12-31','ymd'))['dayofyear'],366)
        self.assertEqual(components(parse_value('2024-04-01','ymd'))['quarter'],2)
        self.assertTrue(all(v is None for v in components(None).values()))

    def test_missing_invalid_blank_and_literal_na_are_distinct(self):
        d=_decode({'x':factor(['2024-02-29','2023-02-29',None,'','NA','Unknown','2024-03-01'])})
        r=calculate(d,dict(datetime_var='x'))
        self.assertEqual((r['parsed'],r['invalid'],r['missing'],r['success']),(2,3,2,.4))
        self.assertEqual([v['status'] for v in r['rows']],['Parsed','Invalid','Missing','Missing','Invalid','Invalid','Parsed'])
        d={'x':Factor(np.array([0,1,2,-1]),['2024-02-29',None,'NA'])}
        r=calculate(d,dict(datetime_var='x'))
        self.assertEqual((r['parsed'],r['invalid'],r['missing']),(1,1,2))

    def test_empty_all_invalid_all_missing_and_metadata(self):
        r=calculate(_decode({'x':text([None,' '])}),dict(datetime_var='x'))
        self.assertIsNone(r['success']);self.assertIsNone(r['minimum'])
        self.assertEqual(calculate(_decode({'x':text(['bad','NA'])}),dict(datetime_var='x'))['success'],0)
        for columns,options in [({'x':text([])},{}),({'x':number([1,2])},{}),({'x':text(['2024-01-01'])},{'timezone':'system'}),({'x':text(['2024-01-01'])},{'datetime_format':'auto'}),({'x':text(['2024-01-01'])},{'preview_rows':10.5})]:
            with self.assertRaises(InputError):calculate(_decode(columns),dict(datetime_var='x',**options))
        d=_decode({'x':number([0,1])});d.metadata['x']={'classes':['Date']}
        with self.assertRaisesRegex(InputError,'native Date/POSIX'):calculate(d,dict(datetime_var='x',datetime_format='unix_epoch'))

    def test_runtime_outputs_keep_sparse_source_ids_and_failed_rows(self):
        columns={'x':factor(['2024-02-29','2023-02-29',None,'2021-01-01'])}
        r=run_analysis('pydatetimeconverter',columns,dict(datetime_var='x',extract_year=True,extract_weeknum=True,show_quality_metrics=True,show_summary=True),row_ids=['2','5','9','20'])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['corrected_datetime_numeric']['title'],'Unix epoch seconds (UTC)')
        self.assertEqual(r['outputs']['year_out']['title'],'Year (UTC)')
        self.assertTrue(all(v.get('title','').strip() for v in r['outputs'].values()))
        epoch=r['outputs']['corrected_datetime_numeric']
        self.assertEqual(epoch['row_ids'],['2','5','9','20'])
        self.assertEqual(epoch['values'],[1709164800.,None,None,1609459200.])
        self.assertEqual(r['outputs']['year_out']['values'],[2024,None,None,2021])
        self.assertEqual(r['outputs']['weeknum_out']['values'],[9,None,None,1])
        self.assertEqual([v['source'] for v in r['tables']['preview']['rows']],['2','5','9','20'])
        self.assertEqual(r['tables']['quality']['rows'][0]['invalid'],1)
        self.assertEqual(r['outputs']['dayname_out']['levels'][4],'Friday')
        self.assertIn('2 of 4 supplied records',r['texts']['report'])

    def test_all_invalid_saved_labels_are_missing_and_preview_is_bounded(self):
        r=run_analysis('pydatetimeconverter',{'x':text(['bad']*30)},dict(datetime_var='x',preview_rows=10),row_ids=[str(i+1) for i in range(30)])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(len(r['tables']['preview']['rows']),10)
        self.assertEqual(r['outputs']['corrected_datetime_char']['values'],[None]*30)
        self.assertEqual(r['outputs']['corrected_datetime_numeric']['values'],[None]*30)
        self.assertNotIn('quality',r['tables'])
        self.assertTrue(any('first 10 source' in v['text'] for v in r['notices']))


if __name__=='__main__':unittest.main()

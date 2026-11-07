"""Explicit encodings: no epoch/century inference and aligned interval output."""
import sys,unittest
from datetime import datetime,date,timedelta,timezone
import numpy as np
from cpjtest import ROOT,number,text,factor,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_datetime import parse_value,calculate as convert
from cpj_intervals import calculate
from cpj_runtime import _decode,InputError


class NumericDates(unittest.TestCase):
    def test_packed_integer_float_text_and_calendar_validation(self):
        for v in [20240229,20240229.,np.int64(20240229),'20240229',' 20240229 ']:
            self.assertEqual(parse_value(v,'packed_ymd'),datetime(2024,2,29,tzinfo=timezone.utc))
        for d in [date(1,1,1),date(999,12,31),date(1000,1,1),date(1900,2,28),date(2000,2,29),date(9999,12,31)]:
            packed=f'{d.year:04d}{d.month:02d}{d.day:02d}'
            self.assertEqual(parse_value(packed,'packed_ymd').date(),d)
        for v in [True,np.bool_(False),20230229,19000229,20241301,20240431,20240001,
                  240229,10101,20240229.5,'20240229.0','2.0240229e7','2024-02-29',
                  '00000101','２０２４０２２９',None,float('inf'),float('nan'),10**400]:
            with self.subTest(v=str(v)[:30]):
                with self.assertRaises(ValueError):parse_value(v,'packed_ymd')

    def test_many_packed_dates_and_adjacent_days(self):
        for i in range(450):
            d=date(1899,12,1)+timedelta(days=i*91)
            v=d.year*10000+d.month*100+d.day
            self.assertEqual(parse_value(v,'packed_ymd').date(),d)

    def test_packed_converter_quality_missingness_and_saved_components(self):
        r=run_analysis('pydatetimeconverter',{'x':number([20240229,20230229,None,20000229])},
                       dict(datetime_var='x',datetime_format='packed_ymd',extract_year=True,show_quality_metrics=True),row_ids=['2','5','9','20'])
        self.assertEqual(r['status'],'ok',r.get('error'))
        q=r['tables']['quality']['rows'][0]
        self.assertEqual((q['parsed'],q['invalid'],q['missing']),(2,1,1))
        self.assertEqual(r['outputs']['year_out']['values'],[2024,None,None,2000])
        self.assertEqual(r['outputs']['year_out']['row_ids'],['2','5','9','20'])
        self.assertEqual(r['outputs']['corrected_datetime_numeric']['values'],[1709164800.,None,None,951782400.])
        r=convert(_decode({'x':factor(['20240229',None,'NA',''])}),dict(datetime_var='x',datetime_format='packed_ymd'))
        self.assertEqual((r['parsed'],r['invalid'],r['missing']),(1,1,2))

    def test_all_explicit_numeric_interval_formats_and_basis(self):
        cases=[('packed_ymd',[20240131,20230131],[20240229,20230228]),
               ('excel_serial',[45322,44957],[45351,44985]),
               ('excel_serial_1904',[43860,43495],[43889,43523]),
               ('unix_epoch',[1706659200,1675123200],[1709164800,1677542400])]
        for fmt,a,b in cases:
            d=_decode({'a':number(a+[None]),'b':number(b+[b[0]])})
            for basis in ['standardized','calendar']:
                r=calculate(d,dict(dx_date='a',fu_date='b',time_format=fmt,time_basis=basis))
                want=[1,1,None] if basis=='calendar' else [29/30.4375,28/30.4375,None]
                self.assertEqual(r['values'],want,(fmt,basis))
            r=run_analysis('pytimeinterval',{'a':number(a+[None]),'b':number(b+[b[0]])},
                           dict(dx_date='a',fu_date='b',time_format=fmt,time_basis='calendar'),row_ids=['2','7','19'])
            self.assertEqual(r['status'],'ok',r.get('error'))
            self.assertEqual(r['outputs']['calculated_time']['values'],[1,1,None])
            self.assertIn(f'Format: {fmt}',r['outputs']['calculated_time']['description'])
            self.assertEqual(r['outputs']['calculated_time']['row_ids'],['2','7','19'])

    def test_fractional_epochs_rounding_early_excel_and_negative_policy(self):
        for fmt in ['excel_serial','excel_serial_1904']:
            r=calculate(_decode({'a':number([45000]),'b':number([45000+5/1440])}),
                        dict(dx_date='a',fu_date='b',time_format=fmt,output_unit='days'))
            self.assertAlmostEqual(r['values'][0],300/86400)
        r=calculate(_decode({'a':number([0]),'b':number([.125])}),
                    dict(dx_date='a',fu_date='b',time_format='unix_epoch',output_unit='days'))
        self.assertEqual(r['values'],[.125/86400])
        r=calculate(_decode({'a':number([60]),'b':number([61])}),
                    dict(dx_date='a',fu_date='b',time_format='excel_serial',output_unit='days'))
        self.assertEqual(r['values'],[1]);self.assertTrue(any('early Excel' in w for w in r['warnings']))
        with self.assertRaisesRegex(InputError,'Negative intervals'):
            calculate(_decode({'a':number([20240229]),'b':number([20240131])}),dict(dx_date='a',fu_date='b',time_format='packed_ymd'))

    def test_packed_parse_guard_and_no_automatic_date_or_century_guessing(self):
        r=calculate(_decode({'a':number([20240101]*5),'b':number([20240201]*4+[20240230])}),
                    dict(dx_date='a',fu_date='b',time_format='packed_ymd'))
        self.assertEqual((r['complete'],r['invalid']),(4,1))
        for fmt,a,b in [('packed_ymd',[240101],[240201]),('ymd',[20240101],[20240201]),('auto',[20240101],[20240201])]:
            with self.assertRaises(InputError):calculate(_decode({'a':number(a),'b':number(b)}),dict(dx_date='a',fu_date='b',time_format=fmt))
        # Source formats stay explicit; numeric-looking text is not interpreted as YMD.
        with self.assertRaises(ValueError):parse_value('20240229','ymd')

if __name__=='__main__':unittest.main()

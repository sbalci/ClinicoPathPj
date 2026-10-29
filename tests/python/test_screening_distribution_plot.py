"""Geometry and validation for aggregated screening distributions."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'inst/python'))
from cpj_plots import figure,render


def state(k=1):
    rows=[dict(variable=f'Marker {i+1}',percentile=p,value=p*(i+1),lower=-10.,upper=80.*(i+1)) for i in range(k) for p in range(101)]
    return dict(kind='screeningquantiles',columns={key:[r[key] for r in rows] for key in rows[0]})


class ScreeningDistributions(unittest.TestCase):
    def test_geometry_and_theme_one_to_twenty_variables(self):
        for k in [1,2,6,7,20]:
            f=figure(state(k),width=1000,height=800,background='#222222',foreground='white')
            panels=[a for a in f.axes if a.get_visible()]
            self.assertEqual(len(panels),k)
            for i,a in enumerate(panels):
                np.testing.assert_array_equal(a.lines[0].get_xdata(),np.arange(101))
                np.testing.assert_array_equal(a.lines[0].get_ydata(),np.arange(101)*(i+1))
                self.assertEqual(list(a.lines[1].get_ydata()),[-10.,-10.])
                self.assertEqual(list(a.lines[2].get_ydata()),[80.*(i+1)]*2)
                self.assertEqual(a.get_facecolor(),(34/255,34/255,34/255,1))
            f.clear()

    def test_constant_curve_and_coincident_limits(self):
        s=state();s['columns']['value']=[1.]*101;s['columns']['lower']=[1.]*101;s['columns']['upper']=[1.]*101
        f=figure(s);self.assertEqual(len(f.axes[0].lines),2);f.clear()
        self.assertIn('png',render(s,width=1000,height=800))

    def test_invalid_state_rejected(self):
        for key,value in [('percentile',2),('value',np.nan),('lower',-9),('upper',-20)]:
            s=state();s['columns'][key][1]=value
            with self.assertRaises(ValueError):figure(s)
        with self.assertRaises(ValueError):figure(state(21))
        s=state();s['columns']['value'][20]=-1
        with self.assertRaises(ValueError):figure(s)

"""Plot geometry and native raster checks independent of the R display bridge."""
import base64
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_plots import figure, render


def state(kind,**columns): return dict(kind=kind,columns=columns,xlab='x',ylab='y')

class Plots(unittest.TestCase):
    def test_interval_duplicate_labels_and_missing_limits(self):
        s=state('interval',label=['A','A','B'],estimate=[1,2,3],lower=[0,None,2],upper=[2,None,4])
        s['reference']=0
        f=figure(s);ax=f.axes[0]
        self.assertEqual([t.get_text() for t in ax.get_yticklabels()],['A','A','B'])
        self.assertTrue(ax.yaxis_inverted())
        self.assertEqual([list(l.get_ydata()) for l in ax.lines[1:]],[[0],[1],[2]])
        self.assertEqual(len(ax.collections),2)
        f.clear()

    def test_singleton_missing_group_and_sorted_steps(self):
        s=state('line',x=[2,1,3],y=[.8,1,.2],group=['a','a',None]);s['step']=True
        f=figure(s);a,b=f.axes[0].lines
        self.assertEqual(list(a.get_xdata()),[1,2]);self.assertEqual(a.get_drawstyle(),'steps-post')
        self.assertEqual(b.get_marker(),'o');self.assertEqual(list(b.get_ydata()),[.2]);f.clear()

    def test_seeded_box_jitter_is_identical_and_does_not_change_global_rng(self):
        s=state('box',group=['a']*4+['b']*4,value=[1,2,3,4,2,3,4,5]);s['reference']=2
        f,g=figure(s),figure(s)
        for a,b in zip(f.axes[0].collections,g.axes[0].collections):np.testing.assert_array_equal(a.get_offsets(),b.get_offsets())
        self.assertEqual(list(f.axes[0].lines[0].get_ydata()),[2,2]);f.clear();g.clear()

    def test_grouped_bars_preserve_counts(self):
        f=figure(state('bar',label=['A','A','B','B'],value=[2,3,4,5],group=['obs','exp','obs','exp']))
        self.assertEqual([p.get_height() for p in f.axes[0].patches],[2,4,3,5]);f.clear()

    def test_png_dimensions_and_labels_treated_as_literal_text(self):
        import struct
        s=state('line',x=[1,2],y=[1,2],group=['$unsafe{label}$']*2)
        payload=render(s,width=500,height=300,background='#222222',foreground='white')
        raw=base64.b64decode(payload['png'])
        self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II',raw[16:24]),(500,300))
        with self.assertRaises(ValueError):render(s,width=5000)

    def test_histogram_panels_keep_separate_variable_scales_and_counts(self):
        s=state('histogram',group=['Age','Age','Marker','Marker'],lower=[10,20,.1,.2],upper=[20,30,.2,.3],count=[3,7,8,2])
        f=figure(s)
        self.assertEqual([a.get_title() for a in f.axes],['Age','Marker'])
        self.assertEqual([sum(p.get_height() for p in a.patches) for a in f.axes],[10,10])
        self.assertLess(f.axes[1].get_xlim()[1],1)
        self.assertGreater(f.axes[0].get_xlim()[0],1)
        f.clear()

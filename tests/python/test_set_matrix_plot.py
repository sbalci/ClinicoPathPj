"""Independent membership-dot and bar geometry fixtures for the bounded set matrix."""
import json,itertools,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'inst/python'))
from cpj_plots import figure,render


def state(patterns,counts,names):
    return dict(kind='setmatrix',columns=dict(pattern=patterns,count=counts,sets=[json.dumps(names)]*len(patterns)))


class SetMatrixPlot(unittest.TestCase):
    def test_geometry_two_to_four_sets(self):
        for k in range(2,5):
            patterns=[''.join(p) for p in itertools.product('01',repeat=k)]
            counts=list(range(len(patterns)));s=state(patterns,counts,[f'Marker {i+1}' for i in range(k)])
            f=figure(s,width=900,height=600,background='#222222',foreground='white')
            top,matrix=f.axes
            self.assertEqual([p.get_height() for p in top.patches],counts)
            self.assertEqual([t.get_text() for t in matrix.get_xticklabels()],patterns)
            # Background dots exist even for none; active dots encode each signature independently.
            active=[(i,j) for i,p in enumerate(patterns) for j in range(k) if p[j]=='1']
            got=[]
            for collection in matrix.collections:
                if collection.get_alpha() is None:
                    got.extend(tuple(map(int,v)) for v in collection.get_offsets())
            self.assertEqual(got,active)
            self.assertEqual(len(matrix.lines),len(patterns)-1)
            self.assertEqual(top.get_facecolor(),(34/255,34/255,34/255,1))
            f.clear()

    def test_none_only_and_long_literal_labels(self):
        f=figure(state(['00'],[5],['<unsafe>_'*8,'B']))
        self.assertEqual([p.get_height() for p in f.axes[0].patches],[5])
        self.assertEqual(len(f.axes[1].lines),0)
        self.assertIn('shortened',f.axes[0].get_title())
        f.clear()

    def test_invalid_geometry_rejected(self):
        for s in [state([],[],['A','B']),state(['00','00'],[1,2],['A','B']),
                  state(['02'],[1],['A','B']),state(['000'],[1],['A','B']),
                  state(['00'],[-1],['A','B']),state(['00'],[.5],['A','B']),
                  state(['00'],[1],['A','A']),state(['00'],[1],['A']),
                  state(['00']*17,[1]*17,['A','B'])]:
            with self.assertRaises(ValueError):figure(s)

    def test_raster_export(self):
        image=render(state(['00','11'],[0,3],['A','B']),width=900,height=600)
        self.assertIn('png',image)

"""Static plot construction in Python. No data access or statistical model refitting."""
import base64
import io
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_PALETTE = ['#3E6D9C', '#CD653D', '#658B55', '#A96DA3', '#C6A143']
_CACHE = None


def figure(state, width=600, height=400, palette=None, background='white', foreground='#222222'):
    global _CACHE
    vendor = Path(__file__).resolve().parent / '_vendor'
    if vendor.is_dir() and str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))
    # Cache lives only for this isolated rendering process; no writes into the module/user home.
    if 'MPLCONFIGDIR' not in os.environ:
        _CACHE = tempfile.TemporaryDirectory(prefix='cpj-mpl-')
        os.environ['MPLCONFIGDIR'] = _CACHE.name
        seed = Path(__file__).with_name('font-cache.json')
        if seed.is_file():
            data = json.loads(seed.read_text())
            # Matplotlib resolves these relative names against its installed data directory.
            if any(Path(e['fname']).is_absolute() or '..' in Path(e['fname']).parts
                   for kind in ('afmlist','ttflist') for e in data[kind]):
                raise ValueError('Bundled font cache must contain only relative bundled fonts')
            (Path(_CACHE.name)/f"fontlist-v{data['_version']}.json").write_text(json.dumps(data))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import numpy as np
    if not isinstance(width, int) or not isinstance(height, int) or not (200 <= width <= 2000 and 200 <= height <= 2000):
        raise ValueError('Plot dimensions must be integers between 200 and 2000 pixels')
    matplotlib.rcParams.update({'text.usetex': False, 'text.parse_math': False,
                                'font.family': 'DejaVu Sans', 'font.size': 10})
    fig = Figure(figsize=(width/100, height/100), dpi=100, facecolor=background, layout='constrained')
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.set_facecolor(background)
    ax.tick_params(colors=foreground)
    for spine in ax.spines.values(): spine.set_color(foreground)
    ax.xaxis.label.set_color(foreground); ax.yaxis.label.set_color(foreground)
    palette = palette or DEFAULT_PALETTE
    columns = state['columns']; kind = state['kind']
    n = len(next(iter(columns.values()), []))
    if n > {'interval':200, 'line':20000, 'box':20000, 'bar':2000, 'scatter':5000, 'histogram':2000}.get(kind, 0):
        raise ValueError('Unsupported plot kind or excessive plot rows')
    if any(len(c) != n for c in columns.values()): raise ValueError('Plot columns have unequal lengths')
    if kind == 'histogram':
        groups = list(dict.fromkeys(columns['group']))
        if not groups or len(groups)>12: raise ValueError('Histograms support one to twelve panels')
        fig.delaxes(ax)
        axes=fig.subplots(int(np.ceil(len(groups)/2)),min(2,len(groups)),squeeze=False).flat
        for i, panel in enumerate(axes):
            if i>=len(groups):panel.set_visible(False);continue
            indices=[j for j,g in enumerate(columns['group']) if g==groups[i]]
            lower=np.array([columns['lower'][j] for j in indices])
            upper=np.array([columns['upper'][j] for j in indices])
            count=np.array([columns['count'][j] for j in indices])
            if np.any(upper<=lower) or np.any(count<0):raise ValueError('Invalid histogram bins or counts')
            panel.set_facecolor(background);panel.tick_params(colors=foreground)
            for spine in panel.spines.values():spine.set_color(foreground)
            panel.bar(lower,count,width=upper-lower,align='edge',color=palette[i%len(palette)],edgecolor=background)
            panel.set_title(groups[i],color=foreground)
            panel.set_xlabel(state.get('xlab',''),color=foreground)
            panel.set_ylabel(state.get('ylab',''),color=foreground)
        return fig
    reference = state.get('reference')
    if reference is not None:
        (ax.axvline if kind in ('interval','scatter') else ax.axhline)(reference, color=foreground, alpha=.5, linestyle='--')
    if kind == 'interval':
        y = np.arange(n)
        for i in range(n):
            estimate = columns['estimate'][i]
            if estimate is None: continue
            lo, hi = columns['lower'][i], columns['upper'][i]
            if lo is not None and hi is not None:
                ax.hlines(i, lo, hi, color=palette[0], linewidth=2)
            ax.plot([estimate], [i], 'o', color=palette[0])
        ax.set_yticks(y, columns['label']); ax.invert_yaxis()
    elif kind == 'line':
        group = columns.get('group', [None]*n)
        keys = list(dict.fromkeys(group))
        for i, key in enumerate(keys):
            points = [(columns['x'][j], columns['y'][j]) for j in range(n) if group[j] == key]
            points.sort(key=lambda p: float('inf') if p[0] is None else p[0])
            x = [np.nan if p[0] is None else p[0] for p in points]
            y = [np.nan if p[1] is None else p[1] for p in points]
            ax.plot(x, y, color=palette[i % len(palette)], marker='o' if len(points)==1 else None,
                    drawstyle='steps-post' if state.get('step') else 'default',
                    label=key if key is not None else '(missing group)')
        if any(g is not None for g in group): ax.legend()
    elif kind == 'scatter':
        groups = list(dict.fromkeys(columns['group']))
        rng = np.random.default_rng(1)
        ticks = {}
        for i,key in enumerate(groups):
            indices = [j for j in range(n) if columns['group'][j] == key]
            x = [columns['x'][j] for j in indices]; y = [columns['y'][j] for j in indices]
            ax.scatter(x, np.asarray(y)+rng.uniform(-.07,.07,len(y)), s=18,
                       color=palette[i % len(palette)], alpha=.65, label=key)
            for v in y: ticks[v] = key
        ax.set_yticks(list(ticks), list(ticks.values()))
    elif kind == 'box':
        groups = list(dict.fromkeys(columns['group']))
        data = [[v for v,g in zip(columns['value'],columns['group']) if g==key and v is not None] for key in groups]
        bp = ax.boxplot(data, positions=np.arange(len(groups)), widths=.5, showfliers=False, patch_artist=True)
        for box in bp['boxes']: box.set_facecolor(palette[0]); box.set_alpha(.4)
        rng = np.random.default_rng(1)
        for i, values in enumerate(data):
            ax.scatter(i+rng.uniform(-.15,.15,len(values)), values, s=12, alpha=.6, color=palette[0])
        ax.set_xticks(np.arange(len(groups)), groups)
    elif kind == 'bar':
        labels = list(dict.fromkeys(columns['label'])); groups = list(dict.fromkeys(columns['group']))
        width = .8 / max(1,len(groups))
        for i,key in enumerate(groups):
            indices = [j for j in range(n) if columns['group'][j]==key]
            ax.bar([labels.index(columns['label'][j])-.4+width*(i+.5) for j in indices],
                   [columns['value'][j] for j in indices], width=width,
                   color=palette[i % len(palette)], label=key)
        step = max(1, int(np.ceil(len(labels)/20)))
        ticks = list(range(0,len(labels),step)); ax.set_xticks(ticks,[labels[j] for j in ticks])
        if len(groups)>1: ax.legend()
    else:
        raise ValueError('Unsupported plot kind')
    ax.set_xlabel(state.get('xlab','')); ax.set_ylabel(state.get('ylab',''))
    for text in ax.get_xticklabels()+ax.get_yticklabels(): text.set_color(foreground)
    legend=ax.get_legend()
    if legend:
        legend.get_frame().set_facecolor(background)
        for text in legend.get_texts(): text.set_color(foreground)
    return fig


def render(state, **settings):
    fig = figure(state, **settings)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    return {'schema_version':1, 'mime':'image/png', 'png':base64.b64encode(buf.getvalue()).decode('ascii')}

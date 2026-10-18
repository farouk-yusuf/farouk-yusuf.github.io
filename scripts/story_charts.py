"""Question-specific static visuals with HTML labels that stay readable on phones.

SVG draws geometry only. Captions and companion tables are supplied by the story
renderer; no browser chart library, script or external request is required.
"""
from story_components import e


def _position(value, low, high):
    if high <= low or not low <= float(value) <= high:
        raise ValueError(f'Chart value {value} outside [{low}, {high}]')
    return (float(value)-low)/(high-low)*100


def _frame(body, *, ymin, ymax, yticks, xticks, xlabel, ylabel, kind, tick_format=str):
    ylabels = ''.join(f'<span style="bottom:{_position(v,ymin,ymax):.4f}%">{e(tick_format(v))}</span>' for v in yticks)
    grid = ''.join(f'<span style="bottom:{_position(v,ymin,ymax):.4f}%"></span>' for v in yticks)
    xlabels = ''.join(f'<span class="{edge}" style="left:{position:.4f}%">{e(label)}</span>' for position,label,edge in xticks)
    return f'''<div class="story-plot" data-viz="{kind}" aria-hidden="true"><div class="plot-unit">{e(ylabel)}</div><div class="plot-grid"><div class="plot-y-labels">{ylabels}</div><div class="plot-area"><div class="plot-guides">{grid}</div>{body}</div></div><div class="plot-x-labels">{xlabels}</div><div class="plot-x-title">{e(xlabel)}</div></div>'''


def line_chart(labels, values, *, ymax, yticks, ylabel, tick_indices=None, optional_ticks=(), value_format=str, kind='line', ymin=0, reference=None):
    positions = [i/max(1,len(values)-1)*100 for i in range(len(values))]
    heights = [_position(v,ymin,ymax) for v in values]
    points = ' '.join(f'{x:.4f},{100-y:.4f}' for x,y in zip(positions,heights))
    body = f'<svg class="plot-geometry" viewBox="0 0 100 100" preserveAspectRatio="none"><polyline class="plot-series" points="{points}" vector-effect="non-scaling-stroke"/></svg>'
    if reference is not None:
        value,label = reference
        body += f'<div class="plot-reference" style="bottom:{_position(value,ymin,ymax):.4f}%"><span>{e(label)}</span></div>'
    for i,(label,value,x,y) in enumerate(zip(labels,values,positions,heights)):
        body += f'<span class="plot-dot {"plot-dot--focus" if i==len(values)-1 else ""}" data-value="{float(value):.8f}" style="left:{x:.4f}%;bottom:{y:.4f}%" title="{e(label)}: {e(value_format(value))}"></span>'
    if tick_indices is None:
        tick_indices = range(len(labels))
    ticks = [(positions[i],labels[i],('plot-tick--first' if i==0 else 'plot-tick--last' if i==len(labels)-1 else '')+(' plot-tick--optional' if i in optional_ticks else '')) for i in tick_indices]
    return _frame(body,ymin=ymin,ymax=ymax,yticks=yticks,xticks=ticks,xlabel='',ylabel=ylabel,kind=kind,tick_format=value_format)


def paired_dots(rows, *, first_label, second_label, maximum=100, prefix='', suffix='%', places=1, kind='paired-dot'):
    """Pairs share a common scale; connector encodes the difference directly."""
    legend = f'<div class="plot-legend"><span><i class="legend-dot legend-dot--open"></i>{e(first_label)}</span><span><i class="legend-dot"></i>{e(second_label)}</span></div>'
    items = []
    for label,first,second,focus in rows:
        x1,x2 = _position(first,0,maximum),_position(second,0,maximum)
        values = f'<span>{e(prefix)}{float(first):,.{places}f}{e(suffix)}</span><span>{e(prefix)}{float(second):,.{places}f}{e(suffix)}</span>'
        items.append(f'<li class="pair-row {"pair-row--focus" if focus else ""}"><div class="pair-heading"><span>{e(label)}</span><strong>{values}</strong></div><div class="pair-scale"><span class="pair-link" style="left:{min(x1,x2):.4f}%;width:{abs(x2-x1):.4f}%"></span><i class="pair-dot pair-dot--open" data-value="{float(first):.8f}" style="left:{x1:.4f}%"></i><i class="pair-dot" data-value="{float(second):.8f}" style="left:{x2:.4f}%"></i></div></li>')
    ticks = ''.join(f'<span style="left:{v/maximum*100:.4f}%" class="{"plot-tick--first" if v==0 else "plot-tick--last" if v==maximum else ""}">{e(prefix)}{v:g}{e(suffix)}</span>' for v in [0,maximum/4,maximum/2,maximum*3/4,maximum])
    return f'<div class="paired-plot" data-viz="{kind}" aria-hidden="true">{legend}<ul>{"".join(items)}</ul><div class="pair-ticks">{ticks}</div></div>'


def count_comparison(first_label, first, second_label, second):
    return f'<div class="count-comparison" data-viz="count-comparison"><div><span>{e(first_label)}</span><strong>{int(first):,}</strong></div><span class="count-arrow" aria-hidden="true">→</span><div><span>{e(second_label)}</span><strong>{int(second):,}</strong></div></div>'


def rainfall_scatter(rows, *, slope, intercept):
    xmin,xmax,ymin,ymax = 650,1100,10,30
    # Fit is displayed across the observed rainfall range, without an uncertainty band.
    low,high = min(float(r['midlands_rain_mm']) for r in rows),max(float(r['midlands_rain_mm']) for r in rows)
    x1,x2 = _position(low,xmin,xmax),_position(high,xmin,xmax)
    y1,y2 = _position(intercept+slope*low,ymin,ymax),_position(intercept+slope*high,ymin,ymax)
    body = f'<svg class="plot-geometry" viewBox="0 0 100 100" preserveAspectRatio="none"><line class="plot-fit" x1="{x1:.4f}" y1="{100-y1:.4f}" x2="{x2:.4f}" y2="{100-y2:.4f}" vector-effect="non-scaling-stroke"/></svg>'
    for row in rows:
        year = row['year']
        rain,spills = float(row['midlands_rain_mm']),float(row['avg_spills_reliable'])
        x,y = _position(rain,xmin,xmax),_position(spills,ymin,ymax)
        # 2023 and 2024 have nearly identical rain; offset their year labels apart.
        offset = 'scatter-label--below' if year=='2023' else 'scatter-label--right' if year=='2022' else 'scatter-label--above'
        focus = ' plot-dot--focus' if year=='2025' else ''
        body += f'<span class="plot-dot{focus}" data-x="{rain:.8f}" data-value="{spills:.8f}" style="left:{x:.4f}%;bottom:{y:.4f}%"></span><span class="scatter-label {offset}{focus}" style="left:{x:.4f}%;bottom:{y:.4f}%">{e(year)}</span>'
    ticks = [(_position(x,xmin,xmax),str(x),'') for x in (700,800,900,1000)]
    graph = _frame(body,ymin=ymin,ymax=ymax,yticks=(10,15,20,25,30),xticks=ticks,xlabel='Midlands annual rainfall (mm)',ylabel='Average recorded spills per qualifying overflow',kind='scatter')
    return '<p class="plot-fit-key"><span></span>Exploratory line fitted to 2020–2024 · 2025 highlighted</p>'+graph


def comparison_lines(labels, series, *, ymin, ymax, yticks, tick_indices, ylabel):
    """Compare observed data, a tested model and its baseline on the same axes."""
    positions = [i/(len(labels)-1)*100 for i in range(len(labels))]
    paths,legend = [],[]
    for name,values,style in series:
        if len(values)!=len(labels):
            raise ValueError('Each comparison series must have one value per label')
        points = ' '.join(f'{x:.4f},{100-_position(value,ymin,ymax):.4f}' for x,value in zip(positions,values))
        paths.append(f'<polyline class="comparison-path comparison-path--{e(style)}" data-series="{e(name)}" points="{points}" vector-effect="non-scaling-stroke"/>')
        legend.append(f'<span><i class="comparison-key comparison-key--{e(style)}"></i>{e(name)}</span>')
    body = '<svg class="plot-geometry" viewBox="0 0 100 100" preserveAspectRatio="none">'+''.join(paths)+'</svg>'
    ticks = [(positions[i],labels[i],'plot-tick--first' if i==0 else 'plot-tick--last' if i==len(labels)-1 else '') for i in tick_indices]
    return '<div class="comparison-legend">'+''.join(legend)+'</div>'+_frame(body,ymin=ymin,ymax=ymax,yticks=yticks,xticks=ticks,xlabel='',ylabel=ylabel,kind='comparison-lines',tick_format=lambda v:f'{v/1000:g}k')


def balance_waterfall(rows, *, maximum=260000):
    """An additive stock/flow bridge; an unclassified residual has a dashed outline."""
    body,ticks = [],[]
    for i,(label,start,end,display,style) in enumerate(rows):
        x = (i+.5)/len(rows)*100
        low,high = sorted((_position(start,0,maximum),_position(end,0,maximum)))
        # Flow labels sit within the tall bars; totals and residual sit above.
        label_y = (low+high)/2 if style=='flow' else high
        placement = 'waterfall-value--inside' if style=='flow' else ''
        body.append(f'<span class="waterfall-bar waterfall-bar--{e(style)}" data-start="{float(start):.8f}" data-end="{float(end):.8f}" style="left:{x:.4f}%;bottom:{low:.4f}%;height:{high-low:.4f}%"></span><span class="waterfall-value {placement}" style="left:{x:.4f}%;bottom:{label_y:.4f}%">{e(display)}</span>')
        if i<len(rows)-1:
            level = _position(end,0,maximum)
            body.append(f'<span class="waterfall-connector" style="left:{x+6:.4f}%;bottom:{level:.4f}%;width:{100/len(rows)-12:.4f}%"></span>')
        ticks.append((x,label,''))
    return _frame(''.join(body),ymin=0,ymax=maximum,yticks=(0,80000,160000,240000),xticks=ticks,xlabel='',ylabel='Waiting pathways · thousands (k)',kind='waterfall',tick_format=lambda v:f'{v/1000:g}k')

"""Shared, accessible markup for evidence-led case studies."""
from html import escape

GITHUB = "https://github.com/farouk-yusuf/farouk-yusuf.github.io/blob/main/"


def e(value):
    return escape(str(value), quote=True)


def p(text):
    return f'<p>{e(text)}</p>'


def source_link(path, label):
    return f'<a class="evidence-link" href="{GITHUB}{e(path)}" target="_blank" rel="noopener">{e(label)} <span aria-hidden="true">↗</span></a>'


def disclosure(title, body, *, css_class=''):
    classes = 'evidence' + (f' {css_class}' if css_class else '')
    return f'<details class="{e(classes)}"><summary>{e(title)}</summary><div class="evidence-body">{body}</div></details>'


def note(label, text):
    return f'<aside class="practice-note"><span class="practice-label">{e(label)}</span>{p(text)}</aside>'


def metric(value, label):
    return f'<div class="finance-metric"><strong>{e(value)}</strong><span>{e(label)}</span></div>'


def requirements_panels(copy):
    summary = '<aside class="requirements-card" aria-label="Requirements summary"><span class="practice-label">Requirements summary</span><dl>'+''.join(f'<div><dt>{e(label)}</dt><dd>{e(text)}</dd></div>' for label,text in copy['requirements_summary'])+'</dl></aside>'
    framework = copy['requirements_template']
    items = ''.join(f'<li><div class="framework-item-heading"><h3>{e(item["element"])}</h3><span class="framework-status framework-status--{e(item["state"])}">{e(item["status"])}</span></div><dl><div><dt>Framework prompt</dt><dd>{e(item["prompt"])}</dd></div><div><dt>Project application</dt><dd>{e(item["application"])}</dd></div></dl></li>' for item in framework['items'])
    return summary+disclosure('See my requirements elicitation template',p(framework['intro'])+'<ol class="framework-items">'+items+'</ol>',css_class='requirements-template')


def horizontal_bars(rows, maximum, format_value):
    """Zero-based bars; labels remain real, readable HTML at narrow widths."""
    result = []
    for label, value, focus in rows:
        result.append(f'<li class="finance-bar-row"><div class="finance-bar-label"><span>{e(label)}</span><strong>{e(format_value(value))}</strong></div><div class="finance-bar-track" aria-hidden="true"><span class="finance-bar {"finance-bar--focus" if focus else ""}" style="width:{float(value)/maximum*100:.3f}%"></span></div></li>')
    return '<ul class="finance-bars">'+''.join(result)+'</ul>'

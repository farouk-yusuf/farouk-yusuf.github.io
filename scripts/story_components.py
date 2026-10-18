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



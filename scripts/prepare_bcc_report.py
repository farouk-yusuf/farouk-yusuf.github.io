#!/usr/bin/env python3
"""Prepare the supplied Power BI PDF and readable static report previews.

Requires PyMuPDF only for asset preparation; website builds remain standard-library
only. Corrects the review-page scope caption and standardises report headings,
preserving the exported report data and visuals.
"""
import argparse
import hashlib
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'projects/01_BCC_Payments/outputs/Birmingham_Payments_PowerBI_Report.pdf'
REVIEW_SCOPE = '1 July 2024–23 July 2026 · Potential duplicates for invoice checks'
PAGES = (
    ('Spending overview', 'assets/bcc-dashboard.png'),
    ('Supplier movements', 'assets/reports/birmingham-suppliers.png'),
    ('Payment review', 'assets/reports/birmingham-payment-review.png'),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', type=Path, required=True)
    args = parser.parse_args()
    assert args.source_pdf.resolve() != OUTPUT.resolve(), 'Keep the supplied source PDF unchanged.'
    document = fitz.open(args.source_pdf)
    assert len(document) == 3, 'Expected the three-page Birmingham report.'
    assert all(abs(page.rect.width-1476) < 1 and abs(page.rect.height-846) < 1 for page in document)
    # Reuse the source's embedded Segoe UI fonts, rather than substituting fonts.
    fonts = {}
    for xref,_,_,base,_,_ in document[0].get_fonts():
        if base.endswith('+SegoeUI'):
            fonts['regular'] = document.extract_font(xref)[3]
        elif base.endswith('+SegoeUI-Bold'):
            fonts['bold'] = document.extract_font(xref)[3]
    assert set(fonts) == {'regular', 'bold'}
    ink = (36/255,)*3
    background = (249/255,)*3
    bold = fitz.Font(fontbuffer=fonts['bold'])
    regular = fitz.Font(fontbuffer=fonts['regular'])
    identity = 'Birmingham City Council Payments'
    for index, (title,_) in enumerate(PAGES):
        page = document[index]
        if index:
            page.add_redact_annot(fitz.Rect(38,39,1200,74), fill=background)
        if index == 2:
            page.add_redact_annot(fitz.Rect(38,77,1200,97), fill=background)
        if index:
            page.apply_redactions(images=0, graphics=0)
            page.insert_font(fontname='BCCBold', fontbuffer=fonts['bold'])
            page.insert_font(fontname='BCCRegular', fontbuffer=fonts['regular'])
            page.insert_text((39.75,66), identity, fontsize=24, fontname='BCCBold', color=ink)
            suffix = ' | '+title
            assert all(regular.has_glyph(ord(c)) for c in suffix if not c.isspace())
            page.insert_text((39.75+bold.text_length(identity,fontsize=24),66), suffix,
                             fontsize=24, fontname='BCCRegular', color=ink)
            if index == 2:
                assert all(regular.has_glyph(ord(c)) for c in REVIEW_SCOPE if not c.isspace())
                page.insert_text((39.75,91.5), REVIEW_SCOPE, fontsize=12,
                                 fontname='BCCRegular', color=ink)
    metadata = document.metadata
    metadata.update(title='Birmingham City Council Payments — Power BI report',
                    author='Farouk Yusuf',
                    subject='Spending overview, supplier movements and potential duplicate-payment review')
    document.set_metadata(metadata)
    document.set_toc([[1,title,index+1] for index,(title,_) in enumerate(PAGES)])
    document.save(OUTPUT, garbage=4, deflate=True)
    document.close()
    published = fitz.open(OUTPUT)
    for index,(_,filename) in enumerate(PAGES):
        target = ROOT/filename
        target.parent.mkdir(parents=True, exist_ok=True)
        published[index].get_pixmap(matrix=fitz.Matrix(1.5,1.5), alpha=False).save(target)
    assert REVIEW_SCOPE in published[2].get_text()
    assert 'All supplier payments in the matched periods' not in published[2].get_text()
    assert all(value in published[0].get_text() for value in ('£558.64M','£677.46M','£118.82M'))
    assert all(value in published[2].get_text() for value in ('281','£4.45M','73','PAIR-001'))
    published.close()
    print(json.dumps({
        'source_sha256':hashlib.sha256(args.source_pdf.read_bytes()).hexdigest(),
        'pdf':str(OUTPUT.relative_to(ROOT)),
        'preview_dimensions':[2214,1269],
        'corrections':['Page 2 and 3 headings standardised','Page 3 caption corrected to full publication coverage'],
    },indent=2))


if __name__ == '__main__':
    main()

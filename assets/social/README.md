# LinkedIn Featured and link-preview covers

These 1200 × 627 PNG covers use the actual portfolio charts, real dashboard
screenshots, local fonts, tool icons and existing organisation marks. No generated
illustrations or synthetic dashboard screenshots are included.

| File | Intended Featured item |
| --- | --- |
| `portfolio.png` | Main data analysis portfolio |
| `birmingham-dashboard.png` | Interactive Birmingham payments dashboard |
| `birmingham-power-bi.png` | Power BI report PDF or Birmingham case study |
| `nhs-waiting-times.png` | NHS waiting-times case study |
| `platform-housing.png` | Platform Housing tenant satisfaction case study |
| `severn-trent.png` | Severn Trent storm overflow case study |

Download a PNG to use as a custom Featured thumbnail. The homepage, interactive
dashboard and all four public-data case studies also declare the appropriate
cover through Open Graph and Twitter metadata. Existing LinkedIn cards may retain
a cached image; changing a site's metadata does not guarantee an existing card
will refresh. A direct PDF link cannot declare HTML Open Graph metadata, so use
its custom thumbnail or link to the case-study report section.

The source screenshots in `evidence/` are captured from the current committed site
by `scripts/prepare_link_previews.py`. The Power BI cover uses the existing PDF
preview at `assets/bcc-dashboard.png`. The script composes text, logos and these
screenshots in a browser-rendered HTML layout. The sticky site navigation is hidden
during chart capture so it cannot overlap a chart; chart contents are unchanged.
Fonts and other assets
load locally. Regenerate after relevant chart changes:

```sh
python3 scripts/build_site.py
python3 scripts/prepare_link_previews.py
python3 scripts/check_site.py
```

Screenshot rendering requires Playwright and Chromium; ordinary website builds
remain Python standard-library only. The metadata configuration is
`site/social.json`; `scripts/social_preview.py` renders tags for generated pages.
The standalone dashboard keeps the corresponding tags in its own HTML head.

Organisation marks follow [the existing provenance notes](../logos/README.md).
The NHS mark identifies the sector, not a UHB-specific logo. Covers explicitly
identify the work as independent analysis of public data. Logos do not imply
employment, commissioning or endorsement.

Project covers use a larger logo above the organisation name. The portfolio grid
also gives the logos more space. The NHS SVG's surrounding whitespace is cropped
in CSS for clearer display; its mark, proportions and colours are unchanged.

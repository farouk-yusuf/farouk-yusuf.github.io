# Organisation marks

The site presents independent analysis, not commissioned work or endorsements.

- `nhs.svg`: NHS mark from the official NHS UK frontend repository, `packages/nhsuk-frontend/src/nhsuk/assets/images/favicon.svg`, commit `9351854f1d8319fe1652ed901dbff47c13c73862`. Original source: https://github.com/nhsuk/nhsuk-frontend. This is the NHS mark, not a University Hospitals Birmingham trust logo. NHS identity remains subject to its own brand guidance; it identifies the NHS subject of this portfolio analysis.
- `bcc.png`, `platform.png` and `severn-trent.png`: supplied by the user in `assets.zip` on 18 October 2026. The original PNGs are used unchanged. They identify the organisations analysed in the portfolio and do not imply affiliation or endorsement.

The logo filenames are configured in `site/projects.json`; run `python3 scripts/build_site.py` after changing assets or filenames. For a UHB trust-specific mark, update its `logo` filename and alt text as appropriate. The current UHB project uses the NHS mark. Keep the independence statement visible.

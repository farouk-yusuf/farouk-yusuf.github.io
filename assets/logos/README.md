# Organisation marks

The site presents independent analysis, not commissioned work or endorsements.

- `nhs.svg`: NHS mark from the official NHS UK frontend repository, `packages/nhsuk-frontend/src/nhsuk/assets/images/favicon.svg`, commit `9351854f1d8319fe1652ed901dbff47c13c73862`. Original source: https://github.com/nhsuk/nhsuk-frontend. This is the NHS mark, not a University Hospitals Birmingham trust logo. NHS identity remains subject to its own brand guidance; it identifies the NHS subject of this portfolio analysis.
- Official Birmingham City Council, Platform Housing and Severn Trent logos could not be downloaded during this change because the environment denied access to their websites. The site uses clearly readable names and neutral initial tiles rather than fabricated organisation marks.

To add approved official logos, save them here as `bcc.svg`, `platform.svg` and `severn-trent.svg`, record their official source URLs and any usage conditions, and run `python3 scripts/build_site.py`. For a UHB trust-specific mark, update the UHB `logo` filename in `site/projects.json` and its alt text in `scripts/build_site.py` as appropriate. Keep the independence statement visible.

# Activate Farouk's GitHub profile

[README.md](README.md) is the prepared profile content. It uses native GitHub Markdown, the portfolio's existing organisation logos and tool icons. It works in a profile repository without a build step or third-party statistics services.

## Main profile panel

GitHub displays a profile README when a **public repository matches the account username**. For this account, the repository must be **`farouk-yusuf/farouk-yusuf`**, with **`README.md` at its root**. A README in `farouk-yusuf.github.io` does not activate that panel.

1. While signed into GitHub as `farouk-yusuf`, [create a public repository named farouk-yusuf](https://github.com/new?name=farouk-yusuf).
2. Add the contents of this folder's [README.md](README.md) as the repository's root `README.md`, then commit it to the default branch.
3. Open [the GitHub profile](https://github.com/farouk-yusuf) to see the new main panel.

The README's fully qualified image URLs point to existing portfolio assets, so no extra asset upload is needed for the profile panel. The NHS image is an NHS mark, not a UHB-specific trust logo.

## Sidebar settings

GitHub controls the sidebar independently of the README. In [profile settings](https://github.com/settings/profile), the following copy fits the existing portfolio:

| Field | Suggested value |
|---|---|
| Name | Farouk Yusuf |
| Bio | Data analyst · SQL, Python, Excel & Power BI · Six years in research · Clear evidence, practical recommendations · Birmingham, UK |
| Location | Birmingham, UK |
| Website | https://farouk-yusuf.github.io/ |
| LinkedIn | https://www.linkedin.com/in/farouk-yusuf-fy |

The selected [colour headshot](../assets/images/headshot-3.png) is available for the sidebar photograph if desired. Upload that original file through GitHub’s profile-photo setting; updating a README does not change the account avatar.

## Portfolio photograph

The site uses `assets/images/headshot-3.png`, the 1086 × 1448 colour portrait supplied in `assets.zip` and selected again by the user. After replacing that file, rebuild with:

```sh
python3 scripts/build_site.py
python3 scripts/check_site.py
```

The colour PNG is active on the homepage. The square black-and-white JPEG remains a fallback. The display crop is controlled by the homepage CSS.

## Publication status for this handoff

The profile README is prepared for review in the portfolio repository. It has not been activated on the account profile. A read of `farouk-yusuf/farouk-yusuf` returned “Repository not found”; the GitHub API returned a forbidden response, so account settings and repository creation could not be completed from this environment. No profile, biography or avatar change is claimed.

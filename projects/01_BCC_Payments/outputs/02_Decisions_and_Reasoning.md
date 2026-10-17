# Decisions and reasoning (interview prep)

**Why combine the corporate directorates?** The September 2025 restructure moved budgets between Council Management, Finance and HR, so Council Management "fell 100%" and Finance "rose from zero". Comparing them as one group shows the real movement.

**Why compare 1 Apr to 23 Jul, not April to July?** The data stops on 23 July 2026. Comparing a partial July with a full July last year would understate this year.

**How were duplicates defined?** Same supplier, same amount (£1,000+), within 3 days, and that amount appears exactly twice in two years. Care providers bill many identical package rates, so without the "exactly twice" rule the check returned 6,553 pairs, mostly legitimate. One-off amounts paid twice are the classic duplicate signature.

**Why pseudonymise rather than delete individuals' payments?** Their spend still counts in totals, but nothing in the outputs can identify them. The hash is one-way; in an organisation the key would be held securely.

**Why a star schema?** Payments are facts; suppliers, directorates, categories and dates are dimensions. That's how a finance reporting database or a Power BI model would be built, and it makes the SQL simple.

**Limitations:** no invoice references, no budgets, payments not commitments, and spend is by payment date, so timing differences (as with the highways PFI) move year-to-date figures.

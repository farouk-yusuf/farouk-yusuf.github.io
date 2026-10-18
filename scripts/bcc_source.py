"""Read the council CSV and reconcile complete, public-safe reporting aggregates."""
import ast
from collections import Counter, defaultdict
import csv
from datetime import date
from decimal import Decimal
import hashlib
from pathlib import Path

CENT = Decimal('.01')
PRIVATE_LABEL = 'Individuals (names withheld)'


def literal_assignment(filename, name):
    for node in ast.parse(Path(filename).read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f'Missing source assignment: {name}')


def source_model(filename, project):
    """Return exact aggregates; supplier account identifiers never leave this function.

    The supplier comparison includes every name/group present in either matched
    window, including zero-net balances. All rows linked to a redacted account
    are pooled, including the names exposed elsewhere under the same identifier.
    """
    filename = Path(filename)
    mapping = literal_assignment(project/'scripts/01_clean.py', 'dir_map')
    corporate = literal_assignment(project/'scripts/03_finance_pack.py', 'CORP')
    group = lambda name: 'Corporate services (combined)' if name in corporate else name
    with filename.open(encoding='utf-8-sig', newline='') as stream:
        sample = stream.read(8192)
        stream.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        reader = csv.DictReader(stream, dialect=dialect)
        required = {'date', 'department', 'beneficiary', 'amount', 'supplier_number'}
        if not required <= set(reader.fieldnames or []):
            raise ValueError('Use the original council CSV, with its original column headings.')
        rows = list(reader)
    if not rows:
        raise ValueError('The source CSV is empty.')
    redacted = lambda name: ''.join(name.upper().replace('-', '').split()).startswith('REDACTEDPERSONALDATA')
    protected = {r['supplier_number'] for r in rows if redacted(r['beneficiary'])}
    spellings = defaultdict(Counter)
    for row in rows:
        account = row['supplier_number']
        if not account or not row['beneficiary'].strip():
            raise ValueError('A source row has a missing supplier account or beneficiary.')
        if account not in protected:
            spellings[account][row['beneficiary']] += 1
    names = {account: counts.most_common(1)[0][0] for account, counts in spellings.items()}
    monthly = defaultdict(lambda: [Decimal(0), 0])
    matched = defaultdict(lambda: [Decimal(0), Decimal(0), Decimal(0)])
    suppliers = defaultdict(lambda: [Decimal(0), Decimal(0)])
    duplicate_groups = defaultdict(list)
    dates = []
    total = Decimal(0)
    comparison_lines = 0
    comparison_accounts = set()
    public_comparison_accounts = set()
    for row in rows:
        if row['department'] not in mapping:
            raise ValueError('The source has an unmapped department; review the upstream mapping.')
        day = date.fromisoformat(row['date'])
        amount = Decimal(row['amount'])
        if not amount.is_finite() or amount != amount.quantize(CENT):
            raise ValueError('A source amount is invalid or has fractions of a penny.')
        report_group = group(mapping[row['department']])
        account = row['supplier_number']
        supplier = PRIVATE_LABEL if account in protected else names[account]
        dates.append(day)
        total += amount
        month = day.replace(day=1)
        monthly[month, report_group][0] += amount
        monthly[month, report_group][1] += 1
        index = None
        if date(2025, 4, 1) <= day <= date(2025, 7, 23):
            index = 0
        elif date(2026, 4, 1) <= day <= date(2026, 7, 23):
            index = 1
        if index is not None:
            matched[report_group][index] += amount
            suppliers[report_group, supplier][index] += amount
            comparison_lines += 1
            comparison_accounts.add(account)
            if account not in protected:
                public_comparison_accounts.add(account)
        if date(2025, 4, 1) <= day <= date(2026, 3, 31):
            matched[report_group][2] += amount
        if account not in protected and amount >= 1000:
            duplicate_groups[account, amount].append((day, report_group))
    # This report is tied to the original publication snapshot, not an arbitrary refresh.
    assert len(rows) == 247785, 'Source row count changed; review the report scope.'
    assert min(dates) == date(2024, 7, 1) and max(dates) == date(2026, 7, 23)
    assert total == Decimal('3873852012.19'), 'Source payment total changed.'
    signatures = Counter()
    same_day = 0
    for (account, amount), observations in duplicate_groups.items():
        if len(observations) != 2:
            continue
        ordered = sorted(observations, key=lambda item: item[0])
        first, last = ordered[0][0], ordered[1][0]
        if (last-first).days <= 3:
            signatures[names[account], amount, first, last] += 1
            same_day += first == last
    assert sum(signatures.values()) == 281 and same_day == 73
    assert sum(key[1]*count for key, count in signatures.items()) == Decimal('4448515.38')
    # Supplier comparisons must explain every penny in every reporting group.
    for report_group, expected in matched.items():
        actual = [sum(values[i] for (g, _), values in suppliers.items() if g == report_group) for i in (0, 1)]
        assert actual == expected[:2], f'Supplier totals do not reconcile: {report_group}'
    return {
        'monthly': monthly, 'matched': matched, 'suppliers': suppliers,
        'candidate_signatures': signatures,
        'source': {
            'filename': filename.name,
            'sha256': hashlib.sha256(filename.read_bytes()).hexdigest(),
            'rows': len(rows), 'total_gbp': str(total),
            'first_date': min(dates).isoformat(), 'last_date': max(dates).isoformat(),
            'matched_payment_lines': comparison_lines,
            'matched_supplier_accounts': len(comparison_accounts),
            'matched_named_supplier_accounts': len(public_comparison_accounts),
            'matched_supplier_display_names': len({name for _, name in suppliers}),
            'supplier_grain': 'Reporting group and standardised supplier display name; all matched-period accounts included. Private accounts pooled by reporting group.',
            'privacy': 'Original supplier numbers, personal pseudonyms and payment descriptions omitted. Names linked to any redacted account withheld.',
        },
    }

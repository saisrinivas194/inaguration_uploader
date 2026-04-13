# Project Status

## Current Implementation

The uploader supports both:
- **Company totals** - Name of the company plus donation amount
- **Committee/contributor rows** - Employer or contributor name plus contribution amount

## Current Functionality

**Inauguration Upload**
- Reads CSV files with company name and amount columns
- Reads committee/contributor exports with `contribution_receipt_amount`
- Automatically detects column names (company/Company, amount/Amount, etc.)
- Falls back from employer to contributor name so PAC donations are still attributed when employer is blank
- Matches companies to brands in Firebase using:
  - Ticker symbols (if available, most reliable)
  - Fuzzy name matching (handles variations like "Apple Inc" vs "Apple Incorporated")
- Rolls up all matched contribution rows per brand before upload
- Uploads amounts to: `brands/{brand_id}/influence/inauguration`

## Data Structure

### Company Totals
```
company,amount
Acme Corp,50000
Tech Inc,75000
```

### Committee/Contributor Rows
```
committee_id,committee_name,contributor_name,contributor_employer,contribution_receipt_amount
C001,Inaugural Committee,Example Corp PAC,,250
C001,Inaugural Committee,Jane Doe,Example Corp,500
```

Supported fields include:
- committee_id
- committee_name
- contributor_name
- contributor_employer
- contribution_receipt_date
- contribution_receipt_amount
- contributor_aggregate_ytd

## Key Points

1. **No PAC floor**: There is no `$1000` minimum or any other PAC donation threshold
2. **All contributions counted**: Row-level files are summed by brand before upload
3. **Executive vs PAC**: Not needed for storage - only final brand totals matter
4. **Ticker Optional**: Works with just company name, but ticker symbols improve matching accuracy

## Implementation Status

1. **Company totals uploader** - Complete
2. **Committee/contributor uploader** - Complete
3. **Additional source-specific mappings** - Can be extended if new column variants appear

## Usage

```bash
# Test with company totals data
python uploader.py company_tab.csv --dry-run

# Upload committee/contributor data
python uploader.py pac_rows.csv --dry-run

# Upload finalized data
python uploader.py company_tab.csv
```

The tool automatically handles both simple company totals and row-level contribution files.

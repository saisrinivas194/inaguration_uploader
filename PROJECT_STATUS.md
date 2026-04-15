# Project Status

## Current Implementation: Company Tab Only

The uploader tool is currently focused on the company tab, which has a simple two-column format:
- **Company Name** - Name of the company
- **Amount** - Inauguration donation amount

## Current Functionality

**Company Tab Upload**
- Reads CSV files with company name and amount columns
- Automatically detects column names (company/Company, amount/Amount, etc.)
- Matches companies to brands in Firebase using:
  - Ticker symbols (if available, most reliable)
  - Fuzzy name matching (handles variations like "Apple Inc" vs "Apple Incorporated")
- Uploads amounts to: `brands/{brand_id}/influence/inauguration`

## Data Structure

### Company Tab (Current Focus)
```
company,amount
Acme Corp,50000
Tech Inc,75000
```

### Individual People Tab (Future - Unconfirmed)
- More complex structure with two potential data formats
- Individual inauguration / executives data
- Currently no upload functionality
- Will be implemented after confirming data structure requirements

**Potential Format 1 - Individual People Tab:**
- Full Name
- Amount
- Company
- Job Title
- Trump Assignment

**Potential Format 2 - Committee/Contributor Data:**
- committee_id
- committee_name
- contributor_name
- contributor_first_name
- contributor_last_name
- contributor_zip
- contributor_employer
- contributor_occupation
- contributor_id
- contribution_receipt_date
- contribution_receipt_amount
- contributor_aggregate_ytd

Note: These formats are not yet confirmed and may be subject to change.

## Key Points

1. **No Overlap**: Some donations appear in company tab but not individual people tab, and vice versa
2. **Simple Format**: Company tab only requires company name and amount
3. **Exact Amounts**: May not all be in company tab - eventually may need to handle both tabs
4. **Executive vs PAC**: Not needed - only total amounts matter
5. **Ticker Optional**: Works with just company name, but ticker symbols improve matching accuracy

## Implementation Status

1. **Company tab uploader** - Complete
2. **Individual people tab details** - Pending data structure confirmation
3. **Individual people tab uploader** - Pending implementation after requirements confirmed

## Usage

```bash
# Test with company tab data
python uploader.py company_tab.csv --dry-run

# Upload company tab data
python uploader.py company_tab.csv
```

The tool automatically handles the simple two-column format from the company tab.


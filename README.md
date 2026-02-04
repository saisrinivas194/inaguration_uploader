# Inauguration Data Uploader

A tool for uploading inauguration data to Firebase from the **company tab**. The data is written to the following structure:

```
brands
  └─ {brand_id}
      └─ influence
          └─ inauguration: {amount}
```

## Current Focus: Company Tab

This tool is designed for the company tab which has a simple two-column format:
- **Company Name** - The name of the company
- **Amount** - The inauguration donation amount

The individual people tab (individual inauguration / executives) is more complex with two potential data formats and will be handled separately in the future. These formats are not yet confirmed.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Firebase Credentials:**
   - Download your Firebase service account JSON file from the Firebase Console
   - Place it in the project directory as `firebase-credentials.json`
   - Or set the `FIREBASE_CREDENTIALS` environment variable to point to the file path

## Usage

### Basic Usage

```bash
python uploader.py data.csv
```

### Options

- `--dry-run` or `-d`: Test run without actually uploading data
- `--credentials` or `-c`: Specify path to Firebase credentials file
- `--show-unmatched`: Show all companies that couldn't be matched to brands
- `--fuzzy-threshold SCORE`: Minimum similarity score (0-100) for fuzzy matching. Default: 85
- `--show-match-details`: Show detailed match information including scores and match types

### Examples

```bash
# Dry run to test matching
python uploader.py inauguration_data.csv --dry-run

# Upload with custom credentials path
python uploader.py data.csv --credentials /path/to/credentials.json

# Upload with custom fuzzy threshold (lower = more permissive)
python uploader.py data.csv --fuzzy-threshold 75

# Upload and show detailed match information
python uploader.py data.csv --show-match-details

# Upload with ticker symbols and show details
python uploader.py data.csv --show-match-details --fuzzy-threshold 80
```

## Data Format

### CSV Format - Company Tab

The CSV file from the **company tab** should contain two columns: company name and amount. The tool will automatically detect common column names:

**Company name columns (detected in this order):**
- `company` or `Company` (most common)
- `company_name` or `Company Name`
- `name` or `Name`
- `brand` or `Brand`

**Amount columns (detected in this order):**
- `amount` or `Amount` (most common)
- `inauguration` or `Inauguration`
- `value` or `Value`

**Ticker symbol columns (optional, if available):**
- `ticker` or `Ticker`
- `ticker_symbol` or `Ticker Symbol`
- `symbol` or `Symbol`

**Simple Company Tab Example:**
```csv
company,amount
Acme Corp,50000
Tech Inc,75000
Apple Inc,100000
```

**With Ticker (if available):**
```csv
company,ticker,amount
Acme Corp,ACME,50000
Tech Inc,TECH,75000
Apple Inc,AAPL,100000
```

Note: The tool works with just company name and amount. Ticker symbols are optional but provide more reliable matching if available.

### JSON Format

The JSON file can be either an array of objects or a single object:

```json
[
  {
    "company": "Acme Corp",
    "ticker": "ACME",
    "amount": 50000
  },
  {
    "company": "Tech Inc",
    "ticker": "TECH",
    "amount": 75000
  },
  {
    "ticker": "AAPL",
    "amount": 100000
  }
]
```

## Company Matching

The tool automatically matches companies from external data to brand IDs in Firebase using **fuzzy matching** and **ticker symbols**. The matching process:

1. **Ticker Matching (Highest Priority)**: If a ticker symbol is provided, it matches exactly against ticker symbols in the database
2. **Exact Name Matching**: Normalizes and matches company names exactly
3. **Fuzzy Matching**: Uses the RapidFuzz library to find similar company names with configurable similarity threshold
4. **Partial Matching**: Checks for partial matches (one name contains the other)
5. **Alias Matching**: Checks against brand aliases if available

### Match Types

- **ticker**: Matched by ticker symbol (100% confidence)
- **exact**: Exact name match after normalization (100% confidence)
- **fuzzy**: Fuzzy match above threshold (shows similarity score)
- **partial**: Partial match (shows similarity score)

### Fuzzy Matching Threshold

The `--fuzzy-threshold` option controls how strict the fuzzy matching is:
- **Higher values (85-100)**: More strict, only very similar names match
- **Lower values (60-84)**: More permissive, allows more variation
- **Default: 85**

Example: With threshold 85, "Apple Inc" would match "Apple Incorporated" but might not match "Apple Computer" (depending on similarity score).

## Output

The tool provides:
- Number of records found
- Number of companies matched to brands (with breakdown by match type)
- Number of companies unmatched
- Match details (if `--show-match-details` is used): Shows which companies matched to which brands, match type, and similarity scores
- Upload progress and results
- Summary statistics

## Notes

- **Current focus**: Company tab only (simple two-column format: company name, amount)
- **Future**: Individual people tab will be handled separately after confirming data structure requirements
  - Potential Format 1: Full Name, Amount, Company, Job Title, Trump Assignment
  - Potential Format 2: Committee/Contributor data with multiple fields (committee_id, contributor_name, contributor_employer, contribution_receipt_amount, contributor_aggregate_ytd, etc.)
  - Note: These formats are not yet confirmed and may be subject to change
- The tool uses fuzzy matching (RapidFuzz library) to handle variations in company names
- Ticker symbols provide the most reliable matching method - use them when available
- Unmatched companies are reported but skipped by default
- Use `--dry-run` to test matching before uploading
- Use `--show-match-details` to review how companies were matched
- Adjust `--fuzzy-threshold` if you're getting too many or too few matches
- The inauguration amount overwrites any existing value for that brand
- Match scores are shown for fuzzy and partial matches to help verify correctness
- No overlap between tabs - some donations appear in one tab but not the other


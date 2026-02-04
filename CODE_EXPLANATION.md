# Complete Code Explanation

## Project Overview

This is a Python-based tool for uploading inauguration donation data to Firebase. It reads company data from CSV or JSON files, matches companies to brands in Firebase using intelligent matching algorithms, and uploads the inauguration amounts to the correct Firebase location.

## Project Structure

```
Inaguration_uploader/
├── uploader.py           # Main script with file parsing and upload logic
├── company_matcher.py     # Company matching algorithms (fuzzy matching, ticker matching)
├── firebase_config.py     # Firebase initialization and configuration
├── requirements.txt        # Python dependencies
├── README.md              # User documentation
├── PROJECT_STATUS.md      # Project status and roadmap
└── CODE_EXPLANATION.md    # This file
```

## Architecture Overview

The tool follows a modular architecture with three main components:

1. **Firebase Configuration** (`firebase_config.py`) - Handles Firebase connection
2. **Company Matching** (`company_matcher.py`) - Handles matching logic
3. **Data Upload** (`uploader.py`) - Handles file parsing and upload orchestration

## Detailed Code Explanation

### 1. firebase_config.py

**Purpose**: Manages Firebase connection and initialization.

#### Key Components:

**Global Variable:**
- `_db`: Stores the Firestore client instance (singleton pattern)

**Functions:**

**`initialize_firebase(credential_path=None)`**
- Initializes Firebase Admin SDK
- Loads credentials from file or environment variable
- Returns Firestore client instance
- Uses singleton pattern to avoid multiple initializations
- Handles errors gracefully with clear error messages

**`get_db()`**
- Returns the Firestore client instance
- Ensures Firebase is initialized before returning
- Raises error if called before initialization

**How it works:**
1. Checks if Firebase is already initialized
2. If not, loads credentials from file or environment variable
3. Initializes Firebase Admin SDK
4. Creates and returns Firestore client
5. Stores client globally for reuse

---

### 2. company_matcher.py

**Purpose**: Matches company names from external data to brand IDs in Firebase.

#### Key Functions:

**`normalize_company_name(name)`**
- Normalizes company names for consistent matching
- Converts to lowercase
- Removes common business suffixes (Inc, LLC, Ltd, Corp, etc.)
- Removes special characters
- Normalizes whitespace
- Example: "Apple Inc." → "apple"

**`normalize_ticker(ticker)`**
- Normalizes ticker symbols
- Converts to uppercase
- Removes spaces and exchange prefixes (NYSE:, NASDAQ:, etc.)
- Example: "NYSE: AAPL" → "AAPL"

**`get_all_brands()`**
- Fetches all brands from Firebase
- Returns dictionary mapping brand_id to brand data
- Used to build matching database

**`find_brand_id_by_ticker(ticker, brands)`**
- Matches by ticker symbol (most reliable method)
- Performs exact match after normalization
- Returns brand_id if found, None otherwise

**`find_brand_id_by_name(company_name, brands, fuzzy_threshold)`**
- Matches by company name using multiple strategies:
  1. **Exact match** - After normalization (100% confidence)
  2. **Partial match** - One name contains the other
  3. **Alias match** - Checks brand aliases
  4. **Fuzzy match** - Uses RapidFuzz library for similarity matching
- Returns tuple: (brand_id, similarity_score)
- Uses configurable threshold (default: 85%)

**`find_brand_id(company_name, ticker, brands, fuzzy_threshold)`**
- Main matching function that tries both ticker and name
- **Priority order:**
  1. Ticker symbol (if provided) - Most reliable
  2. Company name matching
- Returns tuple: (brand_id, score, match_type)
- Match types: 'ticker', 'exact', 'fuzzy', 'partial'

**`match_companies_to_brands(company_data, fuzzy_threshold)`**
- Main function for matching multiple companies
- Processes list of company records
- Returns dictionary with:
  - `matched`: Dictionary of matched companies
  - `unmatched`: List of unmatched companies
  - `match_details`: Detailed match information
  - Statistics: total, matched_count, unmatched_count

**Matching Algorithm Flow:**
```
For each company:
  1. Extract company name and/or ticker
  2. Try ticker matching first (if available)
  3. If no ticker match, try name matching:
     a. Exact match (normalized)
     b. Partial match (contains)
     c. Alias match
     d. Fuzzy match (RapidFuzz)
  4. Record match result with score and type
```

---

### 3. uploader.py

**Purpose**: Main script that orchestrates file parsing, matching, and uploading.

#### Constants:

**`INDIVIDUAL_PEOPLE_FORMAT1_COLUMNS`**
- Future format definition (not yet implemented)
- Columns: Full Name, Amount, Company, Job Title, Trump Assignment

**`COMMITTEE_CONTRIBUTOR_FORMAT2_COLUMNS`**
- Future format definition (not yet implemented)
- 12 columns for committee/contributor data

#### Key Functions:

**`parse_csv_file(file_path)`**
- Parses CSV files containing inauguration data
- Automatically detects column names:
  - Company: 'company', 'Company', 'company_name', etc.
  - Ticker: 'ticker', 'Ticker', 'ticker_symbol', etc.
  - Amount: 'amount', 'Amount', 'inauguration', etc.
- Handles amount formatting (removes $, commas)
- Returns list of dictionaries with parsed data
- Skips invalid rows with warnings

**`parse_json_file(file_path)`**
- Parses JSON files
- Handles multiple formats:
  - Array of objects
  - Dictionary with 'data' key
  - Dictionary with 'companies' key
  - Single object (converts to list)
- Returns list of dictionaries

**`upload_inauguration_data(brand_id, amount, dry_run, verbose)`**
- Uploads single inauguration amount to Firebase
- Firebase path: `brands/{brand_id}/influence/inauguration`
- Supports dry-run mode (simulation)
- Returns True/False for success/failure
- Handles errors gracefully

**`upload_from_file(file_path, dry_run, skip_unmatched, fuzzy_threshold, show_match_details)`**
- Main orchestration function
- **Process flow:**
  1. Parse file (CSV or JSON)
  2. Match companies to brands
  3. Display match statistics
  4. Upload matched data
  5. Return statistics
- Provides detailed progress reporting
- Shows match type breakdown
- Handles unmatched companies

**`main()`**
- Command-line interface entry point
- Uses argparse for argument parsing
- **Command-line options:**
  - `file`: Input file path (required)
  - `--credentials, -c`: Firebase credentials path
  - `--dry-run`: Test mode without uploading
  - `--show-unmatched`: Display unmatched companies
  - `--fuzzy-threshold SCORE`: Matching sensitivity (0-100)
  - `--show-match-details`: Show detailed match information
- Validates inputs
- Handles errors and exits gracefully

## Data Flow

```
1. User runs: python uploader.py data.csv
   ↓
2. main() initializes Firebase
   ↓
3. upload_from_file() called
   ↓
4. parse_csv_file() reads and parses CSV
   ↓
5. match_companies_to_brands() matches companies
   ├─→ get_all_brands() fetches brands from Firebase
   ├─→ find_brand_id() matches each company
   │   ├─→ find_brand_id_by_ticker() (if ticker available)
   │   └─→ find_brand_id_by_name() (fuzzy matching)
   ↓
6. upload_inauguration_data() uploads each match
   ↓
7. Statistics and results displayed
```

## Firebase Data Structure

The tool writes data to Firebase in this structure:

```
brands/
  └─ {brand_id}/
      └─ influence/
          └─ inauguration: {amount}
```

Example:
```
brands/
  └─ apple_inc/
      └─ influence/
          └─ inauguration: 100000
```

## Matching Strategies

### 1. Ticker Matching (Highest Priority)
- **Method**: Exact match after normalization
- **Confidence**: 100%
- **Use case**: Most reliable when ticker symbols are available
- **Example**: "AAPL" matches "Apple Inc."

### 2. Exact Name Matching
- **Method**: Normalized exact match
- **Confidence**: 100%
- **Example**: "Apple Inc" matches "Apple Incorporated" (after normalization)

### 3. Partial Matching
- **Method**: One name contains the other
- **Confidence**: Calculated similarity score
- **Example**: "Apple" matches "Apple Computer Inc"

### 4. Fuzzy Matching
- **Method**: RapidFuzz library (WRatio algorithm)
- **Confidence**: Similarity score (0-100%)
- **Threshold**: Configurable (default: 85%)
- **Example**: "Apple Inc" matches "Apple Incorporated" with 92% similarity

### 5. Alias Matching
- **Method**: Checks brand aliases in Firebase
- **Confidence**: 100% for exact alias match
- **Use case**: Handles alternative company names

## Error Handling

The code includes comprehensive error handling:

1. **File Errors**: Handles missing files, invalid formats
2. **Parsing Errors**: Skips invalid rows with warnings
3. **Firebase Errors**: Clear error messages for connection/upload failures
4. **Validation**: Validates fuzzy threshold range (0-100)
5. **Graceful Degradation**: Continues processing even if some records fail

## Key Features

### 1. Automatic Column Detection
- Detects common column name variations
- Works with different CSV formats
- Case-insensitive matching

### 2. Intelligent Matching
- Multiple matching strategies
- Configurable sensitivity
- Handles name variations

### 3. Dry-Run Mode
- Test matching without uploading
- Preview what would be uploaded
- Safe testing environment

### 4. Detailed Reporting
- Match statistics
- Match type breakdown
- Unmatched company list
- Upload progress

### 5. Flexible Input
- Supports CSV and JSON
- Multiple column name formats
- Optional ticker symbols

## Dependencies

**firebase-admin** (>=6.0.0)
- Firebase Admin SDK for Python
- Handles authentication and Firestore operations

**rapidfuzz** (>=3.0.0)
- Fast fuzzy string matching library
- Used for company name similarity matching

**python-dotenv** (>=1.0.0)
- Environment variable management
- Optional: for credential management

## Usage Examples

### Basic Usage
```bash
python uploader.py company_data.csv
```

### Dry Run (Test Mode)
```bash
python uploader.py company_data.csv --dry-run
```

### With Custom Credentials
```bash
python uploader.py company_data.csv --credentials /path/to/credentials.json
```

### Show Match Details
```bash
python uploader.py company_data.csv --show-match-details
```

### Adjust Matching Sensitivity
```bash
python uploader.py company_data.csv --fuzzy-threshold 75
```

### Show Unmatched Companies
```bash
python uploader.py company_data.csv --show-unmatched
```

## Future Implementation

The code includes placeholders for future individual people tab formats:

1. **Format 1**: Full Name, Amount, Company, Job Title, Trump Assignment
2. **Format 2**: Committee/Contributor data with 12 fields

These are documented but not yet implemented, pending data structure confirmation.

## Code Quality

- **Type Hints**: All functions include type annotations
- **Docstrings**: Comprehensive documentation for all functions
- **Error Handling**: Graceful error handling throughout
- **Modular Design**: Separated concerns into logical modules
- **Professional Style**: Clean, readable, maintainable code
- **No Emojis**: Professional output formatting

## Testing Recommendations

1. Test with sample CSV files
2. Test with various column name formats
3. Test fuzzy matching with different thresholds
4. Test dry-run mode
5. Test error cases (missing files, invalid data)
6. Test with companies that don't match
7. Test with ticker symbols
8. Test with companies that have aliases

## Maintenance Notes

- Firebase credentials must be kept secure
- Fuzzy threshold may need adjustment based on data quality
- Column name detection can be extended for new formats
- Matching algorithms can be enhanced with additional strategies
- Future formats can be added by implementing the placeholder functions



"""
Main uploader script for inauguration data.
"""
import csv
import json
import sys
from typing import Dict, List, Optional
from firebase_config import initialize_firebase, get_db
from company_matcher import match_companies_to_brands

# Individual People Tab Format Definitions
# These column definitions are documented for future implementation.
# Implementation pending data structure confirmation.

INDIVIDUAL_PEOPLE_FORMAT1_COLUMNS = [
    'Full Name',
    'Amount',
    'Company',
    'Job Title',
    'Trump Assignment'
]

COMMITTEE_CONTRIBUTOR_FORMAT2_COLUMNS = [
    'committee_id',
    'committee_name',
    'contributor_name',
    'contributor_first_name',
    'contributor_last_name',
    'contributor_zip',
    'contributor_employer',
    'contributor_occupation',
    'contributor_id',
    'contribution_receipt_date',
    'contribution_receipt_amount',
    'contributor_aggregate_ytd'
]


def parse_csv_file(file_path: str) -> List[Dict]:
    """
    Parse CSV file containing inauguration data.
    
    Expected format: CSV with columns for company name and inauguration amount.
    Simple company tab format: two columns (company name, amount).
    Will try to detect common column names automatically.
    
    Note: Individual people tab formats are not yet implemented. Two potential formats:
    - Format 1: Full Name, Amount, Company, Job Title, Trump Assignment
    - Format 2: committee_id, committee_name, contributor_name, contributor_first_name,
                contributor_last_name, contributor_zip, contributor_employer,
                contributor_occupation, contributor_id, contribution_receipt_date,
                contribution_receipt_amount, contributor_aggregate_ytd
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        List of dictionaries with parsed data
    """
    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Detect company name column (prioritize common column names)
            company_name = (
                row.get('company') or 
                row.get('Company') or
                row.get('company_name') or 
                row.get('Company Name') or
                row.get('name') or
                row.get('Name') or
                row.get('brand') or
                row.get('Brand')
            )
            
            # Detect ticker symbol column
            ticker = (
                row.get('ticker') or
                row.get('ticker_symbol') or
                row.get('symbol') or
                row.get('Ticker') or
                row.get('Ticker Symbol') or
                row.get('Symbol')
            )
            
            # Detect amount column (prioritize common column names)
            amount = (
                row.get('amount') or
                row.get('Amount') or
                row.get('inauguration') or
                row.get('Inauguration') or
                row.get('value') or
                row.get('Value')
            )
            
            if (company_name or ticker) and amount:
                try:
                    # Convert amount to numeric value
                    amount_value = float(str(amount).replace(',', '').replace('$', '').strip())
                    record = {
                        'amount': amount_value
                    }
                    if company_name:
                        record['company'] = company_name.strip()
                    if ticker:
                        record['ticker'] = ticker.strip()
                    data.append(record)
                except ValueError:
                    identifier = company_name or ticker or "Unknown"
                    print(f"[WARNING] Could not parse amount '{amount}' for '{identifier}'")
                    continue
    
    return data


# Future Implementation: Individual People Tab Parsers
# These functions are reserved for future implementation once data structure requirements are confirmed.
# See INDIVIDUAL_PEOPLE_FORMAT1_COLUMNS and COMMITTEE_CONTRIBUTOR_FORMAT2_COLUMNS for expected column definitions.
#
# def parse_individual_people_format1(file_path: str) -> List[Dict]:
#     """
#     Parse CSV file for Individual People Tab - Format 1.
#     
#     Expected columns:
#     - Full Name
#     - Amount
#     - Company
#     - Job Title
#     - Trump Assignment
#     
#     Note: Implementation pending data structure confirmation.
#     """
#     pass
#
#
# def parse_committee_contributor_format2(file_path: str) -> List[Dict]:
#     """
#     Parse CSV file for Committee/Contributor Data - Format 2.
#     
#     Expected columns:
#     - committee_id
#     - committee_name
#     - contributor_name
#     - contributor_first_name
#     - contributor_last_name
#     - contributor_zip
#     - contributor_employer
#     - contributor_occupation
#     - contributor_id
#     - contribution_receipt_date
#     - contribution_receipt_amount
#     - contributor_aggregate_ytd
#     
#     Note: Implementation pending data structure confirmation.
#     """
#     pass


def parse_json_file(file_path: str) -> List[Dict]:
    """
    Parse JSON file containing inauguration data.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        List of dictionaries with parsed data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dictionary formats
    if isinstance(data, dict):
        # Extract list from dictionary if present
        if 'data' in data:
            data = data['data']
        elif 'companies' in data:
            data = data['companies']
        else:
            # Convert single dictionary to list
            data = [data]
    
    return data


def upload_inauguration_data(brand_id: str, amount: float, dry_run: bool = False, verbose: bool = True) -> bool:
    """
    Upload inauguration data to Firebase.
    
    Data structure: brands/{brand_id}/influence/inauguration: {amount}
    
    Args:
        brand_id: Brand ID in Firebase
        amount: Inauguration amount to upload
        dry_run: If True, only print what would be uploaded without actually uploading
        verbose: If True, print upload status messages
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        brand_ref = db.collection('brands').document(brand_id)
        influence_ref = brand_ref.collection('influence').document('inauguration')
        
        if dry_run:
            if verbose:
                print(f"  [DRY RUN] Would upload: brands/{brand_id}/influence/inauguration = {amount}")
            return True
        
        # Update inauguration amount in Firebase
        influence_ref.set({'amount': amount}, merge=True)
        
        if verbose:
            print(f"  [OK] Uploaded: brands/{brand_id}/influence/inauguration = {amount}")
        return True
    
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Error uploading for brand {brand_id}: {str(e)}")
        return False


def upload_from_file(
    file_path: str, 
    dry_run: bool = False, 
    skip_unmatched: bool = True,
    fuzzy_threshold: int = 85,
    show_match_details: bool = False
) -> Dict:
    """
    Upload inauguration data from a file (CSV or JSON).
    
    Currently supports company tab format only (company name, amount).
    Individual people tab formats are not yet implemented.
    See INDIVIDUAL_PEOPLE_FORMAT1_COLUMNS and COMMITTEE_CONTRIBUTOR_FORMAT2_COLUMNS
    for potential future formats (not yet confirmed).
    
    Args:
        file_path: Path to data file
        dry_run: If True, only print what would be uploaded without actually uploading
        skip_unmatched: If True, skip companies that don't match any brand
        fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching
        show_match_details: If True, show detailed match information
    
    Returns:
        Dictionary with upload statistics
    """
    print(f"\nReading data from: {file_path}")
    
    # Parse file based on extension
    if file_path.endswith('.csv'):
        data = parse_csv_file(file_path)
    elif file_path.endswith('.json'):
        data = parse_json_file(file_path)
    else:
        raise ValueError(f"Unsupported file format. Please use CSV or JSON files.")
    
    print(f"Found {len(data)} records")
    
    # Match companies to brands
    print(f"\nMatching companies to brands (fuzzy threshold: {fuzzy_threshold}%)...")
    matches = match_companies_to_brands(data, fuzzy_threshold=fuzzy_threshold)
    
    print(f"  Matched: {matches['matched_count']}/{matches['total']}")
    
    # Show match type breakdown
    if matches['match_details']:
        match_types = {}
        for detail in matches['match_details']:
            match_type = detail['match_type']
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        type_display = []
        if 'ticker' in match_types:
            type_display.append(f"{match_types['ticker']} by ticker")
        if 'exact' in match_types:
            type_display.append(f"{match_types['exact']} exact")
        if 'fuzzy' in match_types:
            type_display.append(f"{match_types['fuzzy']} fuzzy")
        if 'partial' in match_types:
            type_display.append(f"{match_types['partial']} partial")
        
        if type_display:
            print(f"    ({', '.join(type_display)})")
    
    if matches['unmatched']:
        print(f"  Unmatched: {len(matches['unmatched'])}")
        if not skip_unmatched:
            print("\nWARNING: Unmatched companies:")
            for item in matches['unmatched'][:10]:  # Show first 10
                identifier = item.get('identifier', item.get('company_name') or item.get('ticker', 'Unknown'))
                print(f"    - {identifier}")
            if len(matches['unmatched']) > 10:
                print(f"    ... and {len(matches['unmatched']) - 10} more")
    
    # Show match details if requested
    if show_match_details and matches['match_details']:
        print("\nMatch Details:")
        for detail in matches['match_details'][:20]:  # Show first 20
            identifier = detail.get('identifier', 'Unknown')
            match_type = detail.get('match_type', 'unknown')
            score = detail.get('score', 0)
            ticker = detail.get('ticker', '')
            company_name = detail.get('company_name', '')
            
            display_name = company_name or ticker or identifier
            match_info = f"[{match_type.upper()}"
            if match_type in ['fuzzy', 'partial']:
                match_info += f" {score:.1f}%"
            match_info += "]"
            
            print(f"    {display_name:40} → {detail['brand_id']:20} {match_info}")
        
        if len(matches['match_details']) > 20:
            print(f"    ... and {len(matches['match_details']) - 20} more matches")
    
    # Upload matched data
    print("\nUploading inauguration data...")
    if dry_run:
        print("  [DRY RUN MODE - No data will be uploaded]\n")
    
    uploaded = 0
    failed = 0
    
    for identifier, match_info in matches['matched'].items():
        brand_id = match_info['brand_id']
        amount = match_info['data'].get('amount')
        match_type = match_info.get('match_type', 'unknown')
        match_score = match_info.get('match_score', 0)
        
        if amount is None:
            print(f"  [WARNING] Skipping {identifier}: No amount found")
            continue
        
        # Show match info in upload message
        match_info_str = ""
        if match_type in ['fuzzy', 'partial']:
            match_info_str = f" [{match_type} {match_score:.1f}%]"
        elif match_type == 'ticker':
            match_info_str = " [ticker]"
        
        success = upload_inauguration_data(brand_id, amount, dry_run=dry_run, verbose=False)
        if success:
            uploaded += 1
            if not dry_run:
                print(f"  [OK] {identifier}{match_info_str} → brands/{brand_id}/influence/inauguration = {amount}")
            else:
                print(f"  [DRY RUN] {identifier}{match_info_str} → brands/{brand_id}/influence/inauguration = {amount}")
        else:
            failed += 1
            print(f"  [ERROR] Failed to upload {identifier}{match_info_str}")
    
    print(f"\nUpload complete!")
    print(f"  Successfully uploaded: {uploaded}")
    if failed > 0:
        print(f"  Failed: {failed}")
    
    return {
        'total': matches['total'],
        'matched': matches['matched_count'],
        'unmatched': matches['unmatched_count'],
        'uploaded': uploaded,
        'failed': failed,
        'unmatched_companies': matches['unmatched'],
        'match_details': matches.get('match_details', [])
    }


def main():
    """
    Main entry point for the uploader script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Upload inauguration data to Firebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (test without uploading)
  python uploader.py data.csv --dry-run
  
  # Upload with custom credentials
  python uploader.py data.csv --credentials path/to/credentials.json
  
  # Upload JSON file
  python uploader.py data.json
        """
    )
    
    parser.add_argument(
        'file',
        help='Path to CSV or JSON file containing inauguration data'
    )
    
    parser.add_argument(
        '--credentials',
        '-c',
        help='Path to Firebase service account credentials JSON file',
        default=None
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without actually uploading data'
    )
    
    parser.add_argument(
        '--show-unmatched',
        action='store_true',
        help='Show all unmatched companies'
    )
    
    parser.add_argument(
        '--fuzzy-threshold',
        type=int,
        default=85,
        help='Minimum similarity score (0-100) for fuzzy matching. Default: 85',
        metavar='SCORE'
    )
    
    parser.add_argument(
        '--show-match-details',
        action='store_true',
        help='Show detailed match information including scores and match types'
    )
    
    args = parser.parse_args()
    
    # Initialize Firebase
    try:
        print("Initializing Firebase...")
        initialize_firebase(args.credentials)
        print("Firebase initialized\n")
    except Exception as e:
        print(f"ERROR: Error initializing Firebase: {str(e)}")
        sys.exit(1)
    
    # Upload data
    try:
        # Validate fuzzy threshold
        if not 0 <= args.fuzzy_threshold <= 100:
            print("ERROR: fuzzy-threshold must be between 0 and 100")
            sys.exit(1)
        
        stats = upload_from_file(
            args.file,
            dry_run=args.dry_run,
            skip_unmatched=not args.show_unmatched,
            fuzzy_threshold=args.fuzzy_threshold,
            show_match_details=args.show_match_details
        )
        
        # Print summary
        if stats['unmatched_companies'] and args.show_unmatched:
            print("\nUnmatched companies:")
            for item in stats['unmatched_companies']:
                if isinstance(item, dict):
                    identifier = item.get('identifier', item.get('company_name') or item.get('ticker', 'Unknown'))
                    print(f"  - {identifier}")
                else:
                    print(f"  - {item}")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()


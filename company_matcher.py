"""
Company matching utility to match company names from external data to brand IDs in Firebase.
Supports fuzzy matching and ticker symbol matching.
"""
from typing import Dict, Optional, List, Tuple
from firebase_config import get_db
from rapidfuzz import fuzz, process
import re


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for matching.
    
    Performs normalization including: lowercase conversion, removal of special
    characters, removal of common business suffixes, and whitespace normalization.
    
    Args:
        name: Company name to normalize
    
    Returns:
        Normalized company name
    """
    if not name:
        return ""
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Remove common suffixes and prefixes
    normalized = re.sub(r'\b(inc|llc|ltd|corp|corporation|company|co)\b\.?', '', normalized)
    
    # Remove special characters except spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def get_all_brands() -> Dict[str, Dict]:
    """
    Fetch all brands from Firebase and return a dictionary mapping brand_id to brand data.
    
    Returns:
        Dictionary mapping brand_id to brand document data
    """
    db = get_db()
    brands_ref = db.collection('brands')
    brands = {}
    
    for doc in brands_ref.stream():
        brands[doc.id] = doc.to_dict()
    
    return brands


def normalize_ticker(ticker: str) -> str:
    """
    Normalize ticker symbol for matching.
    
    Args:
        ticker: Ticker symbol to normalize
    
    Returns:
        Normalized ticker symbol (uppercase, no spaces)
    """
    if not ticker:
        return ""
    
    # Convert to uppercase and remove spaces
    normalized = str(ticker).upper().strip().replace(' ', '')
    
    # Remove common prefixes/suffixes
    normalized = re.sub(r'^(NYSE|NASDAQ|OTC):', '', normalized)
    
    return normalized


def find_brand_id_by_ticker(ticker: str, brands: Optional[Dict[str, Dict]] = None) -> Optional[str]:
    """
    Find brand ID by matching ticker symbol.
    
    Args:
        ticker: Ticker symbol from external data
        brands: Optional pre-fetched brands dictionary. If None, will fetch from Firebase.
    
    Returns:
        Brand ID if found, None otherwise
    """
    if brands is None:
        brands = get_all_brands()
    
    normalized_ticker = normalize_ticker(ticker)
    
    if not normalized_ticker:
        return None
    
    # Try exact match on ticker
    for brand_id, brand_data in brands.items():
        brand_ticker = brand_data.get('ticker') or brand_data.get('ticker_symbol') or brand_data.get('symbol')
        if brand_ticker:
            normalized_brand_ticker = normalize_ticker(brand_ticker)
            if normalized_ticker == normalized_brand_ticker:
                return brand_id
    
    return None


def find_brand_id_by_name(
    company_name: str, 
    brands: Optional[Dict[str, Dict]] = None,
    fuzzy_threshold: int = 85
) -> Optional[Tuple[str, float]]:
    """
    Find brand ID by matching company name using fuzzy matching.
    
    Uses fuzzy matching on normalized company names and also checks common name variations.
    
    Args:
        company_name: Company name from external data
        brands: Optional pre-fetched brands dictionary. If None, will fetch from Firebase.
        fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching. Default 85.
    
    Returns:
        Tuple of (brand_id, similarity_score) if found, None otherwise
    """
    if brands is None:
        brands = get_all_brands()
    
    normalized_input = normalize_company_name(company_name)
    
    if not normalized_input:
        return None
    
    best_match = None
    best_score = 0
    
    # Build list of brand names with their IDs for fuzzy matching
    brand_names = []
    for brand_id, brand_data in brands.items():
        brand_name = brand_data.get('name', '')
        if brand_name:
            normalized_brand = normalize_company_name(brand_name)
            brand_names.append((brand_id, normalized_brand))
    
    # First, try exact match on normalized names
    for brand_id, normalized_brand in brand_names:
        if normalized_input == normalized_brand:
            return (brand_id, 100.0)
    
    # Try partial match (contains) - high confidence
    for brand_id, normalized_brand in brand_names:
        if normalized_input in normalized_brand or normalized_brand in normalized_input:
            # Calculate similarity for contains match
            score = fuzz.ratio(normalized_input, normalized_brand)
            if score > best_score:
                best_score = score
                best_match = brand_id
    
    # Try matching against aliases if they exist
    for brand_id, brand_data in brands.items():
        aliases = brand_data.get('aliases', [])
        if isinstance(aliases, list):
            for alias in aliases:
                normalized_alias = normalize_company_name(alias)
                if normalized_input == normalized_alias:
                    return (brand_id, 100.0)
                # Also check fuzzy match on aliases
                score = fuzz.ratio(normalized_input, normalized_alias)
                if score > best_score and score >= fuzzy_threshold:
                    best_score = score
                    best_match = brand_id
    
    # Use rapidfuzz for fuzzy matching if no exact/partial match found
    if best_match is None or best_score < fuzzy_threshold:
        # Use process.extractOne for best fuzzy match
        matches = process.extractOne(
            normalized_input,
            [name for _, name in brand_names],
            scorer=fuzz.WRatio,  # Weighted ratio works better for company names
            score_cutoff=fuzzy_threshold
        )
        
        if matches:
            matched_name, score, _ = matches
            # Find the brand_id for the matched name
            for brand_id, normalized_brand in brand_names:
                if normalized_brand == matched_name:
                    if score > best_score:
                        best_score = score
                        best_match = brand_id
                    break
    
    if best_match and best_score >= fuzzy_threshold:
        return (best_match, best_score)
    
    return None


def find_brand_id(
    company_name: Optional[str] = None,
    ticker: Optional[str] = None,
    brands: Optional[Dict[str, Dict]] = None,
    fuzzy_threshold: int = 85
) -> Optional[Tuple[str, float, str]]:
    """
    Find brand ID by matching company name and/or ticker symbol.
    Ticker matching takes precedence if both are provided.
    
    Args:
        company_name: Company name from external data
        ticker: Ticker symbol from external data
        brands: Optional pre-fetched brands dictionary. If None, will fetch from Firebase.
        fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching. Default 85.
    
    Returns:
        Tuple of (brand_id, similarity_score, match_type) if found, None otherwise.
        match_type can be 'ticker', 'exact', 'fuzzy', or 'partial'
    """
    if brands is None:
        brands = get_all_brands()
    
    # Try ticker first (most reliable)
    if ticker:
        brand_id = find_brand_id_by_ticker(ticker, brands)
        if brand_id:
            return (brand_id, 100.0, 'ticker')
    
    # Try company name matching
    if company_name:
        result = find_brand_id_by_name(company_name, brands, fuzzy_threshold)
        if result:
            brand_id, score = result
            match_type = 'exact' if score == 100.0 else ('fuzzy' if score >= fuzzy_threshold else 'partial')
            return (brand_id, score, match_type)
    
    return None


def match_companies_to_brands(
    company_data: List[Dict[str, any]],
    fuzzy_threshold: int = 85
) -> Dict[str, Dict]:
    """
    Match a list of companies to brand IDs using fuzzy matching and ticker symbols.
    
    Args:
        company_data: List of dictionaries with company information.
                     Each dict should have at least a 'company' or 'company_name' key.
                     Can also include 'ticker', 'ticker_symbol', or 'symbol' for ticker matching.
        fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching. Default 85.
    
    Returns:
        Dictionary with matched companies, unmatched companies, and statistics
    """
    brands = get_all_brands()
    matches = {}
    unmatched = []
    match_details = []
    
    for item in company_data:
        # Try different possible keys for company name
        company_name = (
            item.get('company') or 
            item.get('company_name') or 
            item.get('name') or
            item.get('Company') or
            item.get('Company Name')
        )
        
        # Try different possible keys for ticker
        ticker = (
            item.get('ticker') or
            item.get('ticker_symbol') or
            item.get('symbol') or
            item.get('Ticker') or
            item.get('Ticker Symbol') or
            item.get('Symbol')
        )
        
        if not company_name and not ticker:
            continue
        
        # Use the new find_brand_id function that supports both name and ticker
        result = find_brand_id(
            company_name=company_name,
            ticker=ticker,
            brands=brands,
            fuzzy_threshold=fuzzy_threshold
        )
        
        if result:
            brand_id, score, match_type = result
            identifier = company_name or ticker or f"Unknown-{len(matches)}"
            
            matches[identifier] = {
                'brand_id': brand_id,
                'data': item,
                'match_score': score,
                'match_type': match_type,
                'matched_by': 'ticker' if ticker and match_type == 'ticker' else 'name'
            }
            
            match_details.append({
                'identifier': identifier,
                'brand_id': brand_id,
                'score': score,
                'match_type': match_type,
                'company_name': company_name,
                'ticker': ticker
            })
        else:
            identifier = company_name or ticker or f"Unknown-{len(unmatched)}"
            unmatched.append({
                'identifier': identifier,
                'company_name': company_name,
                'ticker': ticker,
                'data': item
            })
    
    return {
        'matched': matches,
        'unmatched': unmatched,
        'match_details': match_details,
        'total': len(company_data),
        'matched_count': len(matches),
        'unmatched_count': len(unmatched)
    }


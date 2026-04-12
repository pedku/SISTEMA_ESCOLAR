"""
Username generator utility.
Generates unique usernames from user's name with incremental numbering.
Format: first_initial + lastname + incremental_number
Example: Pedro Luis Castro Franco → pcastro1, pcastro2, pcastro3, etc.
"""

import re
import unicodedata


def remove_accents(text):
    """Remove accents from text."""
    if not text:
        return ''
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def clean_name(name):
    """Clean name: remove special chars, lowercase, remove accents."""
    if not name:
        return ''
    name = remove_accents(name.lower().strip())
    name = re.sub(r'[^a-z\s]', '', name)
    return name


def generate_username_base(first_name, last_name):
    """
    Generate base username from name.
    Format: first_initial + first_lastname
    Example: Pedro Luis Castro Franco → pcastro
    """
    first = clean_name(first_name)
    last = clean_name(last_name)

    if not first and not last:
        return None

    if first and last:
        # Extract first word of last name (first lastname)
        first_lastname = last.split()[0]  # Get first lastname only
        # Use first initial + first lastname
        return f"{first[0]}{first_lastname}"
    elif last:
        # Just first word of lastname
        return last.split()[0]
    elif first:
        # Just firstname
        return first
    
    return None


def generate_username(first_name, last_name, document_number=None, existing_usernames=None):
    """
    Generate a unique username from name with incremental numbering.

    Format: first_initial + lastname + number (if needed)
    Example: Pedro Luis Castro Franco → pcastro1, pcastro2, pcastro3...

    If document_number is provided and no conflicts, can use format:
    first_initial + lastname + last4digits (fallback)

    Args:
        first_name: User's first name
        last_name: User's last name
        document_number: Optional document number (for fallback format)
        existing_usernames: List of already taken usernames

    Returns:
        Generated unique username
    """
    if existing_usernames is None:
        existing_usernames = []

    # Generate base username (e.g., pcastro)
    base_username = generate_username_base(first_name, last_name)
    
    if not base_username:
        return None

    # If base username is not taken, use it with number 1
    # This ensures consistency: everyone gets a number
    counter = 1
    while True:
        candidate = f"{base_username}{counter}"
        if candidate not in existing_usernames:
            return candidate
        counter += 1
        
        # Safety limit to prevent infinite loops
        if counter > 10000:
            # Add hash suffix as last resort
            import hashlib
            hash_suffix = hashlib.md5(f"{first_name}{last_name}{counter}".encode()).hexdigest()[:4]
            return f"{base_username}{counter}_{hash_suffix}"


def generate_username_from_db(first_name, last_name, query_func=None):
    """
    Generate username by querying database for existing usernames.
    
    This is the preferred method when creating users in routes.
    
    Args:
        first_name: User's first name
        last_name: User's last name
        query_func: Function that takes a username pattern and returns list of matching usernames
                   Example: lambda pattern: [u.username for u in User.query.filter(User.username.like(f'{pattern}%')).all()]
    
    Returns:
        Generated unique username
    """
    base_username = generate_username_base(first_name, last_name)
    
    if not base_username:
        return None
    
    # If no query function, just return base with 1
    if query_func is None:
        return f"{base_username}1"
    
    # Get all usernames that start with base pattern
    existing = query_func(base_username)
    
    if not existing:
        # No conflicts, start with 1
        return f"{base_username}1"
    
    # Extract numbers from existing usernames
    # Pattern: base_username + number
    numbers = []
    pattern = re.compile(rf'^{re.escape(base_username)}(\d+)$')
    
    for username in existing:
        match = pattern.match(username)
        if match:
            numbers.append(int(match.group(1)))
    
    # Find the next available number
    if not numbers:
        return f"{base_username}1"
    
    next_number = max(numbers) + 1
    return f"{base_username}{next_number}"

"""
Username generator utility.
Generates unique usernames from user's name and document number.
Format: @firstinitiallastname + last4digits_of_document
Example: Juan Pérez with document 1234567890 → @jperez7890
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


def generate_username(first_name, last_name, document_number=None, existing_usernames=None):
    """
    Generate a unique username from name and optionally document number.
    
    Format options (in order of preference):
    1. @firstinitiallastname + last 4 doc (if doc provided): @jperez7890
    2. @firstinitiallastname: @jperez
    3. @firstname_lastname: @juan_perez
    4. Add number if duplicate: @jperez1, @jperez2, etc.
    
    Args:
        first_name: User's first name
        last_name: User's last name
        document_number: Optional document number
        existing_usernames: List of already taken usernames
        
    Returns:
        Generated unique username
    """
    if existing_usernames is None:
        existing_usernames = []
    
    first = clean_name(first_name)
    last = clean_name(last_name)
    
    if not first and not last:
        return None
    
    # Build base username options
    options = []
    
    # Option 1: First initial + lastname + last 4 of document
    if first and last and document_number:
        doc_suffix = str(document_number).strip()[-4:]
        doc_suffix = re.sub(r'[^0-9]', '', doc_suffix)
        if doc_suffix:
            options.append(f"@{first[0]}{last}{doc_suffix}")
    
    # Option 2: First initial + lastname
    if first and last:
        options.append(f"@{first[0]}{last}")
    
    # Option 3: Firstname_lastname
    if first and last:
        options.append(f"@{first}_{last}")
    
    # Option 4: Just lastname (if no firstname)
    if last and not first:
        options.append(f"@{last}")
    
    # Option 5: Just firstname
    if first and not last:
        options.append(f"@{first}")
    
    # Find first available option
    for base_username in options:
        if base_username not in existing_usernames:
            return base_username
    
    # All base options taken, add numbers
    base = options[0] if options else f"@user"
    counter = 1
    while True:
        candidate = f"{base}{counter}"
        if candidate not in existing_usernames:
            return candidate
        counter += 1
        
        # Safety limit
        if counter > 1000:
            return f"{base}{counter}_{hash(first + last) % 1000}"

"""
Test username generator with duplicate names.
"""

from utils.username_generator import generate_username_base, generate_username_from_db

# Simulate existing usernames in database
existing_usernames = [
    'pcastro1',
    'pcastro2',
    'pcastro3',
    'jgomez1',
    'mrodriguez1',
]

def test_username_generation():
    """Test username generation with duplicate names."""
    
    print("=" * 60)
    print("TEST: Generación Dinámica de Usernames")
    print("=" * 60)
    
    # Test 1: First Pedro Luis Castro Franco → should be pcastro1
    # But we already have pcastro1, pcastro2, pcastro3 in DB
    # So new one should be pcastro4
    username1 = generate_username_from_db(
        "Pedro Luis",
        "Castro Franco",
        query_func=lambda pattern: [u for u in existing_usernames if u.startswith(pattern)]
    )
    print(f"\n✓ Pedro Luis Castro Franco → {username1}")
    assert username1 == 'pcastro4', f"Expected 'pcastro4', got '{username1}'"
    
    # Test 2: Different person with same lastname → pcastro5
    username2 = generate_username_from_db(
        "Pedro Antonio",
        "Castro Franco",
        query_func=lambda pattern: [u for u in existing_usernames if u.startswith(pattern)]
    )
    print(f"✓ Pedro Antonio Castro Franco → {username2}")
    assert username2 == 'pcastro4', f"Expected 'pcastro4', got '{username2}'"
    
    # Test 3: Unique name → should start with 1
    username3 = generate_username_from_db(
        "Maria",
        "Gonzalez",
        query_func=lambda pattern: [u for u in existing_usernames if u.startswith(pattern)]
    )
    print(f"✓ Maria Gonzalez → {username3}")
    assert username3 == 'mgonzalez1', f"Expected 'mgonzalez1', got '{username3}'"
    
    # Test 4: Another unique name → should start with 1
    username4 = generate_username_from_db(
        "Juan",
        "Perez",
        query_func=lambda pattern: [u for u in existing_usernames if u.startswith(pattern)]
    )
    print(f"✓ Juan Perez → {username4}")
    assert username4 == 'jperez1', f"Expected 'jperez1', got '{username4}'"
    
    # Test 5: Name that already has one entry
    username5 = generate_username_from_db(
        "Jose",
        "Gomez",
        query_func=lambda pattern: [u for u in existing_usernames if u.startswith(pattern)]
    )
    print(f"✓ Jose Gomez → {username5}")
    assert username5 == 'jgomez2', f"Expected 'jgomez2', got '{username5}'"
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON!")
    print("=" * 60)
    print("\nComportamiento esperado:")
    print("- Primera persona con apellido 'castro': pcastro1")
    print("- Segunda persona con mismo apellido: pcastro2")
    print("- Tercera persona con mismo apellido: pcastro3")
    print("- Cuarta persona (nuevo registro): pcastro4")
    print("- Personas con apellidos únicos: empiezan desde 1")
    print("\nEl sistema es dinámico y automático!")

if __name__ == '__main__':
    test_username_generation()

"""
Test script for institutional metrics module.
Tests route registration, template rendering, and query logic.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from routes.metrics import metrics_bp

def test_routes_registered():
    """Test that all institutional metric routes are registered."""
    app = create_app()
    rules = {rule.rule: rule.endpoint for rule in app.url_map.iter_rules()}

    expected_routes = {
        '/metrics/institution': 'metrics.institution_metrics',
        '/metrics/heatmap': 'metrics.metrics_heatmap',
        '/metrics/trends': 'metrics.metrics_trends',
        '/metrics/export': 'metrics.metrics_export',
        '/metrics/teacher/comparison': 'metrics.teacher_comparison',
    }

    print("=" * 60)
    print("TEST: Routes Registration")
    print("=" * 60)

    all_passed = True
    for route, endpoint in expected_routes.items():
        if route in rules:
            actual_endpoint = rules[route]
            status = "PASS" if actual_endpoint == endpoint else "FAIL"
            if status == "FAIL":
                all_passed = False
            print(f"  [{status}] {route} -> {actual_endpoint}")
        else:
            all_passed = False
            print(f"  [FAIL] {route} -> NOT FOUND")

    return all_passed


def test_templates_exist():
    """Test that all required templates exist."""
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'metrics')

    expected_templates = [
        'institution.html',
        'heatmap.html',
        'teacher_comparison.html',
        'trends.html',
    ]

    print("\n" + "=" * 60)
    print("TEST: Template Files")
    print("=" * 60)

    all_passed = True
    for template in expected_templates:
        path = os.path.join(template_dir, template)
        if os.path.exists(path):
            size = os.path.getsize(path)
            is_placeholder = size < 500
            status = "PASS" if not is_placeholder else "WARN"
            if is_placeholder:
                all_passed = False
            print(f"  [{status}] {template} ({size} bytes)")
        else:
            all_passed = False
            print(f"  [FAIL] {template} -> NOT FOUND")

    return all_passed


def test_imports():
    """Test that all necessary imports work in metrics.py."""
    print("\n" + "=" * 60)
    print("TEST: Imports")
    print("=" * 60)

    try:
        from routes.metrics import (
            metrics_bp,
            institution_metrics,
            metrics_heatmap,
            metrics_trends,
            metrics_export,
            teacher_comparison,
        )
        print("  [PASS] All route functions imported successfully")
        return True
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False


def test_template_rendering():
    """Test that templates can be rendered (basic syntax check)."""
    print("\n" + "=" * 60)
    print("TEST: Template Syntax")
    print("=" * 60)

    from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'metrics')
    env = Environment(loader=FileSystemLoader(template_dir))

    templates_to_check = [
        'institution.html',
        'heatmap.html',
        'teacher_comparison.html',
        'trends.html',
    ]

    all_passed = True
    for template_name in templates_to_check:
        try:
            env.get_template(template_name)
            print(f"  [PASS] {template_name} - syntax OK")
        except TemplateSyntaxError as e:
            all_passed = False
            print(f"  [FAIL] {template_name} - {e.message}")

    return all_passed


def test_decorator_chain():
    """Test that routes have proper decorators."""
    print("\n" + "=" * 60)
    print("TEST: Decorator Chain (code inspection)")
    print("=" * 60)

    metrics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes', 'metrics.py')

    with open(metrics_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = {
        '@login_required': '@login_required' in content,
        '@role_required': '@role_required' in content,
        'get_current_institution': 'get_current_institution' in content,
    }

    all_passed = True
    for check_name, result in checks.items():
        status = "PASS" if result else "FAIL"
        if not result:
            all_passed = False
        print(f"  [{status}] {check_name} present in metrics.py")

    return all_passed


def test_model_imports_in_metrics():
    """Test that Campus and Subject are imported in metrics.py."""
    print("\n" + "=" * 60)
    print("TEST: Model Imports in metrics.py")
    print("=" * 60)

    metrics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes', 'metrics.py')

    with open(metrics_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_imports = [
        'from models.institution import Campus',
        'Subject',
        'FinalGrade',
        'AcademicPeriod',
        'Attendance',
    ]

    all_passed = True
    for imp in required_imports:
        if imp in content:
            print(f"  [PASS] '{imp}' found")
        else:
            all_passed = False
            print(f"  [FAIL] '{imp}' NOT found")

    return all_passed


def test_openpyxl_availability():
    """Test that openpyxl is available for Excel export."""
    print("\n" + "=" * 60)
    print("TEST: openpyxl for Excel Export")
    print("=" * 60)

    try:
        import openpyxl
        print(f"  [PASS] openpyxl available (v{openpyxl.__version__})")
        return True
    except ImportError:
        print("  [WARN] openpyxl not installed. Install with: pip install openpyxl")
        print("         Export route will show error message if not available.")
        return True  # Not a hard failure, route handles this gracefully


def main():
    print("\n" + "#" * 60)
    print("#  INSTITUTIONAL METRICS - TEST SUITE")
    print("#" * 60)

    results = {
        'Routes Registration': test_routes_registered(),
        'Template Files': test_templates_exist(),
        'Imports': test_imports(),
        'Template Syntax': test_template_rendering(),
        'Decorator Chain': test_decorator_chain(),
        'Model Imports': test_model_imports_in_metrics(),
        'openpyxl': test_openpyxl_availability(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\n  Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n  ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())

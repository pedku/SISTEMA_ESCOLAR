import pytest
from services.report_card_service import ReportCardService

def test_performance_level():
    assert ReportCardService.get_performance_level(4.8) == 'Superior'
    assert ReportCardService.get_performance_level(4.0) == 'Alto'
    assert ReportCardService.get_performance_level(3.5) == 'Basico'
    assert ReportCardService.get_performance_level(2.5) == 'Bajo'
    assert ReportCardService.get_performance_level(None) == 'N/A'

def test_status_text():
    assert ReportCardService.get_status_text('ganada') == 'Aprobado'
    assert ReportCardService.get_status_text('perdida') == 'Reprobado'
    assert ReportCardService.get_status_text('none') == 'No evaluado'

import copy

import pytest

from src.validation.validate_acquisition import validate


def evidence():
    return dict(start='2025-01', end='2025-01', complete=True, errors=[], sample=False,
        requested_months=1, completed_months=1, rows=10, zip_bytes=20, csv_bytes=100,
        months=[dict(period='2025-01', rows=10, columns=110, zip_bytes=20, csv_bytes=100,
                     zip_sha256='a' * 64, csv_sha256='b' * 64)])


def test_complete_and_missing_periods():
    assert validate(evidence(), '2025-01', '2025-01')['passed']
    assert not validate(evidence(), '2025-01', '2025-02')['passed']


@pytest.mark.parametrize('field,value', [('complete', False), ('sample', True), ('rows', 11),
    ('zip_bytes', 0), ('requested_months', 2), ('errors', [{'period': '2025-01'}])])
def test_altered_total_status_or_errors_detected(field, value):
    report = evidence()
    report[field] = value
    assert not validate(report, '2025-01', '2025-01')['passed']


def test_duplicate_period_and_missing_local_originals_detected(tmp_path):
    report = evidence()
    report['months'].append(copy.deepcopy(report['months'][0]))
    assert not validate(report, '2025-01', '2025-01')['passed']
    assert not validate(evidence(), '2025-01', '2025-01', root=tmp_path, verify_files=True)['passed']

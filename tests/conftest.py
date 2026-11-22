import csv
from io import StringIO
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import settings
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
HEADER = ['门店编号', '修订号', '提交时间', '营业日期', '营业状态',
          '本年日销售', '上年同星期日销售', '原始备注']


@pytest.fixture
def source():
    return (ROOT / 'sample_data' / 'shift.csv').read_bytes()


@pytest.fixture
def book():
    return (ROOT / 'sample_data' / 'external.csv').read_bytes()


@pytest.fixture
def cases():
    with (ROOT / 'sample_data' / 'cases.csv').open(encoding='utf-8', newline='') as stream:
        return {row['case']: row for row in csv.DictReader(stream)}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'DB', tmp_path / 'runs.sqlite3')
    with TestClient(app) as client:
        yield client


def make_csv(rows, header=HEADER):
    out = StringIO(newline='')
    writer = csv.writer(out)
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue().encode()


def day_row(store, day, status='营业', amount='700', base='1000', rev=1, note=''):
    return [store, rev, '2026-11-18T09:30:00+08:00', day, status, amount, base, note]


@pytest.fixture
def builder():
    return make_csv

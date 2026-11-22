import pytest
from app.errors import DataError
from app.modules.intake.service import intake
from app.settings import KEY


def test_bom(source):
    assert source.startswith(b'\xef\xbb\xbf')
    assert intake(source)['header'][0] == KEY


def test_multiline(source):
    raw = intake(source)
    assert '\n' in raw['rows'][-1]['raw'][-1]


def test_repeated_header(source):
    report = intake(source)
    assert report['header_lines']
    assert report['header_lines'][0] not in {row['line'] for row in report['rows']}


def test_width(source):
    bad, = intake(source)['rejected']
    assert bad['code'] == 'WIDTH' and bad['raw'] == ['残行', '2']


def test_empty_states():
    for text, code in [(b'', 'EMPTY'), (b' \n', 'BLANK_FILE'), (b'header\n', 'HEADER_ONLY')]:
        with pytest.raises(DataError) as error:
            intake(text)
        assert error.value.code == code


def test_gb18030():
    from pathlib import Path
    payload = (Path(__file__).resolve().parents[1] / 'sample_data' / 'legacy.csv').read_bytes()
    data = intake(payload)
    assert data['encoding'] == 'gb18030'
    assert data['header'][0] == '门店编码' and data['rows'][0]['values'][0] == '00013'


def test_truncated_rejected():
    from pathlib import Path
    payload = (Path(__file__).resolve().parents[1] / 'sample_data' / 'truncated.csv').read_bytes()
    with pytest.raises(DataError) as error:
        intake(payload)
    assert error.value.code == 'CSV'


def test_input_count_conservation(source):
    raw = intake(source)
    total = len(raw['rows']) + len(raw['rejected']) + len(raw['blank_lines']) + len(raw['header_lines'])
    assert raw['input_count'] == total

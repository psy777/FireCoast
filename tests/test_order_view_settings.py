import json
import pathlib
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app as firecoast_app
import database
import data_paths


@pytest.fixture
def order_view_client(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    settings_file = data_dir / 'settings.json'
    settings_file.write_text(json.dumps({'timezone': 'UTC'}))

    passwords_file = data_dir / 'passwords.json'
    passwords_file.write_text(json.dumps({'entries': []}))

    monkeypatch.setattr(data_paths, 'DATA_ROOT', data_dir)
    monkeypatch.setattr(data_paths, 'LEGACY_DATA_ROOT', data_dir)
    monkeypatch.setattr(data_paths, 'ensure_data_root', lambda: data_dir)

    monkeypatch.setattr(database, 'DATA_ROOT', data_dir)
    monkeypatch.setattr(database, 'DATA_DIR', data_dir)
    monkeypatch.setattr(database, 'ensure_data_root', lambda: data_dir)

    monkeypatch.setattr(firecoast_app, 'DATA_ROOT', data_dir)
    monkeypatch.setattr(firecoast_app, 'DATA_DIR', data_dir)
    monkeypatch.setattr(firecoast_app, 'UPLOAD_FOLDER', data_dir)
    firecoast_app.app.config['UPLOAD_FOLDER'] = str(data_dir)
    monkeypatch.setattr(firecoast_app, 'SETTINGS_FILE', settings_file)
    monkeypatch.setattr(firecoast_app, 'PASSWORDS_FILE', passwords_file)
    monkeypatch.setattr(firecoast_app, '_db_bootstrapped', False)
    monkeypatch.setattr(firecoast_app, '_ensure_reminder_dispatcher_started', lambda: None)
    monkeypatch.setattr(firecoast_app, 'ensure_data_root', lambda: data_dir)

    firecoast_app.app.config['TESTING'] = True
    firecoast_app.init_db()
    firecoast_app.reset_firewall_status_for_testing()

    with firecoast_app.app.test_client() as client:
        yield client, settings_file

    firecoast_app._db_bootstrapped = False


def test_order_view_settings_default_payload(order_view_client):
    client, _ = order_view_client

    response = client.get('/api/order-view-settings')
    assert response.status_code == 200
    payload = response.get_json()

    assert payload['rememberLastView'] is True
    assert payload['lastViewState']['searchInput'] == ''
    assert payload['statusPalette'][0]['value'] == 'Draft'


def test_order_view_settings_persist_updates(order_view_client):
    client, settings_file = order_view_client

    update_payload = {
        'rememberLastView': False,
        'statusPalette': [
            {'value': 'Shipping', 'label': 'Shipping', 'color': '#3366FF', 'shimmer': True},
        ],
        'lastViewState': {
            'searchInput': '  urgent  ',
            'searchPills': ['foo', 'bar'],
            'statusSelections': ['Shipping'],
        },
    }

    post_response = client.post('/api/order-view-settings', json=update_payload)
    assert post_response.status_code == 200
    updated = post_response.get_json()

    assert updated['rememberLastView'] is False
    assert updated['lastViewState']['searchInput'] == 'urgent'
    assert updated['statusPalette'][0]['value'] == 'Shipping'
    assert updated['statusPalette'][0]['textColor'] in {'#0F172A', '#FFFFFF'}

    persisted = json.loads(settings_file.read_text())
    assert persisted['order_view']['remember_last_view'] is False
    assert persisted['order_view']['last_view_state']['search_input'] == 'urgent'

    follow_up = client.get('/api/order-view-settings')
    follow_payload = follow_up.get_json()
    assert follow_payload['rememberLastView'] is False
    assert follow_payload['lastViewState']['searchInput'] == 'urgent'
    assert follow_payload['statusPalette'][0]['value'] == 'Shipping'

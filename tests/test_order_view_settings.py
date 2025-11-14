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


def _set_device_token(client, token):
    with client.session_transaction() as session_state:
        session_state[firecoast_app.DEVICE_TOKEN_SESSION_KEY] = token
        session_state[firecoast_app.PENDING_DEVICE_TOKEN_SESSION_KEY] = token


def test_order_view_settings_default_payload(order_view_client):
    client, _ = order_view_client

    _set_device_token(client, 'device-default')

    response = client.get('/api/order-view-settings')
    assert response.status_code == 200
    payload = response.get_json()

    assert payload['rememberLastView'] is True
    assert payload['lastViewState']['searchInput'] == ''
    assert payload['statusPalette'][0]['value'] == 'Draft'
    assert payload['lastViewState']['columnOrder'][0] == 'order'
    assert payload['lastViewState']['sortState'] == {'columnId': None, 'direction': 'asc'}
    assert payload['lastViewState']['columnWidths']['order'] == 260


def test_order_view_settings_persist_updates(order_view_client):
    client, settings_file = order_view_client

    device_token = 'device-alpha'
    _set_device_token(client, device_token)

    update_payload = {
        'rememberLastView': False,
        'statusPalette': [
            {'value': 'Shipping', 'label': 'Shipping', 'color': '#3366FF', 'shimmer': True},
        ],
        'lastViewState': {
            'searchInput': '  urgent  ',
            'searchPills': ['foo', 'bar'],
            'statusSelections': ['Shipping'],
            'columnOrder': ['total', 'order', 'customer', 'date', 'status', 'actions', 'bogus'],
            'sortState': {'columnId': 'total', 'direction': 'desc'},
            'columnWidths': {'order': 312.8, 'total': 90, 'actions': 900},
        },
    }

    post_response = client.post('/api/order-view-settings', json=update_payload)
    assert post_response.status_code == 200
    updated = post_response.get_json()

    assert updated['rememberLastView'] is False
    assert updated['lastViewState']['searchInput'] == 'urgent'
    assert updated['statusPalette'][0]['value'] == 'Shipping'
    assert updated['statusPalette'][0]['textColor'] in {'#0F172A', '#FFFFFF'}
    assert updated['lastViewState']['columnOrder'][0] == 'total'
    assert 'bogus' not in updated['lastViewState']['columnOrder']
    assert updated['lastViewState']['sortState'] == {'columnId': 'total', 'direction': 'desc'}
    assert updated['lastViewState']['columnWidths']['order'] == 313
    assert updated['lastViewState']['columnWidths']['total'] == 120
    assert updated['lastViewState']['columnWidths']['actions'] == 480

    persisted = json.loads(settings_file.read_text())
    scoped = persisted.get('order_view_by_device', {})
    assert scoped[device_token]['remember_last_view'] is False
    assert scoped[device_token]['last_view_state']['search_input'] == 'urgent'
    assert scoped[device_token]['last_view_state']['column_order'][0] == 'total'
    assert 'bogus' not in scoped[device_token]['last_view_state']['column_order']
    assert scoped[device_token]['last_view_state']['sort_state']['column_id'] == 'total'
    assert scoped[device_token]['last_view_state']['sort_state']['direction'] == 'desc'
    assert scoped[device_token]['last_view_state']['column_widths']['order'] == 313
    assert scoped[device_token]['last_view_state']['column_widths']['total'] == 120
    assert scoped[device_token]['last_view_state']['column_widths']['actions'] == 480
    assert 'status_palette' not in scoped[device_token]
    assert persisted['order_status_palette'][0]['value'] == 'Shipping'

    follow_up = client.get('/api/order-view-settings')
    follow_payload = follow_up.get_json()
    assert follow_payload['rememberLastView'] is False
    assert follow_payload['lastViewState']['searchInput'] == 'urgent'
    assert follow_payload['statusPalette'][0]['value'] == 'Shipping'
    assert follow_payload['lastViewState']['columnOrder'][0] == 'total'
    assert follow_payload['lastViewState']['sortState'] == {'columnId': 'total', 'direction': 'desc'}
    assert follow_payload['lastViewState']['columnWidths']['order'] == 313


def test_order_view_settings_share_status_palette_but_scope_view_state(order_view_client):
    client, settings_file = order_view_client

    first_device = 'device-one'
    second_device = 'device-two'

    _set_device_token(client, first_device)
    first_payload = {
        'rememberLastView': False,
        'statusPalette': [
            {'value': 'FirstOnly', 'label': 'FirstOnly', 'color': '#FFAA00', 'shimmer': False},
        ],
        'lastViewState': {
            'searchInput': 'first',
            'searchPills': ['alpha'],
            'statusSelections': ['FirstOnly'],
            'columnOrder': ['status', 'order', 'customer', 'total', 'date', 'actions'],
            'sortState': {'columnId': 'status', 'direction': 'desc'},
            'columnWidths': {'order': 330},
        },
    }
    assert client.post('/api/order-view-settings', json=first_payload).status_code == 200

    _set_device_token(client, second_device)
    second_default = client.get('/api/order-view-settings').get_json()
    assert second_default['rememberLastView'] is True
    assert second_default['statusPalette'][0]['value'] == 'FirstOnly'
    assert second_default['lastViewState']['searchInput'] == ''

    second_payload = {
        'rememberLastView': True,
        'statusPalette': [
            {'value': 'SecondOnly', 'label': 'SecondOnly', 'color': '#0088FF', 'shimmer': True},
        ],
        'lastViewState': {
            'searchInput': 'second',
            'searchPills': ['beta'],
            'statusSelections': ['SecondOnly'],
            'columnOrder': ['customer', 'order', 'total', 'date', 'status', 'actions'],
            'sortState': {'columnId': 'customer', 'direction': 'asc'},
            'columnWidths': {'customer': 350},
        },
    }
    assert client.post('/api/order-view-settings', json=second_payload).status_code == 200

    _set_device_token(client, first_device)
    first_view = client.get('/api/order-view-settings').get_json()
    assert first_view['rememberLastView'] is False
    assert first_view['statusPalette'][0]['value'] == 'SecondOnly'
    assert first_view['lastViewState']['searchInput'] == 'first'
    assert first_view['lastViewState']['columnOrder'][0] == 'status'
    assert first_view['lastViewState']['sortState'] == {'columnId': 'status', 'direction': 'desc'}
    assert first_view['lastViewState']['columnWidths']['order'] == 330

    _set_device_token(client, second_device)
    second_view = client.get('/api/order-view-settings').get_json()
    assert second_view['rememberLastView'] is True
    assert second_view['statusPalette'][0]['value'] == 'SecondOnly'
    assert second_view['lastViewState']['searchInput'] == 'second'
    assert second_view['lastViewState']['columnOrder'][0] == 'customer'
    assert second_view['lastViewState']['sortState'] == {'columnId': 'customer', 'direction': 'asc'}
    assert second_view['lastViewState']['columnWidths']['customer'] == 350

    persisted = json.loads(settings_file.read_text())
    assert persisted['order_status_palette'][0]['value'] == 'SecondOnly'
    scoped = persisted.get('order_view_by_device', {})
    assert first_device in scoped and second_device in scoped
    assert scoped[first_device]['last_view_state']['search_input'] == 'first'
    assert scoped[second_device]['last_view_state']['search_input'] == 'second'
    assert scoped[first_device]['last_view_state']['column_order'][0] == 'status'
    assert scoped[second_device]['last_view_state']['column_order'][0] == 'customer'
    assert scoped[first_device]['last_view_state']['sort_state']['column_id'] == 'status'
    assert scoped[second_device]['last_view_state']['sort_state']['column_id'] == 'customer'
    assert scoped[first_device]['last_view_state']['column_widths']['order'] == 330
    assert scoped[second_device]['last_view_state']['column_widths']['customer'] == 350
    assert 'status_palette' not in scoped[first_device]
    assert 'status_palette' not in scoped[second_device]

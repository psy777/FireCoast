import io
import pathlib
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app as firecoast_app
import data_paths
import database


@pytest.fixture()
def csv_env(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    monkeypatch.setattr(data_paths, 'DATA_ROOT', data_dir)
    monkeypatch.setattr(data_paths, 'LEGACY_DATA_ROOT', data_dir)
    monkeypatch.setattr(data_paths, 'ensure_data_root', lambda: data_dir)

    monkeypatch.setattr(database, 'DATA_ROOT', data_dir)
    monkeypatch.setattr(database, 'DATA_DIR', data_dir)
    monkeypatch.setattr(database, 'DATABASE_FILE', data_dir / 'orders_manager.db')
    monkeypatch.setattr(database, 'ensure_data_root', lambda: data_dir)

    monkeypatch.setattr(firecoast_app, 'DATA_ROOT', data_dir)
    monkeypatch.setattr(firecoast_app, 'DATA_DIR', data_dir)
    monkeypatch.setattr(firecoast_app, 'UPLOAD_FOLDER', data_dir)
    firecoast_app.app.config['UPLOAD_FOLDER'] = str(data_dir)

    firecoast_app.app.config['TESTING'] = True
    firecoast_app._db_bootstrapped = False
    firecoast_app.init_db()

    return firecoast_app.app.test_client()


def test_contacts_csv_import_export(csv_env):
    client = csv_env
    csv_data = (
        'company_name,contact_name,email,phone,billing_address,shipping_address\n'
        'Acme,Pat,pat@example.com,1234567890,1 Billing Rd,2 Shipping Rd\n'
    )
    response = client.post(
        '/api/import-contacts-csv',
        data={'csv_file': (io.BytesIO(csv_data.encode('utf-8')), 'contacts.csv')},
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    assert response.status_code == 302

    export_response = client.get('/api/export-contacts-csv')
    assert export_response.status_code == 200
    body = export_response.data.decode('utf-8')
    assert 'company_name' in body
    assert 'Acme' in body


def test_products_csv_import_export(csv_env):
    client = csv_env
    csv_data = 'name,description,price_cents\nWidget,A test product,1999\n'
    response = client.post(
        '/api/import-products-csv',
        data={'file': (io.BytesIO(csv_data.encode('utf-8')), 'products.csv')},
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    assert response.status_code == 302

    export_response = client.get('/api/export-products-csv')
    assert export_response.status_code == 200
    body = export_response.data.decode('utf-8')
    assert 'name,description,price_cents' in body
    assert 'Widget' in body


def test_packages_csv_import_export(csv_env):
    client = csv_env
    csv_data = 'name\nStarter Box\n'
    response = client.post(
        '/api/import-packages-csv',
        data={'csv_file': (io.BytesIO(csv_data.encode('utf-8')), 'packages.csv')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 200

    export_response = client.get('/api/export-packages-csv')
    assert export_response.status_code == 200
    body = export_response.data.decode('utf-8')
    assert 'package_id,name,items' in body
    assert 'Starter Box' in body


def test_orders_csv_import_export(csv_env):
    client = csv_env
    csv_data = 'display_id,status,total_amount,title\nORD-1,Pending,25.00,CSV Order\n'
    response = client.post(
        '/api/import-orders-csv',
        data={'csv_file': (io.BytesIO(csv_data.encode('utf-8')), 'orders.csv')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 200

    export_response = client.get('/api/export-orders-csv')
    assert export_response.status_code == 200
    body = export_response.data.decode('utf-8')
    assert 'order_id,display_id,contact_id,order_date,status,total_amount' in body
    assert 'ORD-1' in body

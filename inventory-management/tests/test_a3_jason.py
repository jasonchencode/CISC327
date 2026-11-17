"""Jason's Assignment 3 success scenarios and coverage-directed tests."""
from unittest.mock import patch

import pytest

from app import store


@pytest.fixture
def product(client):
    response = client.post('/products', json={
        'name': 'Keyboard', 'sku': 'KB-001',
        'quantity_on_hand': 10, 'reorder_level': 5,
    })
    assert response.status_code == 201
    return response.get_json()


def assert_recorded_movement(client, response, product, remaining):
    assert response.status_code == 201
    transaction = response.get_json()
    assert transaction['notification_sent'] is True
    assert transaction['product_id'] == product['id']
    assert transaction['type'] == 'OUT'
    assert transaction['quantity'] == 10 - remaining
    stock = client.get(f"/products/{product['id']}/stock-level").get_json()
    assert stock['quantity_on_hand'] == remaining
    saved = client.get('/transactions').get_json()
    assert len(saved) == 1
    assert saved[0]['id'] == transaction['id']
    assert saved[0]['quantity'] == transaction['quantity']


def test_low_stock_notification_success_stub(client, product, monkeypatch):
    """A successful dependency result is reported and stock remains updated."""
    monkeypatch.setattr('app.routes.transactions.send_notification',
                        lambda recipient, subject, message: True)
    response = client.post('/transactions', json={
        'product_id': product['id'], 'type': 'OUT', 'quantity': 6,
    })
    assert_recorded_movement(client, response, product, remaining=4)


def test_low_stock_notification_expected_arguments_at_threshold(client, product):
    """Equality with the reorder level triggers one correctly worded alert."""
    with patch('app.routes.transactions.send_notification', return_value=True) as send:
        response = client.post('/transactions', json={
            'product_id': product['id'], 'type': 'OUT', 'quantity': 5,
        })
        assert_recorded_movement(client, response, product, remaining=5)
        send.assert_called_once_with(
            'inventory@example.com', 'Low stock alert',
            'Keyboard (SKU: KB-001) has 5 units remaining; reorder level: 5.',
        )


@pytest.mark.parametrize('movement,quantity,remaining', [('IN', 3, 13), ('OUT', 2, 8)])
def test_transactions_page_records_movement(client, product, movement, quantity, remaining):
    response = client.post('/ui/transactions', data={
        'product_id': product['id'], 'type': movement,
        'quantity': quantity, 'supplier_id': '7',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/ui/transactions')
    assert store.products[product['id']].quantity_on_hand == remaining
    transaction, = store.transactions.values()
    assert transaction.product_id == product['id']
    assert transaction.supplier_id == 7
    assert transaction.type == movement
    assert transaction.quantity == quantity
    page = client.get('/ui/transactions')
    assert page.status_code == 200
    assert b'Record a Stock Movement' in page.data
    assert f'<td>{movement}</td>'.encode() in page.data
    assert f'<td>{quantity}</td>'.encode() in page.data


def test_transactions_page_without_supplier(client, product):
    response = client.post('/ui/transactions', data={
        'product_id': product['id'], 'type': 'IN', 'quantity': 2,
    }, follow_redirects=True)
    assert response.status_code == 200
    transaction, = store.transactions.values()
    assert transaction.supplier_id is None
    assert transaction.quantity == 2
    assert store.products[product['id']].quantity_on_hand == 12
    assert b'<td>-</td>' in response.data


def test_transactions_page_missing_product(client):
    response = client.post('/ui/transactions', data={
        'product_id': 999, 'type': 'IN', 'quantity': 2,
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Transactions' in response.data
    assert store.transactions == {}
    assert store.products == {}


@pytest.mark.parametrize('payload,error,status', [
    ({'product_id': 999, 'type': 'OUT', 'quantity': 2}, 'Product not found', 404),
    ({'type': 'INVALID', 'quantity': 2}, 'type must be IN or OUT', 400),
])
def test_transaction_api_error_preserves_state(client, product, payload, error, status):
    data = {'product_id': product['id'], **payload}
    response = client.post('/transactions', json=data)
    assert response.status_code == status
    assert response.get_json() == {'error': error}
    assert store.transactions == {}
    assert store.products[product['id']].quantity_on_hand == 10


@pytest.mark.parametrize('method,path', [
    ('get', '/purchase-orders/999'),
    ('put', '/purchase-orders/999/receive'),
    ('get', '/products/999/reconciliations'),
])
def test_missing_resource_error(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 404
    expected = 'Purchase order not found' if 'purchase-orders' in path else 'Product not found'
    assert response.get_json() == {'error': expected}
    assert store.transactions == {}


@pytest.mark.parametrize('supplier_exists', [False, True])
def test_purchase_order_missing_dependency(client, supplier_exists):
    supplier_id = 999
    if supplier_exists:
        supplier_id = client.post('/suppliers', json={
            'name': 'Supplier', 'contact_email': 'supplier@example.com',
        }).get_json()['id']
    response = client.post('/purchase-orders', json={
        'supplier_id': supplier_id, 'product_id': 999, 'quantity_ordered': 3,
    })
    assert response.status_code == 404
    expected = 'Product not found' if supplier_exists else 'Supplier not found'
    assert response.get_json() == {'error': expected}
    assert store.purchase_orders == {}
    assert store.transactions == {}

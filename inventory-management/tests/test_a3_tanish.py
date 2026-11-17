from unittest.mock import patch
import pytest


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Inventory Management System" in response.data


def test_product_creation_through_ui(client):
    response = client.post("/ui/products", data={
        "name": "Keyboard",
        "sku": "KB-001",
        "unit_price": "25.50",
        "quantity_on_hand": "10"
    }, follow_redirects=True)

    assert response.status_code == 200

    products = client.get("/products").get_json()

    assert len(products) == 1
    assert products[0]["name"] == "Keyboard"
    assert products[0]["quantity_on_hand"] == 10


def test_product_deletion_through_ui(client):
    product = client.post("/products", json={
        "name": "Mouse",
        "sku": "MS-001",
        "quantity_on_hand": 5
    }).get_json()

    response = client.post(
        f"/ui/products/{product['id']}/delete",
        follow_redirects=True
    )

    assert response.status_code == 200

    products = client.get("/products").get_json()
    assert products == []


def test_supplier_creation_through_ui(client):
    response = client.post("/ui/suppliers", data={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    }, follow_redirects=True)

    assert response.status_code == 200

    suppliers = client.get("/suppliers").get_json()
    assert len(suppliers) == 1
    assert suppliers[0]["name"] == "ABC Supplies"


def test_supplier_deletion_through_ui(client):
    supplier = client.post("/suppliers", json={
        "name": "Temporary Supplier",
        "contact_email": "temp@example.com"
    }).get_json()

    response = client.post(
        f"/ui/suppliers/{supplier['id']}/delete",
        follow_redirects=True
    )

    assert response.status_code == 200

    suppliers = client.get("/suppliers").get_json()
    assert suppliers == []


def test_update_nonexistent_supplier(client):
    response = client.put("/suppliers/999", json={
        "name": "Missing Supplier"
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def test_delete_nonexistent_supplier(client):
    response = client.delete("/suppliers/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def test_low_stock_notification_failure_stub(client, monkeypatch):
    """Failed notification does not undo a valid stock transaction."""

    product_response = client.post("/products", json={
        "name": "Monitor",
        "sku": "MON-001",
        "quantity_on_hand": 10,
        "reorder_level": 5,
    })
    assert product_response.status_code == 201
    product = product_response.get_json()

    # Stub: force the notification service to report failure.
    monkeypatch.setattr(
        "app.routes.transactions.send_notification",
        lambda recipient, subject, message: False
    )

    response = client.post("/transactions", json={
        "product_id": product["id"],
        "type": "OUT",
        "quantity": 7,
    })

    # The transaction succeeds despite notification failure.
    assert response.status_code == 201
    transaction = response.get_json()
    assert transaction["notification_sent"] is False
    assert transaction["type"] == "OUT"
    assert transaction["quantity"] == 7
    assert transaction["product_id"] == product["id"]

    # Inventory must still be updated from 10 to 3.
    stock_response = client.get(
        f"/products/{product['id']}/stock-level"
    )
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 3

    # The transaction must still be saved.
    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1
    assert transactions[0]["id"] == transaction["id"]


@pytest.mark.parametrize(
    "movement,quantity,expected_stock",
    [
        ("OUT", 2, 8),
        ("IN", 3, 13),
    ]
)
def test_notification_not_triggered(
    client, movement, quantity, expected_stock
):
    """Non-triggering movements must not call the notification service."""

    product_response = client.post("/products", json={
        "name": "Keyboard",
        "sku": "KB-002",
        "quantity_on_hand": 10,
        "reorder_level": 5,
    })
    assert product_response.status_code == 201
    product = product_response.get_json()

    # Mock: record whether the service is called.
    with patch(
        "app.routes.transactions.send_notification"
    ) as mock_send:

        response = client.post("/transactions", json={
            "product_id": product["id"],
            "type": movement,
            "quantity": quantity,
        })

        assert response.status_code == 201
        transaction = response.get_json()
        assert transaction["notification_sent"] is False
        assert transaction["type"] == movement
        assert transaction["quantity"] == quantity

        # No notification should have been attempted.
        mock_send.assert_not_called()

    # Verify that inventory was updated correctly.
    stock = client.get(
        f"/products/{product['id']}/stock-level"
    ).get_json()
    assert stock["quantity_on_hand"] == expected_stock

    # Verify the stock movement was recorded.
    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product["id"]
    assert transactions[0]["type"] == movement

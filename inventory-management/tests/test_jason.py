def test_list_all_products(client):
    """Returns all products currently in inventory."""
    product = {
        "name": "Widget A",
        "sku": "WGT-001",
        "unit_price": 9.99,
        "quantity_on_hand": 50,
        "reorder_level": 10,
    }
    client.post("/products", json=product)

    response = client.get("/products")

    assert response.status_code == 200
    products = response.get_json()
    assert len(products) == 1
    assert products[0]["name"] == "Widget A"
    assert products[0]["sku"] == "WGT-001"

def test_create_product_with_defaults(client):
    """Creates a product and applies default values for optional fields."""
    response = client.post("/products", json={
        "name": "Widget B",
        "sku": "WGT-002",
    })

    assert response.status_code == 201
    product = response.get_json()

    assert product["name"] == "Widget B"
    assert product["sku"] == "WGT-002"
    assert product["unit_price"] == 0.0
    assert product["quantity_on_hand"] == 0
    assert product["reorder_level"] == 0

    # Verify the product was actually stored.
    get_response = client.get(f"/products/{product['id']}")
    assert get_response.status_code == 200
    assert get_response.get_json() == product


def test_get_product(client):
    """Retrieves an existing product and handles nonexistent IDs."""
    create_response = client.post("/products", json={
        "name": "Widget C",
        "sku": "WGT-003",
        "unit_price": 15.50,
        "quantity_on_hand": 20,
        "reorder_level": 5,
    })
    product_id = create_response.get_json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Widget C"
    assert response.get_json()["quantity_on_hand"] == 20

    missing_response = client.get("/products/99999")
    assert missing_response.status_code == 404


def test_update_product(client):
    """Updates selected product fields without changing other fields."""
    create_response = client.post("/products", json={
        "name": "Widget D",
        "sku": "WGT-004",
        "unit_price": 10.0,
        "quantity_on_hand": 30,
        "reorder_level": 5,
    })
    product_id = create_response.get_json()["id"]

    response = client.put(f"/products/{product_id}", json={
        "name": "Updated Widget D",
        "quantity_on_hand": 40,
    })

    assert response.status_code == 200
    updated = response.get_json()

    assert updated["name"] == "Updated Widget D"
    assert updated["quantity_on_hand"] == 40
    assert updated["sku"] == "WGT-004"
    assert updated["unit_price"] == 10.0
    assert updated["reorder_level"] == 5

    missing_response = client.put("/products/99999", json={
        "name": "Missing Product",
    })
    assert missing_response.status_code == 404


def test_delete_product(client):
    """Deletes a product and verifies it can no longer be retrieved."""
    create_response = client.post("/products", json={
        "name": "Widget E",
        "sku": "WGT-005",
    })
    product_id = create_response.get_json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 204
    assert response.data == b""

    get_response = client.get(f"/products/{product_id}")
    assert get_response.status_code == 404

    missing_response = client.delete("/products/99999")
    assert missing_response.status_code == 404


def test_current_quantity_on_hand(client):
    """Returns the correct quantity for an existing product."""
    create_response = client.post("/products", json={
        "name": "Widget F",
        "sku": "WGT-006",
        "quantity_on_hand": 25,
    })
    product_id = create_response.get_json()["id"]

    response = client.get(f"/products/{product_id}/stock-level")

    assert response.status_code == 200
    assert response.get_json() == {
        "product_id": product_id,
        "quantity_on_hand": 25,
    }

    missing_response = client.get("/products/99999/stock-level")
    assert missing_response.status_code == 404

def test_identify_low_stock_products(client):
    """Includes products at or below their reorder level."""
    client.post("/products", json={
        "name": "Low Stock",
        "sku": "LOW-001",
        "quantity_on_hand": 5,
        "reorder_level": 5,
    })

    client.post("/products", json={
        "name": "Out of Stock",
        "sku": "LOW-002",
        "quantity_on_hand": 0,
        "reorder_level": 10,
    })

    client.post("/products", json={
        "name": "Healthy Stock",
        "sku": "LOW-003",
        "quantity_on_hand": 20,
        "reorder_level": 5,
    })

    response = client.get("/products/low-stock")

    assert response.status_code == 200
    products = response.get_json()

    assert len(products) == 2
    names = [product["name"] for product in products]
    assert "Low Stock" in names
    assert "Out of Stock" in names
    assert "Healthy Stock" not in names



def test_record_stock_movement(client):
    # Create a product with 10 units in stock
    product_response = client.post("/products", json={
        "name": "Test Product",
        "sku": "TEST-001",
        "quantity_on_hand": 10,
        "reorder_level": 2
    })

    product_id = product_response.get_json()["id"]

    # Record stock coming in
    in_response = client.post("/transactions", json={
        "product_id": product_id,
        "type": "IN",
        "quantity": 5
    })

    assert in_response.status_code == 201
    assert in_response.get_json()["type"] == "IN"
    assert in_response.get_json()["quantity"] == 5

    # Verify inventory increased from 10 to 15
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.get_json()["quantity_on_hand"] == 15

    # Record stock going out
    out_response = client.post("/transactions", json={
        "product_id": product_id,
        "type": "OUT",
        "quantity": 3
    })

    assert out_response.status_code == 201

    # Verify inventory decreased from 15 to 12
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.get_json()["quantity_on_hand"] == 12

    # Verify both transactions were recorded
    transactions_response = client.get("/transactions")
    transactions = transactions_response.get_json()

    assert len(transactions) == 2
    assert [t["type"] for t in transactions] == ["IN", "OUT"]


def test_receive_purchase_order(client):
    # Create a supplier
    supplier_response = client.post("/suppliers", json={
        "name": "Test Supplier",
        "contact_email": "supplier@test.com"
    })
    assert supplier_response.status_code == 201
    supplier_id = supplier_response.get_json()["id"]

    # Create a product with 10 units in stock
    product_response = client.post("/products", json={
        "name": "Test Product",
        "sku": "TEST-001",
        "quantity_on_hand": 10,
        "reorder_level": 2
    })
    assert product_response.status_code == 201
    product_id = product_response.get_json()["id"]

    # Create a purchase order for 5 additional units
    po_response = client.post("/purchase-orders", json={
        "supplier_id": supplier_id,
        "product_id": product_id,
        "quantity_ordered": 5
    })
    assert po_response.status_code == 201
    po_id = po_response.get_json()["id"]
    assert po_response.get_json()["status"] == "pending"

    # Receive the purchase order
    receive_response = client.put(f"/purchase-orders/{po_id}/receive")
    assert receive_response.status_code == 200
    assert receive_response.get_json()["status"] == "received"

    # Verify inventory increased from 10 to 15
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.get_json()["quantity_on_hand"] == 15

    # Verify an IN transaction was recorded
    transactions_response = client.get("/transactions")
    transactions = transactions_response.get_json()

    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product_id
    assert transactions[0]["supplier_id"] == supplier_id
    assert transactions[0]["type"] == "IN"
    assert transactions[0]["quantity"] == 5


def test_receive_purchase_order_updates_inventory_only_once(client):
    # Create a supplier
    supplier_response = client.post("/suppliers", json={
        "name": "Test Supplier",
        "contact_email": "supplier@test.com"
    })
    supplier_id = supplier_response.get_json()["id"]

    # Create a product with 10 units
    product_response = client.post("/products", json={
        "name": "Test Product",
        "sku": "TEST-001",
        "unit_price": 10.0,
        "quantity_on_hand": 10,
        "reorder_level": 2
    })
    product_id = product_response.get_json()["id"]

    # Create a purchase order for 5 units
    po_response = client.post("/purchase-orders", json={
        "supplier_id": supplier_id,
        "product_id": product_id,
        "quantity_ordered": 5
    })
    po_id = po_response.get_json()["id"]

    # Receive the purchase order
    first_response = client.put(f"/purchase-orders/{po_id}/receive")
    assert first_response.status_code == 200

    # Attempt to receive the same purchase order again
    second_response = client.put(f"/purchase-orders/{po_id}/receive")
    assert second_response.status_code == 400

    # Verify inventory was only increased once
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.get_json()["quantity_on_hand"] == 15
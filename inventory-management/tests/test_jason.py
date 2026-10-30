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
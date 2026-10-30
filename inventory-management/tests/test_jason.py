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

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

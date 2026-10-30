
def test_create_and_retrieve_supplier(client):
    response = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "orders@example.com"
    })

    assert response.status_code == 201

    supplier = response.get_json()
    assert supplier["name"] == "ABC Supplies"
    assert supplier["contact_email"] == "orders@example.com"

    supplier_id = supplier["id"]

    lookup = client.get(f"/suppliers/{supplier_id}")

    assert lookup.status_code == 200
    assert lookup.get_json()["name"] == "ABC Supplies"


def test_get_nonexistent_supplier(client):
    response = client.get("/suppliers/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def test_list_suppliers(client):
    client.post("/suppliers", json={
        "name": "Supplier A",
        "contact_email": "a@example.com"
    })
    client.post("/suppliers", json={
        "name": "Supplier B",
        "contact_email": "b@example.com"
    })

    response = client.get("/suppliers")

    assert response.status_code == 200
    suppliers = response.get_json()
    assert len(suppliers) == 2
    assert {s["name"] for s in suppliers} == {
        "Supplier A", "Supplier B"
    }


def test_update_supplier(client):
    created = client.post("/suppliers", json={
        "name": "Old Supplier",
        "contact_email": "old@example.com"
    })
    supplier_id = created.get_json()["id"]

    response = client.put(
        f"/suppliers/{supplier_id}",
        json={"name": "New Supplier"}
    )

    assert response.status_code == 200
    assert response.get_json()["name"] == "New Supplier"

    retrieved = client.get(f"/suppliers/{supplier_id}")
    assert retrieved.get_json()["name"] == "New Supplier"
    assert retrieved.get_json()["contact_email"] == "old@example.com"


def test_delete_supplier(client):
    created = client.post("/suppliers", json={
        "name": "Temporary Supplier",
        "contact_email": "temp@example.com"
    })
    supplier_id = created.get_json()["id"]

    response = client.delete(f"/suppliers/{supplier_id}")

    assert response.status_code == 204

    retrieved = client.get(f"/suppliers/{supplier_id}")
    assert retrieved.status_code == 404


def test_supplier_products(client):
    supplier = client.post("/suppliers", json={
        "name": "Hardware Supplier",
        "contact_email": "hardware@example.com"
    }).get_json()

    product = client.post("/products", json={
        "name": "Keyboard",
        "sku": "KB-001",
        "unit_price": 25,
        "quantity_on_hand": 10,
        "reorder_level": 3
    }).get_json()

    transaction = client.post("/transactions", json={
        "product_id": product["id"],
        "supplier_id": supplier["id"],
        "type": "IN",
        "quantity": 5
    })

    assert transaction.status_code == 201

    response = client.get(
        f"/suppliers/{supplier['id']}/products"
    )

    assert response.status_code == 200
    products = response.get_json()

    assert len(products) == 1
    assert products[0]["id"] == product["id"]
    

def test_filter_transactions_by_supplier(client):
    supplier_a = client.post("/suppliers", json={
        "name": "Supplier A",
        "contact_email": "a@example.com"
    }).get_json()

    supplier_b = client.post("/suppliers", json={
        "name": "Supplier B",
        "contact_email": "b@example.com"
    }).get_json()

    product = client.post("/products", json={
        "name": "Mouse",
        "sku": "MS-001"
    }).get_json()

    for supplier in (supplier_a, supplier_b):
        response = client.post("/transactions", json={
            "product_id": product["id"],
            "supplier_id": supplier["id"],
            "type": "IN",
            "quantity": 5
        })
        assert response.status_code == 201

    response = client.get(
        f"/transactions?supplier_id={supplier_a['id']}"
    )

    assert response.status_code == 200
    results = response.get_json()

    assert len(results) == 1
    assert results[0]["supplier_id"] == supplier_a["id"]
    

def test_filter_transactions_by_product(client):
    supplier = client.post("/suppliers", json={
        "name": "Supplier A",
        "contact_email": "a@example.com"
    }).get_json()

    first_product = client.post("/products", json={
        "name": "Keyboard",
        "sku": "KB-001"
    }).get_json()

    second_product = client.post("/products", json={
        "name": "Mouse",
        "sku": "MS-001"
    }).get_json()

    for product in (first_product, second_product):
        response = client.post("/transactions", json={
            "product_id": product["id"],
            "supplier_id": supplier["id"],
            "type": "IN",
            "quantity": 5
        })
        assert response.status_code == 201

    response = client.get(
        f"/transactions?product_id={second_product['id']}"
    )

    assert response.status_code == 200
    results = response.get_json()

    assert len(results) == 1
    assert results[0]["product_id"] == second_product["id"]

 
def test_create_purchase_order(client):
    supplier = client.post("/suppliers", json={
        "name": "Hardware Supplier",
        "contact_email": "orders@example.com"
    }).get_json()

    product = client.post("/products", json={
        "name": "Keyboard",
        "sku": "KB-001",
        "unit_price": 25,
        "quantity_on_hand": 10
    }).get_json()

    response = client.post("/purchase-orders", json={
        "supplier_id": supplier["id"],
        "product_id": product["id"],
        "quantity_ordered": 20
    })

    assert response.status_code == 201
    order = response.get_json()

    assert order["supplier_id"] == supplier["id"]
    assert order["product_id"] == product["id"]
    assert order["quantity_ordered"] == 20
    assert order["status"] == "pending"


def test_list_purchase_orders(client):
    supplier = client.post("/suppliers", json={
        "name": "Supplier A",
        "contact_email": "a@example.com"
    }).get_json()

    product = client.post("/products", json={
        "name": "Mouse",
        "sku": "MS-001"
    }).get_json()

    for quantity in (10, 25):
        response = client.post("/purchase-orders", json={
            "supplier_id": supplier["id"],
            "product_id": product["id"],
            "quantity_ordered": quantity
        })
        assert response.status_code == 201

    response = client.get("/purchase-orders")

    assert response.status_code == 200
    orders = response.get_json()

    assert len(orders) == 2
    assert {order["quantity_ordered"] for order in orders} == {
        10, 25
    }


def test_get_purchase_order(client):
    supplier = client.post("/suppliers", json={
        "name": "Supplier A",
        "contact_email": "a@example.com"
    }).get_json()

    product = client.post("/products", json={
        "name": "Monitor",
        "sku": "MON-001"
    }).get_json()

    created = client.post("/purchase-orders", json={
        "supplier_id": supplier["id"],
        "product_id": product["id"],
        "quantity_ordered": 15
    })

    assert created.status_code == 201
    order_id = created.get_json()["id"]

    response = client.get(f"/purchase-orders/{order_id}")

    assert response.status_code == 200
    order = response.get_json()

    assert order["id"] == order_id
    assert order["quantity_ordered"] == 15
    assert order["status"] == "pending"


def test_purchase_order_invalid_supplier(client):
    product = client.post("/products", json={
        "name": "Keyboard",
        "sku": "KB-001"
    }).get_json()

    response = client.post("/purchase-orders", json={
        "supplier_id": 999,
        "product_id": product["id"],
        "quantity_ordered": 10
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"

    # An invalid order must not be saved.
    orders = client.get("/purchase-orders").get_json()
    assert orders == []


def test_get_nonexistent_purchase_order(client):
    response = client.get("/purchase-orders/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Purchase order not found"


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

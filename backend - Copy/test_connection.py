import json
import sys
from pathlib import Path

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from server import create_app

def test_full_pipeline():
    print("==================================================")
    print("      Testing LegalEase Backend API Endpoints     ")
    print("==================================================")

    app = create_app("development")
    client = app.test_client()

    # 1. Health check
    print("\n[1] Testing GET /api/health ...")
    res = client.get("/api/health")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.get_data(as_text=True)}"
    data = res.get_json()
    print(f"Response: {data}")
    assert data.get("status") == "ok"
    print("--> Health check passed!")

    # 2. Register user
    test_email = "testrunner@legalease.com"
    test_password = "password123"
    print(f"\n[2] Testing POST /api/auth/register for {test_email} ...")
    res = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_password,
        "name": "Test Runner"
    })
    print(f"Status: {res.status_code}")
    if res.status_code == 409:
        print("User already exists, proceeding to login...")
    else:
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.get_data(as_text=True)}"
        reg_data = res.get_json()
        print(f"Registered user: {reg_data.get('user')}")

    # 3. Login user
    print(f"\n[3] Testing POST /api/auth/login ...")
    res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.get_data(as_text=True)}"
    login_data = res.get_json()
    token = login_data.get("token")
    assert token, "No token returned in login"
    print(f"Received JWT token: {token[:20]}...")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 4. Current user info
    print("\n[4] Testing GET /api/auth/me ...")
    res = client.get("/api/auth/me", headers=auth_headers)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    me_data = res.get_json()
    print(f"User profile: {me_data}")

    # 5. Create document
    print("\n[5] Testing POST /api/documents (Create Document) ...")
    doc_payload = {
        "template_type": "nda",
        "title": "Mutual Non-Disclosure Agreement - Test Draft",
        "answers": {
            "party_a": "Acme Robotics LLC",
            "party_b": "Jordan Reyes",
            "jurisdiction": "Delaware",
            "effective_date": "2026-09-27",
            "term": "2",
            "mutual": "mutual",
            "penalty": "fixed",
            "penalty_amount": "50000"
        }
    }
    res = client.post("/api/documents", json=doc_payload, headers=auth_headers)
    print(f"Status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201: {res.get_data(as_text=True)}"
    doc_data = res.get_json()
    doc_id = doc_data.get("id")
    print(f"Created Document #{doc_id}")
    print(f"Risk Flags Found: {len(doc_data.get('risk_flags', []))}")
    for flag in doc_data.get("risk_flags", []):
        print(f"  - [{flag.get('level').upper()}] {flag.get('message')}")
    print(f"Drafted Content Preview:\n{doc_data.get('content')[:200]}...\n")

    # 6. Retrieve document
    print(f"\n[6] Testing GET /api/documents/{doc_id} ...")
    res = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    print(f"Retrieved Document #{doc_id} successfully.")

    # 7. Update document
    print(f"\n[7] Testing PUT /api/documents/{doc_id} (Update Answers) ...")
    updated_payload = {
        "title": "Mutual NDA - Updated Draft",
        "answers": {
            "party_a": "Acme Robotics LLC",
            "party_b": "Jordan Reyes",
            "jurisdiction": "California",
            "effective_date": "2026-10-01",
            "term": "3",
            "mutual": "mutual",
            "penalty": "none",
            "penalty_amount": "0"
        }
    }
    res = client.put(f"/api/documents/{doc_id}", json=updated_payload, headers=auth_headers)
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    updated_doc = res.get_json()
    print(f"Updated jurisdiction to: {updated_doc.get('jurisdiction')}")

    # 8. Test clause explanation
    print(f"\n[8] Testing POST /api/documents/{doc_id}/explain-clause ...")
    clause_payload = {
        "clause_text": "Each party may disclose information considered confidential in connection with this relationship."
    }
    res = client.post(f"/api/documents/{doc_id}/explain-clause", json=clause_payload, headers=auth_headers)
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    expl_data = res.get_json()
    print(f"Clause Explanation: {expl_data.get('explanation')}")

    # 9. Test export docx
    print(f"\n[9] Testing GET /api/documents/{doc_id}/export?format=docx ...")
    res = client.get(f"/api/documents/{doc_id}/export?format=docx", headers=auth_headers)
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    print(f"DOCX Export size: {len(res.data)} bytes")

    # 10. Test export pdf
    print(f"\n[10] Testing GET /api/documents/{doc_id}/export?format=pdf ...")
    res = client.get(f"/api/documents/{doc_id}/export?format=pdf", headers=auth_headers)
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    print(f"PDF Export size: {len(res.data)} bytes")

    # 11. Test list documents
    print("\n[11] Testing GET /api/documents ...")
    res = client.get("/api/documents", headers=auth_headers)
    assert res.status_code == 200, f"Expected 200: {res.get_data(as_text=True)}"
    docs_list = res.get_json()
    print(f"Total documents for user: {len(docs_list)}")

    print("\n==================================================")
    print("   ALL API ENDPOINTS & FLOWS VERIFIED 100% OK!    ")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()

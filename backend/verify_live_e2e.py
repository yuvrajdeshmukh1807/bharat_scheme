import urllib.request
import json

print("=" * 60)
print("BHARATSCHEME AI - END-TO-END VERIFICATION")
print("=" * 60)

# 1. Frontend Web Page
r1 = urllib.request.urlopen("http://localhost:5173")
print(f"1. Frontend Web Page: {r1.status} OK ({len(r1.read())} bytes received)")

# 2. Backend Health
r2 = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
d2 = json.loads(r2.read().decode())
print(f"2. Backend Direct Health: {r2.status} OK (Indexed: {d2['schemes_indexed']} schemes)")

# 3. Frontend API Proxy - Scheme Catalog
r3 = urllib.request.urlopen("http://localhost:5173/api/schemes")
d3 = json.loads(r3.read().decode())
print(f"3. Frontend API Proxy (Schemes): {r3.status} OK ({len(d3)} schemes fetched)")

# 4. Frontend API Proxy - Eligibility Calculation
prof = {
    "state": "Maharashtra", "age": 45, "gender": "male", "caste_category": "OBC",
    "occupation": "farmer", "student_status": False, "annual_income": 120000,
    "is_farmer": True, "has_landholding": True, "is_entrepreneur": False,
    "is_differently_abled": False, "is_bpl_ration_card_holder": False,
    "is_minority": False, "language": "en"
}
req4 = urllib.request.Request(
    "http://localhost:5173/api/eligibility/check",
    data=json.dumps(prof).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
r4 = urllib.request.urlopen(req4)
d4 = json.loads(r4.read().decode())
print(f"4. Frontend API Proxy (Eligibility): {r4.status} OK (Eligible count: {d4['eligible_count']})")

# 5. Frontend API Proxy - AI RAG Assistant Chat
chat = {"query": "What is PM Kisan?", "language": "en"}
req5 = urllib.request.Request(
    "http://localhost:5173/api/assistant/chat",
    data=json.dumps(chat).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
r5 = urllib.request.urlopen(req5)
d5 = json.loads(r5.read().decode())
citations = [c["scheme_id"] for c in d5["citations"]]
print(f"5. Frontend API Proxy (RAG Chat): {r5.status} OK (Citations: {citations})")

print("=" * 60)
print("ALL 5 END-TO-END WORKFLOWS PASSED 100% SUCCESSFULLY!")
print("=" * 60)

import json
import urllib.request

API_BASE = "http://127.0.0.1:8000/api/v1"

def call_api(endpoint: str, data: dict = None, method: str = "GET"):
    url = f"{API_BASE}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=" * 65)
print("AgentDesk MVP — Phase 1D Live End-to-End Verification")
print("=" * 65)

# 1. Fetch demo business
demo_biz = call_api("/business/demo")
biz_id = demo_biz["id"]
print(f"Target Business: {demo_biz['name']} ({biz_id})")

# 2. Test Informational Question
q1 = "What are your opening hours?"
print("\n" + "-" * 50)
print(f"TEST 1: Informational Question -> '{q1}'")
r1 = call_api("/chat", {"business_id": biz_id, "message": q1}, method="POST")
print(f"Answer: {r1['answer'][:90]}...")
print(f"Lead Created: {r1['lead']['created']} | Status: {r1['lead']['status']} | Score: {r1['lead']['score']}")
assert r1["lead"]["created"] is False, "Expected NO lead for hours question"
print("[PASS] Verified: No lead created for general informational query.")

# 3. Test Warm Lead (Interest)
q2 = "How much does teeth whitening cost? I'm interested."
print("\n" + "-" * 50)
print(f"TEST 2: Interest Question -> '{q2}'")
r2 = call_api("/chat", {"business_id": biz_id, "message": q2}, method="POST")
print(f"Answer: {r2['answer'][:90]}...")
print(f"Lead Created: {r2['lead']['created']} | Status: {r2['lead']['status']} | Score: {r2['lead']['score']}")
assert r2["lead"]["created"] is True, "Expected lead created for pricing interest"
assert r2["lead"]["status"] == "WARM", "Expected WARM status"
print(f"[PASS] Verified: WARM lead created with deterministic score {r2['lead']['score']}.")

# 4. Test Strong Intent / Hot Lead with Contact Details
q3 = "I want to book teeth whitening. My name is Ali and my email is ali@example.com."
print("\n" + "-" * 50)
print(f"TEST 3: Strong Intent + Contact -> '{q3}'")
r3 = call_api("/chat", {"business_id": biz_id, "message": q3}, method="POST")
print(f"Answer: {r3['answer'][:90]}...")
print(f"Lead Created: {r3['lead']['created']} | Status: {r3['lead']['status']} | Score: {r3['lead']['score']}")
assert r3["lead"]["created"] is True, "Expected lead created for booking request"
assert r3["lead"]["status"] == "HOT", "Expected HOT status"
assert r3["lead"]["score"] >= 80, "Expected score >= 80"
print(f"[PASS] Verified: HOT lead created with deterministic score {r3['lead']['score']}.")

# 5. Verify Leads API and Dashboard endpoint
print("\n" + "-" * 50)
print(f"TEST 4: GET /api/v1/leads for {biz_id}")
leads_data = call_api(f"/leads?business_id={biz_id}")
print(f"Total Leads: {leads_data['total_leads']}")
print(f"HOT Leads:   {leads_data['hot_leads']}")
print(f"WARM Leads:  {leads_data['warm_leads']}")
print(f"COLD Leads:  {leads_data['cold_leads']}")
print(f"Recent Leads returned: {len(leads_data['leads'])}")

found_ali = any(l["name"] == "Ali" and l["email"] == "ali@example.com" for l in leads_data["leads"])
assert found_ali, "Captured lead 'Ali' should be present in leads database"
print("[PASS] Verified: Ali (ali@example.com) found in leads database.")


print("\n" + "=" * 65)
print("ALL LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY.")
print("=" * 65)

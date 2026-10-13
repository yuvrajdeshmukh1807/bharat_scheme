"""Deep audit of schemes_data.py and API endpoint behavior."""
import sys, json
sys.path.insert(0, '.')
from schemes_data import SCHEMES_DATA, CATEGORIES_METADATA
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=" * 60)
print("SCHEMES DATA AUDIT")
print("=" * 60)
print(f"Total schemes in SCHEMES_DATA: {len(SCHEMES_DATA)}")
print(f"Total categories in CATEGORIES_METADATA: {len(CATEGORIES_METADATA)}")

# Check required fields on every scheme
required_fields = [
    'id','slug','title_en','title_hi','title_mr','ministry','level','state_name',
    'category','brief_en','brief_hi','brief_mr','description_en','description_hi','description_mr',
    'benefits_en','benefits_hi','benefits_mr','eligibility_criteria',
    'eligibility_summary_en','eligibility_summary_hi','eligibility_summary_mr',
    'documents_required_en','documents_required_hi','documents_required_mr',
    'application_steps_en','application_steps_hi','application_steps_mr',
    'official_portal_url','application_mode','tags'
]
missing_field_errors = []
for s in SCHEMES_DATA:
    for f in required_fields:
        if f not in s or s[f] is None:
            missing_field_errors.append(f"SCHEME {s['id']} missing field: {f}")
        elif isinstance(s[f], str) and s[f].strip() == '':
            missing_field_errors.append(f"SCHEME {s['id']} EMPTY field: {f}")

if missing_field_errors:
    print("MISSING/EMPTY FIELDS:")
    for e in missing_field_errors[:20]:
        print(f"  {e}")
else:
    print("All required fields present on all schemes: OK")

# Check URL format
url_issues = []
for s in SCHEMES_DATA:
    url = s.get('official_portal_url', '')
    if not url.startswith('http'):
        url_issues.append(f"{s['id']}: invalid URL: {url}")
    elif '.gov.in' not in url and '.nic.in' not in url and 'gov' not in url:
        url_issues.append(f"{s['id']}: non-gov URL: {url}")
if url_issues:
    print("URL ISSUES:")
    for u in url_issues:
        print(f"  {u}")
else:
    print("All scheme URLs valid .gov.in/.nic.in: OK")

# Check eligibility_criteria has at least one rule key
ec_issues = []
for s in SCHEMES_DATA:
    ec = s.get('eligibility_criteria', {})
    if not ec:
        ec_issues.append(f"{s['id']}: empty eligibility_criteria")
if ec_issues:
    print("ELIGIBILITY CRITERIA ISSUES:")
    for e in ec_issues:
        print(f"  {e}")
else:
    print("All schemes have eligibility_criteria: OK")

# List scheme IDs
print("\nAll scheme IDs:")
for s in SCHEMES_DATA:
    print(f"  {s['id']} [{s['level']}] {s['category']}")

print("\n" + "=" * 60)
print("API ENDPOINT AUDIT")
print("=" * 60)

# Test all endpoints
tests = [
    ("GET /api/health", lambda: client.get("/api/health")),
    ("GET /api/categories", lambda: client.get("/api/categories")),
    ("GET /api/categories?language=hi", lambda: client.get("/api/categories?language=hi")),
    ("GET /api/categories?language=mr", lambda: client.get("/api/categories?language=mr")),
    ("GET /api/schemes", lambda: client.get("/api/schemes")),
    ("GET /api/schemes?language=hi", lambda: client.get("/api/schemes?language=hi")),
    ("GET /api/schemes?category=Agriculture+and+Farmers", lambda: client.get("/api/schemes?category=Agriculture+and+Farmers")),
    ("GET /api/schemes?level=State", lambda: client.get("/api/schemes?level=State")),
    ("GET /api/schemes?search=kisan", lambda: client.get("/api/schemes?search=kisan")),
    ("GET /api/featured", lambda: client.get("/api/featured")),
    ("GET /api/featured?language=hi", lambda: client.get("/api/featured?language=hi")),
    ("GET /api/schemes/pm-kisan", lambda: client.get("/api/schemes/pm-kisan")),
    ("GET /api/schemes/INVALID-ID", lambda: client.get("/api/schemes/INVALID-ID-999")),
    ("GET /api/saved-schemes?user_id=test-user-audit", lambda: client.get("/api/saved-schemes?user_id=test-user-audit")),
]

for name, fn in tests:
    r = fn()
    status_ok = "OK" if r.status_code in [200, 404] else "FAIL"
    data_len = ""
    try:
        d = r.json()
        if isinstance(d, list):
            data_len = f" [{len(d)} items]"
        elif isinstance(d, dict) and 'schemes_indexed' in d:
            data_len = f" [indexed={d['schemes_indexed']}]"
    except:
        pass
    print(f"  {status_ok} {r.status_code} {name}{data_len}")

# Test eligibility with all 3 personas
print("\nELIGIBILITY ENGINE SPOT CHECKS:")
from schemas import EligibilityProfile
from eligibility_engine import evaluate_scheme_eligibility
from schemes_data import SCHEMES_DATA

def quick_check(label, profile_dict, scheme_id):
    profile = EligibilityProfile(**profile_dict)
    scheme = next((s for s in SCHEMES_DATA if s['id'] == scheme_id), None)
    if not scheme:
        print(f"  SKIP {label}: scheme {scheme_id} not found")
        return
    result = evaluate_scheme_eligibility(scheme, profile)
    print(f"  {label}: {result.match_status} (score={result.match_score}) matched={len(result.matched_reasons)} unmet={len(result.unmet_reasons)}")

quick_check("Farmer->pm-kisan", {"state":"Maharashtra","age":45,"gender":"male","caste_category":"OBC","occupation":"farmer","student_status":False,"annual_income":120000,"is_farmer":True,"has_landholding":True,"is_entrepreneur":False,"is_differently_abled":False,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"en"}, "pm-kisan")
quick_check("Student->scholarship", {"state":"Maharashtra","age":20,"gender":"female","caste_category":"General","occupation":"student","student_status":True,"education_level":"undergraduate","annual_income":350000,"is_farmer":False,"has_landholding":False,"is_entrepreneur":False,"is_differently_abled":False,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"en"}, "central-sector-scholarship-pm-usp")
quick_check("Woman->ladki-bahin", {"state":"Maharashtra","age":32,"gender":"female","caste_category":"General","occupation":"homemaker","student_status":False,"annual_income":150000,"is_farmer":False,"has_landholding":False,"is_entrepreneur":False,"is_differently_abled":False,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"mr"}, "majhi-ladki-bahin-maharashtra")
quick_check("Wrong-state->ladki-bahin", {"state":"Bihar","age":30,"gender":"female","caste_category":"General","occupation":"homemaker","student_status":False,"annual_income":150000,"is_farmer":False,"has_landholding":False,"is_entrepreneur":False,"is_differently_abled":False,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"en"}, "majhi-ladki-bahin-maharashtra")
quick_check("Male->gender-restricted", {"state":"Maharashtra","age":20,"gender":"male","caste_category":"General","occupation":"student","student_status":True,"annual_income":350000,"is_farmer":False,"has_landholding":False,"is_entrepreneur":False,"is_differently_abled":False,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"en"}, "pm-pragati-scholarship-girls")
quick_check("Disability->adip", {"state":"Maharashtra","age":30,"gender":"male","caste_category":"General","occupation":"unemployed","student_status":False,"annual_income":80000,"is_farmer":False,"has_landholding":False,"is_entrepreneur":False,"is_differently_abled":True,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"en"}, "adip-scheme-divyangjan")
quick_check("Non-disabled->adip", {"state":"Maharashtra","age":30,"gender":"male","caste_category":"General","occupation":"salaried","student_status":False,"annual_income":80000,"is_farmer":False,"has_landholding":False,"is_entrepreneur":False,"is_differently_abled":False,"is_bpl_ration_card_holder":False,"is_minority":False,"language":"en"}, "adip-scheme-divyangjan")

print("\nAUDIT COMPLETE")

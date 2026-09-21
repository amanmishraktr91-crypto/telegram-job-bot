"""
Local Pipeline Test Script
Simulates the entire workflow (Scraping -> Fake Filter -> Intelligence Breakdown)
without needing a Telegram token.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from anti_scam import filter_fake_jobs, check_job_legitimacy

from job_aggregator import search_all_jobs
from ai_analyzer import analyze_job_market

def run_test(query: str = "UI/UX Designer", location: str = "Noida"):
    print(f"\n" + "="*60)
    print(f"RUNNING JOB INTELLIGENCE PIPELINE TEST")
    print(f"Role: {query} | Location: {location}")
    print("="*60)

    # 1. Test Scam Filter with Synthetic Scam Job
    print("\n--- [STEP 1] Testing Anti-Scam Filter on Sample Scam Job ---")
    fake_sample = {
        "title": "Part Time Work From Home UI Assistant",
        "company": "Urgent Hiring",
        "location": "Noida",
        "description": "Daily payout guaranteed! Earn Rs 2500 per day. No skills required. Pay registration fee 499 for company kit. Send resume to hr_job_recruiter99@gmail.com",
        "apply_link": "https://wa.me/919999999999"
    }
    is_safe, score, red_flags = check_job_legitimacy(fake_sample)
    print(f"Fake Sample Legitimate? -> {is_safe} (Trust Score: {score})")
    print(f"Caught Red Flags: {red_flags}")
    assert not is_safe, "Scam filter failed to catch fake sample job!"
    print("[OK] Anti-Scam Filter working accurately!")

    # 2. Test Live Fetching
    print(f"\n--- [STEP 2] Fetching Live Jobs for '{query}' in '{location}' ---")
    raw_jobs = search_all_jobs(query, location)
    print(f"Total raw jobs fetched: {len(raw_jobs)}")

    if not raw_jobs:
        print("Note: No live jobs returned from network in test environment.")
        return

    # 3. Filter real jobs
    verified, discarded = filter_fake_jobs(raw_jobs)
    print(f"Verified Safe Jobs: {len(verified)}")
    print(f"Blocked/Discarded Suspicious Jobs: {len(discarded)}")

    # 4. Market Intelligence
    print("\n--- [STEP 3] Running Tiered Job Intelligence Analysis ---")
    analysis = analyze_job_market(query, location, verified)
    tier_specs = analysis.get("tier_specs", {})
    classified = analysis.get("classified_jobs", {})

    for tier_name, label in [("fresher", "Fresher (0-1 yr)"), ("mid", "Mid-Level (2-4 yrs)"), ("senior", "Senior (5+ yrs)")]:
        spec = tier_specs.get(tier_name, {})
        jobs = classified.get(tier_name, [])
        print(f"\n>> {label}:")
        print(f"   Salary: {spec.get('salary')}")
        print(f"   Skills: {spec.get('skills')}")
        print(f"   Tools:  {spec.get('tools')}")
        print(f"   Companies Hiring ({len(jobs)}):")
        for j in jobs[:2]:
            print(f"     * {j.get('company')} ({j.get('location')}) - {j.get('title')}")


    print("\n" + "="*60)
    print("[SUCCESS] PIPELINE TEST COMPLETE - SYSTEM READY!")
    print("="*60 + "\n")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "UI/UX Designer"
    loc = sys.argv[2] if len(sys.argv) > 2 else "Noida"
    run_test(q, loc)

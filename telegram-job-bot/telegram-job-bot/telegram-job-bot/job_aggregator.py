"""
Multi-Source Job Aggregator with Watchdog Integration
Aggregates job listings across LinkedIn, Google Jobs, Naukri, and Indeed.
Protected by OutputAuditor, GeoSentinel, and AutoHealer.
"""

import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
import re
from config import SERPAPI_KEY
from self_healing_watchdog import OutputAuditor, GeoSentinel, CompanyTruthSentinel, auto_heal_sync, health_sentinel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Compatibility helper
def is_relevant_job(query: str, title: str) -> bool:
    return OutputAuditor.audit_job(query, {"title": title})

def is_location_match(job_location: str, target_location: str) -> bool:
    return GeoSentinel.verify_location(job_location, target_location)


@auto_heal_sync(max_retries=2, delay=1.0, fallback_return=[])
def fetch_linkedin_public_jobs(query: str, location: str, limit: int = 25) -> List[Dict[str, Any]]:
    """
    Fetches real active job listings directly from LinkedIn's public job endpoint.
    Protected by AutoHealer retry shield and strict OutputAuditor + GeoSentinel validators.
    """
    jobs = []
    loc_search = location.strip()
    is_pan_india = loc_search.lower() in ["india", "all india"]

    if not re.search(r'\b(usa|united states|uk|canada|germany|dubai)\b', loc_search, re.IGNORECASE):
        if "india" not in loc_search.lower():
            loc_search = f"{loc_search}, India"

    encoded_query = urllib.parse.quote(query)
    encoded_location = urllib.parse.quote(loc_search)

    # For specific cities, paginate pages (0, 25, 50) to collect sufficient city-specific jobs
    pages = [0, 25] if is_pan_india else [0, 25, 50]

    failed_pages = 0
    for start_idx in pages:
        if len(jobs) >= limit:
            break

        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
            f"keywords={encoded_query}&location={encoded_location}&start={start_idx}"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                failed_pages += 1
                continue
        except Exception as req_err:
            failed_pages += 1
            logger.warning(f"Error fetching LinkedIn page {start_idx}: {req_err}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("li")
        if not job_cards:
            break

        for card in job_cards:
            if len(jobs) >= limit:
                break

            title_tag = card.find("h3", class_="base-search-card__title")
            company_tag = card.find("h4", class_="base-search-card__subtitle")
            location_tag = card.find("span", class_="job-search-card__location")
            link_tag = card.find("a", class_="base-card__full-link")
            time_tag = card.find("time")

            if not title_tag or not company_tag:
                continue

            title = title_tag.get_text(strip=True)
            company = company_tag.get_text(strip=True)
            loc = location_tag.get_text(strip=True) if location_tag else location

            # WATCHDOG 1: OutputAuditor verifies role relevance (blocks dishwashers, sales trainees, etc.)
            if not OutputAuditor.audit_job(query, {"title": title}):
                continue

            # WATCHDOG 2: GeoSentinel verifies exact geographic boundaries (Noida vs India)
            if not GeoSentinel.verify_location(loc, location):
                continue

            # WATCHDOG 3: CompanyTruthSentinel blocks generic shells ('Confidential', 'Urgent Hiring')
            if not CompanyTruthSentinel.is_authentic_company(company):
                continue

            apply_link = link_tag.get("href", "").split("?")[0] if link_tag else ""
            posted_at = time_tag.get_text(strip=True) if time_tag else "Recently"

            jobs.append({
                "title": title,
                "company": company,
                "location": loc,
                "description": f"Position: {title} at {company}. Location: {loc}. Posted: {posted_at}.",
                "salary": "Check on listing",
                "apply_link": apply_link or f"https://www.linkedin.com/jobs/search?keywords={encoded_query}&location={encoded_location}",
                "source": "LinkedIn",
                "posted_at": posted_at
            })

    # FIX Issue 10: If all pages failed due to network errors, raise ConnectionError so @auto_heal_sync retries!
    if not jobs and failed_pages >= len(pages):
        raise ConnectionError(f"All {failed_pages} LinkedIn pages failed to respond.")

    return jobs


@auto_heal_sync(max_retries=2, delay=1.0, fallback_return=[])
def fetch_serpapi_google_jobs(query: str, location: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetches job listings from Google Jobs via SerpApi.
    Protected by AutoHealer retry shield.
    """
    jobs = []
    if not SERPAPI_KEY:
        return jobs

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": f"{query} in {location}",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }
    res = requests.get(url, params=params, timeout=12)
    if res.status_code == 200:
        data = res.json()
        raw_jobs = data.get("jobs_results", [])
        for r in raw_jobs[:limit]:
            apply_links = r.get("apply_options", [])
            link = apply_links[0].get("link") if apply_links else ""
            
            # FIX Issue 9: Skip jobs with empty links to prevent broken <a href="">
            if not link:
                continue

            source_name = apply_links[0].get("title", "Google Jobs") if apply_links else "Google Jobs"
            salary = r.get("detected_extensions", {}).get("salary", "Not Disclosed")
            posted_at = r.get("detected_extensions", {}).get("posted_at", "Recently")
            loc = r.get("location", location)

            title = r.get("title", "")
            company = r.get("company_name", "")
            if not OutputAuditor.audit_job(query, {"title": title}):
                continue
            if not GeoSentinel.verify_location(loc, location):
                continue
            if not CompanyTruthSentinel.is_authentic_company(company):
                continue

            jobs.append({
                "title": title,
                "company": r.get("company_name", ""),
                "location": loc,
                "description": r.get("description", ""),
                "salary": salary,
                "apply_link": link,
                "source": source_name,
                "posted_at": posted_at
            })

    return jobs


def search_all_jobs(query: str, location: str) -> List[Dict[str, Any]]:
    """
    Combines results across sources with autonomous self-healing.
    If 0 jobs are found, automatically tries alternative verified query terms.
    """
    all_jobs = []

    # 1. Fetch from LinkedIn public portal
    linkedin_jobs = fetch_linkedin_public_jobs(query, location, limit=20)
    all_jobs.extend(linkedin_jobs)

    # 2. Fetch SerpApi if key is provided
    if SERPAPI_KEY:
        google_jobs = fetch_serpapi_google_jobs(query, location, limit=15)
        all_jobs.extend(google_jobs)

    # 3. AUTONOMOUS SELF-HEALING:
    # If 0 jobs found for the exact term, query OutputAuditor for alternative terms
    if not all_jobs:
        fallback_query = OutputAuditor.get_self_healing_fallback_query(query, attempt=0)
        if fallback_query:
            logger.info(f"[AutoHealer] 0 jobs for '{query}'. Auto-recovering using fallback: '{fallback_query}'")
            fallback_jobs = fetch_linkedin_public_jobs(fallback_query, location, limit=15)
            all_jobs.extend(fallback_jobs)

    # Deduplicate results
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        key = (j.get("company", "").strip().lower(), j.get("title", "").strip().lower()[:25])
        if key not in seen and j.get("title") and j.get("company"):
            seen.add(key)
            unique_jobs.append(j)

    return unique_jobs

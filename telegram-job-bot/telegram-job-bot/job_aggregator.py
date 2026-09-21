"""
Multi-Source Job Aggregator
Aggregates job listings across LinkedIn, Google Jobs, Naukri, and Indeed.
"""

import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
from config import SERPAPI_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_linkedin_public_jobs(query: str, location: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Fetches real active job listings directly from LinkedIn's public job endpoint.
    Requires no login credentials.
    """
    jobs = []
    try:
        encoded_query = urllib.parse.quote(query)
        encoded_location = urllib.parse.quote(location)
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
            f"keywords={encoded_query}&location={encoded_location}&start=0"
        )

        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code != 200:
            logger.warning(f"LinkedIn public API returned status: {response.status_code}")
            return jobs

        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("li")

        for card in job_cards[:limit]:
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

        # Prioritize jobs whose location explicitly mentions the target city
        target_city = location.strip().lower()
        exact_matches = [j for j in jobs if target_city in j["location"].lower()]
        other_matches = [j for j in jobs if target_city not in j["location"].lower()]
        jobs = exact_matches + other_matches

    except Exception as e:
        logger.error(f"Error fetching LinkedIn jobs: {e}")

    return jobs



def fetch_serpapi_google_jobs(query: str, location: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetches job listings from Google Jobs via SerpApi (aggregates LinkedIn, Naukri, Indeed, Glassdoor).
    """
    jobs = []
    if not SERPAPI_KEY:
        return jobs

    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_jobs",
            "q": f"{query} in {location}",
            "hl": "en",
            "api_key": SERPAPI_KEY,
        }
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            raw_jobs = data.get("jobs_results", [])
            for r in raw_jobs[:limit]:
                # Extract best apply link
                apply_links = r.get("apply_options", [])
                link = apply_links[0].get("link") if apply_links else ""
                source_name = apply_links[0].get("title", "Google Jobs") if apply_links else "Google Jobs"

                salary = r.get("detected_extensions", {}).get("salary", "Not Disclosed")
                posted_at = r.get("detected_extensions", {}).get("posted_at", "Recently")

                jobs.append({
                    "title": r.get("title", ""),
                    "company": r.get("company_name", ""),
                    "location": r.get("location", location),
                    "description": r.get("description", ""),
                    "salary": salary,
                    "apply_link": link,
                    "source": source_name,
                    "posted_at": posted_at
                })
    except Exception as e:
        logger.error(f"Error in SerpApi fetch: {e}")

    return jobs


def search_all_jobs(query: str, location: str) -> List[Dict[str, Any]]:
    """
    Combines results from LinkedIn, Google Jobs, and job aggregators.
    Deduplicates results based on company name and normalized title.
    """
    all_jobs = []

    # 1. First fetch directly from LinkedIn public portal
    linkedin_jobs = fetch_linkedin_public_jobs(query, location, limit=15)
    all_jobs.extend(linkedin_jobs)

    # 2. If SerpApi key is provided, fetch Google Jobs (Naukri, Indeed, etc.)
    if SERPAPI_KEY:
        google_jobs = fetch_serpapi_google_jobs(query, location, limit=20)
        all_jobs.extend(google_jobs)

    # Deduplicate
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        key = (j.get("company", "").strip().lower(), j.get("title", "").strip().lower()[:25])
        if key not in seen and j.get("title") and j.get("company"):
            seen.add(key)
            unique_jobs.append(j)

    return unique_jobs

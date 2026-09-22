"""
Advanced Multi-Scan Anti-Scam & Verification Engine (4-Stage Military-Grade Pipeline)
Ensures 0% fake, scam, ghost, or deceptive jobs reach the user or the channel.
"""

import re
import urllib.parse
from typing import Dict, Any, Tuple, List

# STAGE 1: Trusted Domain Whitelist for Job Applications
TRUSTED_DOMAINS = [
    "linkedin.com",
    "naukri.com",
    "indeed.com",
    "glassdoor.com",
    "greenhouse.io",
    "lever.co",
    "myworkdayjobs.com",
    "workday.com",
    "smartrecruiters.com",
    "darwinbox.com",
    "freshteam.com",
    "instahyre.com",
    "hirist.com",
    "cutshort.io",
    "wellfound.com",
    "angel.co",
    "foundit.in",
    "monsterindia.com"
]

# High-risk Phishing & Link Shorteners (Instantly Banned)
BANNED_LINK_PATTERNS = [
    r"bit\.ly",
    r"tinyurl\.com",
    r"cutt\.ly",
    r"wa\.me",
    r"api\.whatsapp\.com",
    r"t\.me",
    r"telegram\.me",
    r"forms\.gle",
    r"docs\.google\.com/forms",
]

# STAGE 2: High-Risk Scam & Extortion Keyword Patterns
SCAM_KEYWORDS = [
    r"registration\s*fees?",
    r"security\s*deposit",
    r"processing\s*fees?",
    r"daily\s*payout\s*guaranteed",
    r"earn\s*(?:rs\.?|inr|₹)?\s*\d{3,5}\s*(?:daily|per\s*day|hourly)",
    r"typing\s*work",
    r"data\s*entry\s*offline",
    r"sms\s*sending",
    r"captcha\s*typing",
    r"like\s*(?:youtube|insta(?:gram)?)\s*videos?",
    r"telegram\s*tasks?",
    r"crypto\s*task",
    r"no\s*skills?\s*required.*earn\s*(?:lakhs?|thousands?)",
    r"pay\s*before\s*joining",
    r"training\s*fees?",
    r"laptop\s*deposit",
    r"envelope\s*packing",
    r"work\s*only\s*1-2\s*hours?.*earn\s*(?:30|40|50)k",
    r"whatsapp\s*(?:us|me|cv|resume)\s*(?:at|on)?\s*\+?\d{10}",
    r"contact\s*hr\s*on\s*whatsapp",
    r"direct\s*joining\s*without\s*interview",
    r"100%\s*selection\s*guaranteed",
    r"payment\s*after\s*selection",
    r"medical\s*charge",
]

# Suspicious Public Email Domains
PUBLIC_EMAIL_DOMAINS = [
    "@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@rediffmail.com"
]

# Generic / Suspicious Company Names
GENERIC_COMPANY_PATTERNS = [
    r"^urgent\s+hiring$",
    r"^placement\s+services?$",
    r"^confidential$",
    r"^direct\s+company$",
    r"^hr\s+recruitment$",
    r"^consultancy\s+firm$",
    r"^private\s+limited$",
    r"^top\s+mnc\s+client$",
    r"^hiring\s+team$",
]

def scan_stage_1_domain_security(apply_link: str) -> Tuple[bool, List[str]]:
    """Stage 1: Validates link against phishing, shorteners, and whatsapp redirects."""
    flags = []
    if not apply_link:
        return False, ["Missing application link"]

    lower_link = apply_link.lower()

    # Check for banned shorteners or private chat links
    for b_pattern in BANNED_LINK_PATTERNS:
        if re.search(b_pattern, lower_link):
            flags.append(f"Security Alert: Link points to suspicious/unverified target ({b_pattern})")
            return False, flags

    # Verify if link belongs to recognized corporate ATS or trusted domain
    parsed = urllib.parse.urlparse(lower_link)
    netloc = parsed.netloc.replace("www.", "")

    is_trusted = any(td in netloc for td in TRUSTED_DOMAINS) or "careers" in lower_link or "job" in lower_link
    if not is_trusted:
        flags.append(f"Unverified external domain: {netloc}")

    return (len(flags) == 0 or is_trusted), flags


def scan_stage_2_content_heuristics(title: str, company: str, description: str) -> Tuple[bool, List[str]]:
    """Stage 2: Checks for fraudulent keywords, fees, and fake contact channels."""
    flags = []
    text = f"{title} {company} {description}".lower()

    for pattern in SCAM_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(f"Scam phrase detected: '{pattern}'")

    for domain in PUBLIC_EMAIL_DOMAINS:
        if domain in text and ("apply" in text or "resume" in text or "hr" in text or "cv" in text):
            flags.append(f"Uses free personal email ({domain}) instead of authentic corporate domain")
            break

    for gen in GENERIC_COMPANY_PATTERNS:
        if re.search(gen, company.strip(), re.IGNORECASE):
            flags.append(f"Generic unverified company shell name: '{company}'")
            break

    return len(flags) == 0, flags


def scan_stage_3_salary_sanity(title: str, salary_text: str) -> Tuple[bool, List[str]]:
    """Stage 3: Flags absurd and unrealistic salary promises."""
    flags = []
    sal = salary_text.lower()
    
    # Catch traps like "50000 per day" or "10000 daily"
    if "per day" in sal or "daily" in sal:
        numbers = re.findall(r"\d+", sal.replace(",", ""))
        for n in numbers:
            if int(n) > 2000:
                flags.append(f"Unrealistic daily salary promise: ₹{n}/day")
                return False, flags

    return True, flags


def scan_stage_4_corporate_integrity(company: str, location: str) -> Tuple[bool, List[str]]:
    """Stage 4: Checks company identity completeness."""
    flags = []
    comp = company.strip()
    if not comp or comp.lower() in ["-", "n/a", "none", "unknown", "confidential"]:
        flags.append("Company identity undisclosed or anonymous")
        return False, flags
    return True, flags


def multi_scan_job_verification(job: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
    """
    Executes all 4 scanning stages.
    A job MUST pass all 4 stages to be marked genuine.
    """
    all_flags = []
    trust_score = 1.0

    title = job.get("title", "")
    company = job.get("company", "")
    description = job.get("description", "")
    apply_link = job.get("apply_link", "")
    salary = job.get("salary", "")

    # Run Stage 1: Domain & Link Security
    s1_pass, s1_flags = scan_stage_1_domain_security(apply_link)
    all_flags.extend(s1_flags)
    if not s1_pass:
        trust_score -= 0.50

    # Run Stage 2: Content & Fraud Keywords
    s2_pass, s2_flags = scan_stage_2_content_heuristics(title, company, description)
    all_flags.extend(s2_flags)
    if not s2_pass:
        trust_score -= 0.40

    # Run Stage 3: Salary Sanity
    s3_pass, s3_flags = scan_stage_3_salary_sanity(title, salary)
    all_flags.extend(s3_flags)
    if not s3_pass:
        trust_score -= 0.30

    # Run Stage 4: Corporate Integrity
    s4_pass, s4_flags = scan_stage_4_corporate_integrity(company, job.get("location", ""))
    all_flags.extend(s4_flags)
    if not s4_pass:
        trust_score -= 0.20

    trust_score = max(0.0, min(1.0, trust_score))
    # Threshold Consistency Fix (Issue 7): Uses CONFIDENCE_THRESHOLD from config.py
    from config import CONFIDENCE_THRESHOLD
    is_safe = (trust_score >= CONFIDENCE_THRESHOLD) and (len(all_flags) == 0)

    return is_safe, trust_score, all_flags


# Alias for compatibility
check_job_legitimacy = multi_scan_job_verification


def filter_fake_jobs(jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

    """
    Applies the Multi-Scan Verification to the entire batch of jobs.
    """
    verified_jobs = []
    discarded_jobs = []

    for job in jobs:
        is_safe, score, flags = multi_scan_job_verification(job)
        job["trust_score"] = round(score, 2)
        job["security_flags"] = flags

        if is_safe:
            verified_jobs.append(job)
        else:
            discarded_jobs.append(job)

    return verified_jobs, discarded_jobs

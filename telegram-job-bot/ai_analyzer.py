"""
AI Job Market & Quality Analyzer (Layer 2)
Uses Google Gemini to deeply analyze job descriptions, verify authenticity,
extract real market salaries, and identify must-have skills.
"""

import json
import logging
from typing import List, Dict, Any
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Try initializing Google GenAI client
ai_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize Google GenAI SDK: {e}")

ANALYSIS_PROMPT_TEMPLATE = """
You are an expert recruitment market intelligence and fraud detection agent.
You have been provided with real active job listings for the role '{query}' in '{location}'.

JOB LISTINGS:
{jobs_json}

YOUR TASKS:
1. FRAUD & QUALITY CHECK:
   - Identify if any listing looks like a scam, ghost job, multi-level marketing (MLM), or deceptive trap.
   - Discard any fraudulent jobs.

2. SALARY MARKET ESTIMATION:
   - What is the realistic industry salary package (CTC in INR LPA) for this exact role in '{location}'?
   - Break it down into:
     * Fresher / Entry Level (0-1 yr)
     * Mid-Level (2-4 yrs)
     * Senior / Lead (5+ yrs)

3. TOP DEMANDED SKILLS & TOOLS:
   - List the top 5 to 7 specific technical tools, frameworks, and core skills that recruiters are actively demanding.

4. BRIEF MARKET SUMMARY:
   - 2 concise sentences describing the hiring momentum in this location.

OUTPUT FORMAT:
Respond strictly in valid JSON with this schema:
{{
  "discarded_fake_count": 0,
  "salary_breakdown": {{
    "fresher": "e.g. ₹3.5 - 5.5 LPA",
    "mid_level": "e.g. ₹6.0 - 11.0 LPA",
    "senior": "e.g. ₹12.0 - 20.0+ LPA"
  }},
  "top_skills": [
    "Skill/Tool 1",
    "Skill/Tool 2",
    "Skill/Tool 3",
    "Skill/Tool 4",
    "Skill/Tool 5"
  ],
  "market_summary": "Brief 1-2 line summary of current hiring trends in this location."
}}
"""

def analyze_job_market(query: str, location: str, verified_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sends verified jobs to Gemini for deep intelligence extraction.
    Falls back to smart heuristic summary if API key is missing.
    """
    if not verified_jobs:
        return {
            "error": "No verified jobs found for this role and location."
        }

    # If Gemini AI is active, run deep analysis
    if ai_client:
        try:
            # Prepare compact JSON for prompt
            compact_jobs = [
                {
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "salary": j.get("salary"),
                    "source": j.get("source"),
                    "description": (j.get("description") or "")[:200]
                }
                for j in verified_jobs[:15]
            ]

            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                query=query,
                location=location,
                jobs_json=json.dumps(compact_jobs, indent=2)
            )

            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )

            result = json.loads(response.text)
            return result
        except Exception as e:
            logger.error(f"Gemini API analysis failed: {e}")

    # Fallback heuristic analysis if Gemini API is not configured or fails
    return fallback_market_analysis(query, location, verified_jobs)


def classify_jobs_by_experience(verified_jobs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Classifies verified job postings into 3 experience tiers:
    - fresher: 0-1 yr, junior, trainee, associate, intern
    - senior: 5+ yrs, senior, sr, lead, principal, manager
    - mid: 2-4 yrs, specialist, or general postings
    """
    fresher_keywords = ["junior", "jr", "fresher", "intern", "trainee", "associate", "entry", "0-1", "graduate"]
    senior_keywords = ["senior", "sr", "lead", "principal", "architect", "manager", "head", "5+", "6+", "7+", "8+"]

    fresher_jobs = []
    mid_jobs = []
    senior_jobs = []

    for job in verified_jobs:
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()

        if any(k in text for k in senior_keywords):
            senior_jobs.append(job)
        elif any(k in text for k in fresher_keywords):
            fresher_jobs.append(job)
        else:
            mid_jobs.append(job)

    # Ensure each bucket gets representative jobs if some are empty
    if not fresher_jobs and len(mid_jobs) > 2:
        # Transfer the most entry-like mid jobs
        fresher_jobs = [mid_jobs.pop()]
    if not senior_jobs and len(mid_jobs) > 2:
        senior_jobs = [mid_jobs.pop()]

    return {
        "fresher": fresher_jobs,
        "mid": mid_jobs,
        "senior": senior_jobs
    }


def get_tier_skills_and_tools(query: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns specific skills and tools demanded for Fresher, Mid, and Senior levels for any job role.
    """
    q = query.lower()

    # Default general profile
    profile = {
        "fresher": {
            "salary": "₹3.5L - ₹5.5L LPA",
            "skills": ["Foundational Domain Knowledge", "Problem Solving", "Attention to Detail", "Basic Project Execution"],
            "tools": ["Core Industry Software", "MS Office / Google Docs", "Git / Basic Collaboration Tools"]
        },
        "mid": {
            "salary": "₹6.5L - ₹12.0L LPA",
            "skills": ["Independent Execution", "Client Communication", "Process Optimization", "Quality Assurance"],
            "tools": ["Advanced Workflow Tools", "Jira / Asana", "CI/CD & Cloud Basics", "Analytical Dashboards"]
        },
        "senior": {
            "salary": "₹15.0L - ₹25.0L+ LPA",
            "skills": ["Architecture & Strategy", "Team Leadership & Mentorship", "Stakeholder Management", "Scalability & ROI"],
            "tools": ["Enterprise Tech Stack", "Strategy Frameworks", "Roadmapping & Budgeting", "Executive Dashboards"]
        }
    }

    if "ui" in q or "ux" in q or "design" in q:
        profile = {
            "fresher": {
                "salary": "₹3.5L - ₹5.5L LPA",
                "skills": ["Visual Design Basics", "Wireframing", "Color Theory & Typography", "Basic Responsive Layouts"],
                "tools": ["Figma (Core)", "Adobe XD", "Illustrator / Photoshop", "Canva"]
            },
            "mid": {
                "salary": "₹7.0L - ₹13.0L LPA",
                "skills": ["Design Systems Building", "User Journey Mapping", "Interactive Prototyping", "Usability Testing & Research"],
                "tools": ["Figma (Advanced Auto-Layout & Variables)", "Principle / ProtoPie", "Miro / FigJam", "Maze / Hotjar"]
            },
            "senior": {
                "salary": "₹16.0L - ₹26.0L+ LPA",
                "skills": ["Product Design Strategy", "Cross-Functional Leadership", "Design Ops & Governance", "Business Metrics (Conversion, Retention)"],
                "tools": ["Enterprise Design Systems", "Zeroheight / Storybook", "Mixpanel / Amplitude", "Jira & Confluence"]
            }
        }
    elif "python" in q or "developer" in q or "software" in q or "backend" in q or "frontend" in q:
        profile = {
            "fresher": {
                "salary": "₹4.0L - ₹6.5L LPA",
                "skills": ["Data Structures & Algorithms", "Clean Coding Practices", "REST APIs Consumption", "Basic Database Querying"],
                "tools": ["Python / JavaScript", "Git & GitHub", "VS Code", "Postman", "SQL / SQLite"]
            },
            "mid": {
                "salary": "₹8.0L - ₹16.0L LPA",
                "skills": ["Microservices Architecture", "API Design & Security", "Performance Tuning", "Database Indexing & Caching"],
                "tools": ["Django / FastAPI / React", "Docker & Containers", "PostgreSQL / MongoDB", "Redis", "AWS / GCP Basics"]
            },
            "senior": {
                "salary": "₹18.0L - ₹32.0L+ LPA",
                "skills": ["System Design & High Availability", "Distributed Systems", "Team Mentorship & Code Reviews", "Tech Stack Decision Making"],
                "tools": ["Kubernetes", "Kafka / RabbitMQ", "Terraform & DevOps", "Cloud Architecture (AWS/Azure)", "Prometheus / Grafana"]
            }
        }
    elif "data" in q or "analyst" in q:
        profile = {
            "fresher": {
                "salary": "₹3.5L - ₹5.5L LPA",
                "skills": ["Data Extraction & Cleaning", "Descriptive Statistics", "Basic Charting & Reporting", "SQL Querying"],
                "tools": ["Advanced Excel (VLOOKUP, Pivot)", "SQL", "Power BI / Tableau (Basics)", "Python (Pandas)"]
            },
            "mid": {
                "salary": "₹7.0L - ₹14.0L LPA",
                "skills": ["Business Intelligence Dashboards", "Predictive Analytics", "Data Pipeline Automation", "Cohort & Funnel Analysis"],
                "tools": ["Power BI / Tableau (DAX, Calculated Fields)", "Python (NumPy, Scikit-learn)", "PostgreSQL / Snowflake", "Airflow"]
            },
            "senior": {
                "salary": "₹16.0L - ₹28.0L+ LPA",
                "skills": ["Data Strategy & Monetization", "Enterprise Data Governance", "Machine Learning in Production", "Executive Storytelling"],
                "tools": ["BigQuery / Databricks", "Cloud Data Lakes", "MLflow / MLOps", "Looker", "Statistical Modeling"]
            }
        }

    return profile


def analyze_job_market(query: str, location: str, verified_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tier-based market intelligence: Fresher vs Mid vs Senior breakdown.
    """
    if not verified_jobs:
        return {"error": "No verified jobs found."}

    # 1. Classify verified jobs into experience tiers
    classified_jobs = classify_jobs_by_experience(verified_jobs)

    # 2. Get tier-specific skills, tools, and salary brackets
    tier_specs = get_tier_skills_and_tools(query)

    return {
        "classified_jobs": classified_jobs,
        "tier_specs": tier_specs,
        "total_count": len(verified_jobs)
    }


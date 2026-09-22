"""
AI Job Market & Quality Analyzer
Uses Google Gemini AI (when GEMINI_API_KEY is configured) to deeply analyze
real job descriptions, dynamically extract real market salaries, and identify must-have skills.
Falls back seamlessly to smart heuristic benchmarks if Gemini is unavailable.
"""

import json
import logging
from typing import List, Dict, Any
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Try initializing Google GenAI client
ai_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        from google import genai
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Google Gemini AI client successfully initialized.")
    except Exception as e:
        logger.warning(f"Could not initialize Google GenAI SDK: {e}")

ANALYSIS_PROMPT_TEMPLATE = """
You are an expert recruitment market intelligence and fraud detection agent.
You have been provided with real active job listings for the role '{query}' in '{location}'.

JOB LISTINGS:
{jobs_json}

YOUR TASKS:
1. SALARY MARKET ESTIMATION:
   - What is the realistic industry salary package (CTC in INR LPA) for this exact role in '{location}'?
   - Break it down into:
     * fresher (0-1 yr exp): e.g. "₹3.5L - ₹5.5L LPA"
     * mid (2-4 yrs exp): e.g. "₹7.0L - ₹13.0L LPA"
     * senior (5+ yrs exp): e.g. "₹16.0L - ₹26.0L+ LPA"

2. TOP DEMANDED SKILLS & TOOLS:
   - List the top 3-4 specific skills and top 3-4 tools for each tier (fresher, mid, senior) that recruiters in these listings are actively demanding.

OUTPUT FORMAT:
Respond strictly in valid JSON with this exact schema:
{{
  "tier_specs": {{
    "fresher": {{
      "salary": "₹X.XL - ₹Y.YL LPA",
      "skills": ["Skill 1", "Skill 2", "Skill 3"],
      "tools": ["Tool 1", "Tool 2", "Tool 3"]
    }},
    "mid": {{
      "salary": "₹X.XL - ₹Y.YL LPA",
      "skills": ["Skill 1", "Skill 2", "Skill 3"],
      "tools": ["Tool 1", "Tool 2", "Tool 3"]
    }},
    "senior": {{
      "salary": "₹X.XL - ₹Y.YL LPA",
      "skills": ["Skill 1", "Skill 2", "Skill 3"],
      "tools": ["Tool 1", "Tool 2", "Tool 3"]
    }}
  }}
}}
"""


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

    if not fresher_jobs and len(mid_jobs) > 2:
        fresher_jobs = [mid_jobs.pop()]
    if not senior_jobs and len(mid_jobs) > 2:
        senior_jobs = [mid_jobs.pop()]

    return {
        "fresher": fresher_jobs,
        "mid": mid_jobs,
        "senior": senior_jobs
    }


def get_heuristic_tier_specs(query: str) -> Dict[str, Dict[str, Any]]:
    """Heuristic fallback specifications if Gemini AI is not configured or fails."""
    q = query.lower()

    if any(k in q for k in ["ui", "ux", "design"]):
        return {
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
    elif any(k in q for k in ["python", "developer", "software", "backend", "frontend", "engineer"]):
        return {
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
    elif any(k in q for k in ["data", "analyst"]):
        return {
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

    return {
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


def analyze_job_market(query: str, location: str, verified_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tier-based market intelligence: Fresher vs Mid vs Senior breakdown.
    FIX (Issue 3): Actually invokes Google Gemini AI when key is provided!
    Falls back gracefully to smart heuristic specs if AI is offline or key is absent.
    """
    if not verified_jobs:
        return {"error": "No verified jobs found."}

    # 1. Classify verified jobs into experience tiers
    classified_jobs = classify_jobs_by_experience(verified_jobs)

    # 2. Extract dynamic tier specifications via Gemini AI if available
    tier_specs = None
    if ai_client:
        try:
            compact_jobs = [
                {
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "salary": j.get("salary"),
                    "location": j.get("location"),
                    "description": (j.get("description") or "")[:180]
                }
                for j in verified_jobs[:10]
            ]
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                query=query,
                location=location,
                jobs_json=json.dumps(compact_jobs, indent=2)
            )
            response = ai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            parsed = json.loads(response.text)
            if "tier_specs" in parsed and "fresher" in parsed["tier_specs"]:
                tier_specs = parsed["tier_specs"]
                logger.info(f"Successfully generated Gemini AI market intelligence for '{query}' in '{location}'")
        except Exception as e:
            logger.warning(f"Gemini AI extraction failed: {e}. Using resilient heuristic fallback.")

    # 3. Fallback to heuristic specs if AI was not run or didn't return tier_specs
    if not tier_specs:
        tier_specs = get_heuristic_tier_specs(query)

    return {
        "classified_jobs": classified_jobs,
        "tier_specs": tier_specs,
        "total_count": len(verified_jobs)
    }

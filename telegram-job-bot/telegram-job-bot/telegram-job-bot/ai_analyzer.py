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


def get_tier_skills_and_tools(query: str) -> Dict[str, Dict[str, Any]]:
    """Distinct skills (knowledge) and tools (software) for each experience tier."""
    q = query.lower()

    if any(k in q for k in ["ui", "ux", "design"]):
        return {
            "fresher": {
                "salary": "₹3.5L - ₹5.5L LPA",
                "skills": [
                    "Visual Design Basics",
                    "Wireframing & Mockups",
                    "Color Theory & Typography",
                    "Responsive Layouts"
                ],
                "tools": [
                    "Figma (Basic)",
                    "Adobe XD",
                    "Canva",
                    "Photoshop (Basic)"
                ]
            },
            "mid": {
                "salary": "₹7.0L - ₹13.0L LPA",
                "skills": [
                    "Design Systems Building",
                    "User Journey Mapping",
                    "Interactive Prototyping",
                    "Usability Testing"
                ],
                "tools": [
                    "Figma (Auto-Layout, Variables)",
                    "ProtoPie / Principle",
                    "Maze / Hotjar",
                    "Miro / FigJam"
                ]
            },
            "senior": {
                "salary": "₹16.0L - ₹26.0L+ LPA",
                "skills": [
                    "Product Design Strategy",
                    "Cross-Functional Leadership",
                    "Design Ops & Governance",
                    "Business Metrics (Conversion)"
                ],
                "tools": [
                    "Enterprise Design Systems",
                    "Zeroheight / Storybook",
                    "Mixpanel / Amplitude",
                    "Jira & Confluence"
                ]
            }
        }

    if any(k in q for k in ["data", "analyst"]):
        return {
            "fresher": {
                "salary": "₹3.5L - ₹5.5L LPA",
                "skills": [
                    "Data Cleaning & Wrangling",
                    "Descriptive Statistics",
                    "Basic SQL Querying",
                    "Reporting Fundamentals"
                ],
                "tools": [
                    "Advanced Excel (VLOOKUP, Pivot)",
                    "SQL / MySQL",
                    "Power BI (Basic)",
                    "Python (Pandas)"
                ]
            },
            "mid": {
                "salary": "₹7.0L - ₹14.0L LPA",
                "skills": [
                    "Predictive Modeling Basics",
                    "Automated Data Pipelines",
                    "Cohort & Funnel Analysis",
                    "Executive Storytelling"
                ],
                "tools": [
                    "Power BI / Tableau (Advanced DAX)",
                    "PostgreSQL / Snowflake",
                    "Python (NumPy, Scikit-learn)",
                    "Airflow"
                ]
            },
            "senior": {
                "salary": "₹16.0L - ₹28.0L+ LPA",
                "skills": [
                    "Data Monetization Strategy",
                    "Enterprise Data Governance",
                    "High-Throughput Analytics",
                    "Cross-Functional Data Leadership"
                ],
                "tools": [
                    "BigQuery / Databricks",
                    "Cloud Data Lakes (AWS/GCP)",
                    "MLflow / MLOps",
                    "Looker"
                ]
            }
        }

    # Default (Software Developer / Engineering / Other)
    return {
        "fresher": {
            "salary": "₹3.5L - ₹5.5L LPA",
            "skills": [
                "Core Language Basics",
                "Problem Solving & DSA",
                "REST API Consumption",
                "Git & Clean Code Basics"
            ],
            "tools": [
                "VS Code",
                "Git & GitHub",
                "Postman",
                "Linux CLI Basics"
            ]
        },
        "mid": {
            "salary": "₹6.5L - ₹12.0L LPA",
            "skills": [
                "System Design Basics",
                "API Development & Security",
                "Database Indexing & Caching",
                "Testing (Unit + Integration)"
            ],
            "tools": [
                "Docker",
                "Jenkins / GitHub Actions",
                "PostgreSQL / MongoDB",
                "AWS / GCP Basics"
            ]
        },
        "senior": {
            "salary": "₹15.0L - ₹25.0L+ LPA",
            "skills": [
                "Architecture & Scalability",
                "Team Leadership & Code Governance",
                "Stakeholder Management",
                "System Design at Scale"
            ],
            "tools": [
                "Kubernetes",
                "Terraform / IaC",
                "Observability (Grafana/Datadog)",
                "Kafka / RabbitMQ"
            ]
        }
    }

get_heuristic_tier_specs = get_tier_skills_and_tools


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

import json

from backend.ai_service import client
from backend.config import GROQ_MODEL
from backend.schemas import JDAnalysis


def build_jd_analysis_prompt(job_description: str) -> str:
    return f"""
You are an expert technical recruiter and job description analyst
working for KAIROS, an AI-powered recruitment assistant.

Your task is to understand a job description and extract only the
requirements that are relevant for evaluating a candidate.

JOB DESCRIPTION:
<job_description>
{job_description}
</job_description>

YOUR ANALYSIS TASKS:

1. IDENTIFY THE ROLE
   - Extract the actual job title.
   - Identify its broader role category.
   - Examples: Software Development, Backend Development,
     Frontend Development, Full Stack Development, Data Science.
   - Identify the seniority level: Internship, Entry-Level,
     Junior, Mid-Level, Senior or Lead.

2. EXTRACT TECHNICAL REQUIREMENTS
   - Identify explicitly mentioned technical skills.
   - Assign importance: high, medium or low.
   - Consider responsibilities to identify implicit technical
     capabilities only when reasonably supported by the JD.
   - Do not invent technologies or mandatory requirements.
   - Avoid duplicate skills.

3. EXTRACT SOFT SKILLS
   - Identify explicitly mentioned human and interpersonal skills.
   - Infer reasonable soft skills from responsibilities when
     clearly supported.
   - Examples: teamwork, communication, curiosity for learning,
     adaptability and attention to detail.
   - Do not assume every desirable soft skill is mandatory.

4. ANALYZE RESPONSIBILITIES
   - Convert responsibilities into concise, meaningful capabilities.
   - Examples: feature development, debugging, testing,
     documentation and code reviews.
   - Avoid treating every sentence as a separate requirement.
   - Avoid duplicate or overly generic responsibilities.

5. EDUCATION AND EXPERIENCE
   - Extract actual education requirements.
   - Extract experience requirements.
   - Distinguish mandatory requirements from preferences.
   - Do not penalize candidates for experience that is not required.

6. IGNORE IRRELEVANT INFORMATION
   Do not include administrative or organizational information
   in matching requirements.

   Examples:
   - Reporting Span
   - Influence Level
   - Organizational designation
   - Product: Not Applicable
   - Internal department classifications

IMPORTANT RULES:

- Analyze the meaning of the JD, not just individual keywords.
- Do not invent skills or requirements.
- Do not treat every responsibility as a mandatory skill.
- Give greater importance to core job requirements.
- Do not create requirements just to make the extracted list longer.
- If a category is not mentioned, return an empty list.
- Use concise, standardized skill names.
- Return valid JSON only.

OUTPUT FORMAT:

Return a JSON object matching this structure:

{{
    "role_title": "Job title",
    "role_category": "Broader role category",
    "seniority": "Entry-Level",

    "technical_requirements": [
        {{
            "skill": "Data Structures and Algorithms",
            "importance": "high",
            "description": "Core programming fundamentals"
        }}
    ],

    "soft_skill_requirements": [
        {{
            "skill": "Curiosity for Learning",
            "importance": "high",
            "description": "Willingness to learn new technologies"
        }}
    ],

    "responsibilities": [
        "Feature Development",
        "Debugging",
        "Testing"
    ],

    "education_requirement": "BTech",
    "experience_requirement": "Entry-Level",

    "non_relevant_information": [
        "Reporting Span"
    ]
}}

Return only the JSON object.
"""


def analyze_job_description(job_description: str) -> JDAnalysis:

    if not client:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    if not job_description or len(job_description.strip()) < 30:
        raise ValueError(
            "Please provide a meaningful job description."
        )

    prompt = build_jd_analysis_prompt(job_description)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise job description analyst. "
                    "Return valid JSON matching the requested schema."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "The AI returned an empty JD analysis."
        )

    try:
        analysis_data = json.loads(content)
        analysis = JDAnalysis.model_validate(analysis_data)

    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            f"Unable to validate AI-generated JD analysis: {error}"
        ) from error

    return analysis
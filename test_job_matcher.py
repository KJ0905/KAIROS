
from backend.schemas import Resume
from backend.job_matcher import calculate_job_match

resume = Resume(
    name="Test Candidate",
    skills=["Python", "FastAPI", "React"],
    projects=[
        "Built a real-time chat application using Node.js and WebSockets"
    ],
)

job_description = """
We need a software engineer with Python, FastAPI, SQL, Docker,
React, and experience building backend APIs.
"""

result = calculate_job_match(resume, job_description)

print("Match score:", result["match_score"], "%")
print("Matched keywords:", result["matched_keywords"])
print("Missing keywords:", result["missing_keywords"])
print("Explanation:", result["explanation"])

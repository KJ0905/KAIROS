from backend.jd_analyzer import analyze_job_description


jd = """
Role Title: Software Developer / IT Associate Tech Engineer

This is an entry-level role focused on executing clearly
defined tasks and contributing to software projects.

Responsibilities:
- Implement features and modules.
- Write code, debug, test and document software.
- Participate in code reviews.
- Collaborate with cross-functional teams.

Skills:
- Data Structures and Algorithms
- Full Stack
- CI/CD Tools
- Curiosity for Learning
- Attention to Detail

Education: BTech
Experience: Not applicable
"""

analysis = analyze_job_description(jd)

print(analysis.model_dump_json(indent=2))
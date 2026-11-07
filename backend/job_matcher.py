
import re

from backend.schemas import Resume


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "has", "have", "in", "is", "it", "of", "on", "or",
    "our", "that", "the", "this", "to", "was", "will", "with",
    "we", "you", "your", "their", "they", "who", "which",
    "candidate", "experience", "years", "work", "working",
    "skills", "skill", "ability", "strong", "knowledge",
}


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]*", text.lower())
    return {word.strip(".") for word in words if word not in STOP_WORDS and len(word) > 1}


def resume_to_text(resume: Resume) -> str:
    parts = [
        resume.name or "",
        " ".join(resume.skills),
        " ".join(resume.education),
        " ".join(resume.projects),
        " ".join(resume.achievements),
        " ".join(resume.sportsprogramming),
    ]

    for experience in resume.experiences:
        parts.extend([
            experience.company or "",
            experience.role or "",
            experience.duration or "",
            experience.description or "",
            " ".join(experience.skills_used),
        ])

    return " ".join(parts)


def calculate_job_match(
    resume: Resume,
    job_description: str,
) -> dict:
    resume_words = tokenize(resume_to_text(resume))
    job_words = tokenize(job_description)

    if not job_words:
        raise ValueError("The job description contains no usable keywords.")

    matched = sorted(resume_words & job_words)
    missing = sorted(job_words - resume_words)

    score = round(len(matched) / len(job_words) * 100)

    return {
        "match_score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "total_job_keywords": len(job_words),
        "matched_keyword_count": len(matched),
        "explanation": (
            "This score measures keyword overlap only. "
            "It is not a measure of overall candidate suitability."
        ),
    }

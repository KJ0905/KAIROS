
import re

from backend.schemas import Resume, PersonalProfile, JDAnalysis


# ==================================================
# 1. SKILL RELATIONSHIPS
# ==================================================

RELATED_SKILLS = {
    "Backend Development": [
        "Node.js",
        "Express.js",
        "REST APIs",
        "PostgreSQL",
        "MongoDB",
        "Prisma",
        "Authentication",
        "WebSockets",
    ],
    "Frontend Development": [
        "React",
        "Next.js",
        "TypeScript",
        "JavaScript",
        "HTML",
        "CSS",
    ],
    "Full Stack Development": [
        "React",
        "Node.js",
        "Express.js",
        "REST APIs",
        "PostgreSQL",
        "MongoDB",
        "Prisma",
        "Authentication",
    ],
    "Software Development": [
        "Git",
        "GitHub",
        "Debugging",
        "Testing",
        "Problem Solving",
        "Database Design",
    ],
    "Data Science": [
        "Python",
        "Machine Learning",
        "Data Analysis",
        "Statistics",
    ],
}


SKILL_ALIASES = {
    "data structures and algorithms": [
        "dsa",
        "data structures",
        "algorithms",
        "competitive programming",
    ],
    "full stack development": [
        "full stack",
        "fullstack",
        "frontend and backend",
    ],
    "backend development": [
        "backend",
        "back end",
        "server side development",
    ],
    "frontend development": [
        "frontend",
        "front end",
        "client side development",
    ],
    "ci cd tools": [
        "ci cd",
        "continuous integration",
        "continuous deployment",
        "continuous delivery",
        "github actions",
    ],
    "ci cd": [
        "continuous integration",
        "continuous deployment",
        "continuous delivery",
        "github actions",
    ],
    "database management": [
        "database design",
        "database systems",
        "sql",
    ],
    "software development": [
        "software engineering",
        "application development",
    ],
    "problem solving": [
        "analytical thinking",
        "critical thinking",
    ],
    "curiosity for learning": [
        "eager to learn",
        "quick learner",
        "continuous learning",
        "willingness to learn",
        "learn new technologies",
    ],
    "attention to detail": [
        "detail oriented",
        "attention to details",
    ],
    "teamwork": [
        "collaboration",
        "collaborative",
        "team player",
        "cross functional collaboration",
    ],
    "collaboration": [
        "teamwork",
        "collaborative",
        "team player",
        "worked with team",
        "cross functional collaboration",
    ],
    "adaptability": [
        "flexibility",
        "adapt to change",
    ],
    "team collaboration": [
        "teamwork",
        "collaboration",
        "collaborative",
        "team player",
        "worked with team",
        "cross functional collaboration",
    ],
}


# Responsibility labels mapped to equivalent phrases.
# These are used to find evidence in the resume.

RESPONSIBILITY_EVIDENCE = {
    "feature development": [
        "developed features",
        "built features",
        "implemented features",
        "developed modules",
        "built applications",
        "application development",
        "software development",
    ],
    "code implementation": [
        "implemented",
        "wrote code",
        "developed software",
        "built backend",
        "built frontend",
        "implemented apis",
        "developed application",
    ],
    "debugging": [
        "debugged",
        "fixed bugs",
        "troubleshooting",
        "resolved errors",
        "bug fixing",
    ],
    "testing": [
        "unit tests",
        "integration tests",
        "tested applications",
        "testing",
        "validated functionality",
    ],
    "documentation": [
        "technical documentation",
        "documented code",
        "api documentation",
        "wrote documentation",
    ],
    "code reviews": [
        "code review",
        "reviewed code",
        "peer review",
    ],
    "design discussions": [
        "system design",
        "software architecture",
        "technical design",
        "design decisions",
    ],
    "collaboration with cross functional stakeholders": [
        "collaborated with team",
        "team collaboration",
        "worked with team",
        "cross functional collaboration",
        "collaborative project",
    ],
}


# Soft skills mapped to phrases that can demonstrate them.

SOFT_SKILL_EVIDENCE = {
    "curiosity for learning": [
        "eager to learn",
        "quick learner",
        "continuous learning",
        "willingness to learn",
        "learned new technologies",
        "explored new technologies",
        "adaptability and learning",
    ],
    "attention to detail": [
        "attention to detail",
        "detail oriented",
        "careful implementation",
        "thorough testing",
        "quality assurance",
        "careful code review",
    ],
    "collaboration": [
        "collaboration",
        "collaborated",
        "teamwork",
        "team player",
        "worked with team",
        "cross functional",
    ],
    "communication": [
        "communication",
        "presented ideas",
        "technical discussions",
        "explained technical concepts",
        "communicated effectively",
    ],
}

# ==================================================
# EVIDENCE EXTRACTION
# ==================================================

# def get_candidate_evidence(
#     requirement: str,
#     resume: Resume,
#     personal_profile: PersonalProfile | None = None,
#     is_soft_skill: bool = False,
# ) -> list[dict]:

#     evidence = []

#     # Collect individual resume sections.
#     sources = []

#     for project in resume.projects:
#         sources.append({
#             "source": "Resume Project",
#             "title": project,
#         })

#     for experience in resume.experiences:
#         sources.append({
#             "source": "Work Experience",
#             "title": experience.role or experience.company or "Experience",
#             "text": " ".join([
#                 experience.description or "",
#                 " ".join(experience.skills_used),
#             ]),
#         })

#     # Include resume skills and achievements.
#     sources.append({
#         "source": "Resume Skills",
#         "title": "Technical Skills",
#         "text": " ".join(resume.skills),
#     })

#     sources.append({
#         "source": "Resume Achievements",
#         "title": "Achievements",
#         "text": " ".join(resume.achievements),
#     })

#     # Include personal profile evidence.
#     if personal_profile:
#         for experience in personal_profile.experiences:
#             sources.append({
#                 "source": "Personal Experience",
#                 "title": experience.title,
#                 "text": " ".join([
#                     experience.situation or "",
#                     experience.action or "",
#                     experience.result or "",
#                     " ".join(experience.skills_demonstrated),
#                 ]),
#             })

#         sources.append({
#             "source": "Personal Profile",
#             "title": "Personal Skills",
#             "text": " ".join(
#                 personal_profile.soft_skills
#                 + personal_profile.communication
#                 + personal_profile.teamwork
#                 + personal_profile.leadership
#                 + personal_profile.problem_solving
#                 + personal_profile.adaptability_and_learning
#                 + personal_profile.strengths
#             ),
#         })

#     # Determine phrases that can support this requirement.
#     phrases = [requirement]

#     phrases.extend(get_aliases(requirement))

#     if is_soft_skill:
#         phrases.extend(
#             SOFT_SKILL_EVIDENCE.get(
#                 normalize(requirement),
#                 [],
#             )
#         )

#     # Find evidence in each source.
#     for item in sources:

#         text = item.get("text", item.get("title", ""))

#         if not text:
#             continue

#         matched_phrases = [
#             phrase
#             for phrase in phrases
#             if contains_phrase(text, phrase)
#         ]

#         if matched_phrases:
#             evidence.append({
#                 "source": item["source"],
#                 "title": item["title"],
#                 "snippet": text,
#                 "matched_phrase": matched_phrases[0],
#             })

#     return evidence


def get_candidate_evidence(
    requirement: str,
    resume: Resume,
    personal_profile: PersonalProfile | None = None,
    is_soft_skill: bool = False,
) -> list[dict]:

    evidence = []
    sources = []

    # ------------------------------------------
    # 1. RESUME PROJECTS
    # ------------------------------------------

    for project in resume.projects:
        project_text = project.strip()

        # Separate project name from description.
        parts = re.split(r"[:—–]", project_text, maxsplit=1)

        title = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""

        sources.append({
            "source": "Resume Project",
            "title": title,
            "text": project_text,
        })

    # ------------------------------------------
    # 2. WORK EXPERIENCE
    # ------------------------------------------

    for experience in resume.experiences:
        text = " ".join([
            experience.description or "",
            " ".join(experience.skills_used),
        ]).strip()

        sources.append({
            "source": "Work Experience",
            "title": experience.role or experience.company or "Experience",
            "text": text,
        })

    # ------------------------------------------
    # 3. RESUME SKILLS AND ACHIEVEMENTS
    # ------------------------------------------

    sources.append({
        "source": "Resume Skills",
        "title": "Technical Skills",
        "text": " ".join(resume.skills),
    })

    sources.append({
        "source": "Resume Achievements",
        "title": "Achievements",
        "text": " ".join(resume.achievements),
    })

    # ------------------------------------------
    # 4. PERSONAL KNOWLEDGE BASE
    # ------------------------------------------

    if personal_profile:

        profile_categories = [
            ("Personality Traits", personal_profile.personality_traits),
            ("Strengths", personal_profile.strengths),
            ("Soft Skills", personal_profile.soft_skills),
            ("Communication", personal_profile.communication),
            ("Teamwork", personal_profile.teamwork),
            ("Leadership", personal_profile.leadership),
            ("Problem Solving", personal_profile.problem_solving),
            ("Adaptability and Learning",
             personal_profile.adaptability_and_learning),
            ("Work Style", personal_profile.work_style),
        ]

        for category, values in profile_categories:
            if values:
                sources.append({
                    "source": "Personal Profile",
                    "title": category,
                    "text": " ".join(values),
                })

        # Personal experiences
        for experience in personal_profile.experiences:

            text = " ".join([
                experience.situation or "",
                experience.action or "",
                experience.result or "",
                " ".join(experience.skills_demonstrated),
            ]).strip()

            sources.append({
                "source": "Personal Experience",
                "title": experience.title,
                "text": text,
            })

    # ------------------------------------------
    # 5. DETERMINE SUPPORTING PHRASES
    # ------------------------------------------

    phrases = [requirement]
    phrases.extend(get_aliases(requirement))

    if is_soft_skill:
        phrases.extend(
            SOFT_SKILL_EVIDENCE.get(
                normalize(requirement),
                [],
            )
        )

    # ------------------------------------------
    # 6. FIND AND FORMAT EVIDENCE
    # ------------------------------------------

    for item in sources:

        text = item["text"]

        if not text:
            continue

        matched_phrases = [
            phrase
            for phrase in phrases
            if contains_phrase(text, phrase)
        ]

        if not matched_phrases:
            continue

        matched_phrase = matched_phrases[0]

        # Split text into sentences to provide
        # concise evidence wherever possible.
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        matching_sentences = [
            sentence.strip()
            for sentence in sentences
            if any(
                contains_phrase(sentence, phrase)
                for phrase in matched_phrases
            )
        ]

        snippet = (
            " ".join(matching_sentences)
            if matching_sentences
            else text
        )

        evidence.append({
            "source": item["source"],
            "title": item["title"],
            "snippet": snippet,
            "matched_phrase": matched_phrase,
        })

    return evidence


IMPORTANCE_WEIGHTS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


# ==================================================
# 2. CONVERT CANDIDATE INFORMATION INTO TEXT
# ==================================================

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


def personal_profile_to_text(
    profile: PersonalProfile | None,
) -> str:

    if profile is None:
        return ""

    parts = [
        profile.introduction or "",
        " ".join(profile.personality_traits),
        " ".join(profile.strengths),
        " ".join(profile.soft_skills),
        " ".join(profile.communication),
        " ".join(profile.teamwork),
        " ".join(profile.leadership),
        " ".join(profile.problem_solving),
        " ".join(profile.adaptability_and_learning),
        " ".join(profile.work_style),
    ]

    for experience in profile.experiences:
        parts.extend([
            experience.title or "",
            experience.situation or "",
            experience.action or "",
            experience.result or "",
            " ".join(experience.skills_demonstrated),
        ])

    # areas_to_improve is intentionally excluded
    # because improvement areas are not positive evidence.

    return " ".join(parts)


# ==================================================
# 3. TEXT MATCHING UTILITIES
# ==================================================

def normalize(text: str) -> str:

    return re.sub(
        r"[^a-z0-9+#.]+",
        " ",
        text.lower(),
    ).strip()


def contains_phrase(text: str, phrase: str) -> bool:

    normalized_text = normalize(text)
    normalized_phrase = normalize(phrase)

    if not normalized_phrase:
        return False

    return bool(
        re.search(
            r"(?<![a-z0-9])"
            + re.escape(normalized_phrase)
            + r"(?![a-z0-9])",
            normalized_text,
        )
    )


def get_aliases(requirement: str) -> list[str]:

    normalized_requirement = normalize(requirement)

    # Normalize dictionary keys too, so punctuation
    # differences such as CI/CD do not break lookup.

    for key, aliases in SKILL_ALIASES.items():
        if normalize(key) == normalized_requirement:
            return aliases

    return []


def requirement_matches(
    requirement: str,
    description: str | None,
    candidate_text: str,
) -> bool:

    # 1. Exact requirement match
    if contains_phrase(candidate_text, requirement):
        return True

    # 2. Known synonyms and aliases
    aliases = get_aliases(requirement)

    if any(
        contains_phrase(candidate_text, alias)
        for alias in aliases
    ):
        return True

    # Do not use loose word overlap.
    # It can produce false positives.

    return False


# ==================================================
# 4. RESPONSIBILITY MATCHING
# ==================================================

def responsibility_matches(
    responsibility: str,
    candidate_text: str,
) -> bool:

    normalized_responsibility = normalize(responsibility)

    # Check exact phrase first.
    if contains_phrase(candidate_text, responsibility):
        return True

    # Check known equivalent phrases.
    evidence_phrases = RESPONSIBILITY_EVIDENCE.get(
        normalized_responsibility,
        [],
    )

    return any(
        contains_phrase(candidate_text, phrase)
        for phrase in evidence_phrases
    )


# ==================================================
# 5. SOFT SKILL MATCHING
# ==================================================

def soft_skill_matches(
    requirement: str,
    candidate_text: str,
) -> bool:

    normalized_requirement = normalize(requirement)

    # Exact match
    if contains_phrase(candidate_text, requirement):
        return True

    # Known aliases
    aliases = get_aliases(requirement)

    if any(
        contains_phrase(candidate_text, alias)
        for alias in aliases
    ):
        return True

    # Additional evidence phrases
    evidence_phrases = SOFT_SKILL_EVIDENCE.get(
        normalized_requirement,
        [],
    )

    return any(
        contains_phrase(candidate_text, phrase)
        for phrase in evidence_phrases
    )


# ==================================================
# 6. WEIGHTED SCORE CALCULATION
# ==================================================

def calculate_weighted_score(
    requirements,
    matched_names: list[str],
) -> int:

    if not requirements:
        return 0

    total_weight = 0
    matched_weight = 0

    for requirement in requirements:

        weight = IMPORTANCE_WEIGHTS.get(
            requirement.importance.lower(),
            2,
        )

        total_weight += weight

        if requirement.skill in matched_names:
            matched_weight += weight

    if total_weight == 0:
        return 0

    return round(
        matched_weight / total_weight * 100
    )


# ==================================================
# 7. DEVELOPMENT OPPORTUNITY DETAILS
# ==================================================

def build_development_opportunities(
    requirements,
    matched_names: list[str],
) -> list[dict]:

    opportunities = []

    for requirement in requirements:

        if requirement.skill in matched_names:
            continue

        opportunities.append({
            "skill": requirement.skill,
            "importance": requirement.importance,
            "description": (
                requirement.description
                or f"The job description expects {requirement.skill}."
            ),
            "suggestion": (
                f"Build practical experience with {requirement.skill} "
                f"through a relevant project or hands-on practice."
            ),
        })

    return opportunities


# ==================================================
# 8. MAIN JOB MATCHING FUNCTION
# ==================================================

def calculate_job_match(
    resume: Resume,
    job_analysis: JDAnalysis,
    personal_profile: PersonalProfile | None = None,
) -> dict:

    resume_text = resume_to_text(resume)

    personal_text = personal_profile_to_text(
        personal_profile
    )

    combined_personal_evidence = (
        resume_text + " " + personal_text
    )

    # --------------------------------------------------
    # A. TECHNICAL SKILL MATCHING
    # --------------------------------------------------

    technical_requirements = (
        job_analysis.technical_requirements
    )

    matched_technical = []
    technical_evidence = []

    for requirement in technical_requirements:

        if requirement_matches(
            requirement.skill,
            requirement.description,
            resume_text,
        ):
            matched_technical.append(requirement.skill)

            evidence = get_candidate_evidence(
                requirement=requirement.skill,
                resume=resume,
                personal_profile=None,
                is_soft_skill=False,
            )

            technical_evidence.append({
                "skill": requirement.skill,
                "importance": requirement.importance,
                "evidence": evidence,
            })

    development_opportunities = [
        requirement.skill
        for requirement in technical_requirements
        if requirement.skill not in matched_technical
    ]

    technical_score = calculate_weighted_score(
        technical_requirements,
        matched_technical,
    )

    development_opportunity_details = (
        build_development_opportunities(
            technical_requirements,
            matched_technical,
        )
    )

    # --------------------------------------------------
    # B. PERSONAL / SOFT SKILL MATCHING
    # --------------------------------------------------

    personal_requirements = (
        job_analysis.soft_skill_requirements
    )

    matched_soft = []
    personal_evidence = []

    for requirement in personal_requirements:

        if soft_skill_matches(
            requirement.skill,
            combined_personal_evidence,
        ):
            matched_soft.append(requirement.skill)

            evidence = get_candidate_evidence(
                requirement=requirement.skill,
                resume=resume,
                personal_profile=personal_profile,
                is_soft_skill=True,
            )

            personal_evidence.append({
                "skill": requirement.skill,
                "importance": requirement.importance,
                "evidence": evidence,
            })

    missing_personal = [
        requirement.skill
        for requirement in personal_requirements
        if requirement.skill not in matched_soft
    ]

    personal_score = calculate_weighted_score(
        personal_requirements,
        matched_soft,
    )

    # --------------------------------------------------
    # C. ROLE SUITABILITY
    # --------------------------------------------------

    role_category = job_analysis.role_category
    responsibilities = job_analysis.responsibilities

    # Keep responsibility matching for informational purposes only.
    matched_responsibilities = [
        responsibility
        for responsibility in responsibilities
        if responsibility_matches(
            responsibility,
            resume_text,
        )
    ]

    # Role suitability is calculated using technical
    # and personal skills match.

    role_components = []

    if technical_requirements:
        role_components.append((technical_score, 0.50))

    if personal_requirements:
        role_components.append((personal_score, 0.20))

    if role_components:
        total_role_weight = sum(
            weight for _, weight in role_components
        )

        role_score = round(
            sum(
                score * weight
                for score, weight in role_components
            ) / total_role_weight
        )
    else:
        role_score = 0

    # --------------------------------------------------
    # D. OVERALL WEIGHTED SCORE
    # --------------------------------------------------

    # Role suitability already combines technical and
    # personal match, so it represents the overall score.
    # Do not count it again as a separate component.

    overall_score = role_score

    # --------------------------------------------------
    # E. RELATED SKILLS
    # --------------------------------------------------

    related_skills = set()

    for skill in RELATED_SKILLS.get(role_category, []):

        if contains_phrase(resume_text, skill):

            if skill not in matched_technical:
                related_skills.add(skill)

    # Related skills are informational only.
    # They do not contribute to any score.

    # --------------------------------------------------
    # F. MATCH VERDICT
    # --------------------------------------------------

    if overall_score >= 80:
        verdict = "Excellent Match"

    elif overall_score >= 65:
        verdict = "Strong Match"

    elif overall_score >= 45:
        verdict = "Moderate Match"

    else:
        verdict = "Low Match"

    # --------------------------------------------------
    # G. ROLE ASSESSMENT
    # --------------------------------------------------

    role_assessment = (
        f"The candidate is being evaluated for the "
        f"{job_analysis.role_title} role in "
        f"{role_category}. Based on the technical match "
        f"of {technical_score}% and personal skills match "
        f"of {personal_score}%, the candidate has a "
        f"role suitability score of {role_score}%."
    )

    # --------------------------------------------------
    # H. EXPLANATION
    # --------------------------------------------------

    explanation = (
        f"{verdict}. The candidate matched "
        f"{len(matched_technical)} of "
        f"{len(technical_requirements)} technical requirements "
        f"and {len(matched_soft)} of "
        f"{len(personal_requirements)} personal requirements. "
        f"Based on these results, role suitability is "
        f"{role_score}%."
    )

    # --------------------------------------------------
    # I. FINAL RESPONSE
    # --------------------------------------------------

    matched_keywords = sorted(
        set(matched_technical + matched_soft)
    )

    return {

        # Scores
        "match_score": overall_score,
        "technical_match_score": technical_score,
        "personal_match_score": personal_score,
        "role_match_score": role_score,

        # Skill categories
        "matched_technical_skills": matched_technical,
        "related_skills": sorted(related_skills),
        "matched_soft_skills": matched_soft,
        "development_opportunities": development_opportunities,
        "development_opportunity_details": (
            development_opportunity_details
        ),
        "missing_personal_skills": missing_personal,
        "technical_evidence": technical_evidence,
        "personal_evidence": personal_evidence,

        # Role analysis
        "role": job_analysis.role_title,
        "role_category": role_category,
        "role_assessment": role_assessment,
        "matched_responsibilities": matched_responsibilities,
        "verdict": verdict,

        # Explanation
        "explanation": explanation,

        # Preserve existing frontend response fields
        "matched_keywords": matched_keywords,
        "matched_resume_keywords": matched_technical,
        "matched_personal_keywords": matched_soft,
        "missing_keywords": (
            development_opportunities + missing_personal
        ),

        "total_job_keywords": (
            len(technical_requirements)
            + len(personal_requirements)
        ),

        "matched_keyword_count": len(matched_keywords),
    }

from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = Field(default_factory=list)

class ProjectLinks(BaseModel):
    name: str
    github: str | None = None
    demo: str | None = None
    other_links: list[str] = Field(default_factory=list)

class ProfileLinks(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    codeforces: str | None = None
    codechef: str | None = None
    atcoder: str | None = None
    portfolio: str | None = None
    other_links: list[str] = Field(default_factory=list)


class PersonalExperience(BaseModel):
    title: str
    situation: str | None = None
    action: str | None = None
    result: str | None = None
    skills_demonstrated: list[str] = Field(default_factory=list)


class PersonalProfile(BaseModel):
    # General information
    introduction: str | None = None
    personality_traits: list[str] = Field(default_factory=list)

    # Personal strengths and development areas
    strengths: list[str] = Field(default_factory=list)
    areas_to_improve: list[str] = Field(default_factory=list)

    # Soft skills
    soft_skills: list[str] = Field(default_factory=list)
    communication: list[str] = Field(default_factory=list)
    teamwork: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    problem_solving: list[str] = Field(default_factory=list)
    adaptability_and_learning: list[str] = Field(default_factory=list)

    # Evidence and experiences
    experiences: list[PersonalExperience] = Field(default_factory=list)

    # Career preferences
    work_style: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    career_goals: list[str] = Field(default_factory=list)


class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    rollno: str | None = None
    total_experience_years: float | None = None

    skills: list[str] = Field(default_factory=list)
    sportsprogramming: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    profile_links: ProfileLinks = Field(default_factory=ProfileLinks)
    project_links: list[ProjectLinks] = Field(default_factory=list)


class ChatRequest(BaseModel):
    conversation_id: str
    question: str = Field(min_length=1, max_length=4000)


class NewConversationRequest(BaseModel):
    pass


class JobMatchRequest(BaseModel):
    job_description: str = Field(min_length=30, max_length=12000)

# --------------------------------------------------
# Job Description Analysis Schemas
# --------------------------------------------------

class JDRequirement(BaseModel):
    skill: str
    importance: str = "medium"  # high, medium, low
    description: str | None = None


class JDAnalysis(BaseModel):
    role_title: str
    role_category: str
    seniority: str | None = None

    # Technical requirements extracted from the JD
    technical_requirements: list[JDRequirement] = Field(
        default_factory=list
    )

    # Personal and soft skill requirements
    soft_skill_requirements: list[JDRequirement] = Field(
        default_factory=list
    )

    # Responsibilities converted into relevant capabilities
    responsibilities: list[str] = Field(
        default_factory=list
    )

    # Education and experience requirements
    education_requirement: str | None = None
    experience_requirement: str | None = None

    # Information that should not affect matching scores
    non_relevant_information: list[str] = Field(
        default_factory=list
    )


class JDAnalysisResponse(BaseModel):
    analysis: JDAnalysis
    analysis_summary: str | None = None

class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)

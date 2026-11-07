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


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)

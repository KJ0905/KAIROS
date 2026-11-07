
from backend.ai_service import generate_answer
from backend.schemas import Resume

resume = Resume(
    name="Test Candidate",
    skills=["Python", "FastAPI", "React"],
    projects=["Built a real-time chat application using React and Node.js"],
)

answer = generate_answer(
    resume=resume,
    conversation_history=[],
    question="Which skills does this candidate have?",
)

print(answer)

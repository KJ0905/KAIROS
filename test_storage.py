
from backend.schemas import Resume
from backend.storage import (
    save_candidate,
    get_candidate,
    create_conversation,
    get_conversation,
    save_conversation,
)

resume = Resume(
    name="Test Candidate",
    email="test@example.com",
    skills=["Python", "FastAPI"],
)

candidate_id = save_candidate(resume, "test_resume.pdf")
print("Candidate ID:", candidate_id)

candidate = get_candidate(candidate_id)
print("Candidate name:", candidate["resume"]["name"])

conversation_id = create_conversation(candidate_id)
conversation = get_conversation(conversation_id)

conversation["messages"].append({
    "role": "user",
    "content": "What skills does this candidate have?",
})

save_conversation(conversation)

updated = get_conversation(conversation_id)
print("Saved messages:", updated["messages"])

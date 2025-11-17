# ai.py
import os
import json
from openai import OpenAI


# ============================================================
# Initialize HuggingFace Router Client
# ============================================================
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)


# ============================================================
# Utility: Safe JSON Parse
# ============================================================
def safe_json(text):
    try:
        return json.loads(text)
    except Exception:
        # Fallback into a generic structure
        return {"steps": {"Step 1": text}}


# ============================================================
# Generic AI JSON Response Caller
# Used by:
#   - weekly plan
#   - step explainer
#   - skill gap analysis
#   - mock interview
#   - roadmap chat wrapper
# ============================================================
def generate_ai_response(prompt):
    try:
        completion = client.chat.completions.create(
            model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
            messages=[
                {"role": "system", "content": "Return strictly valid JSON. No markdown, no ```."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.6,
        )

        output = completion.choices[0].message.content
        return safe_json(output)

    except Exception as e:
        print("AI Error:", e)
        return {"error": "AI generation failed", "details": str(e)}



# ============================================================
# Roadmap Generator (Core)
# ============================================================
def generate_ai_roadmap(user_id, career_name, reference_content=None, preferences={}):
    """
    Generate a personalized roadmap using LLaMA 4 model.
    MUST return ONLY:
    {
        "steps": {
            "Step 1": "...",
            "Step 2": "..."
        }
    }
    """

    # Prepare reference text
    if reference_content:
        steps_text = json.dumps(reference_content.get("steps", {}))
        if steps_text == "{}":
            steps_text = "No steps available in reference."
    else:
        steps_text = "None"

    # Strict JSON roadmap instruction
    system_prompt = """
    You are an expert career roadmap generator.

    Rules:
    - Return ONLY valid JSON.
    - No markdown, no ``` blocks.
    - Do NOT wrap the result in extra keys like "roadmap", "data", etc.
    - The ONLY valid output format is:

    {
        "steps": {
            "Step 1": "...",
            "Step 2": "...",
            "Step 3": "..."
        }
    }

    Steps must be detailed, practical, and personalized.
    Include tools, concepts, hands-on tasks, and references where useful.
    """

    user_prompt = (
        f"Career: {career_name}\n\n"
        f"Reference roadmap steps: {steps_text}\n\n"
        f"User preferences: {json.dumps(preferences)}\n\n"
        "Return ONLY JSON in the EXACT format:\n"
        "{ \"steps\": { \"Step 1\": \"...\", \"Step 2\": \"...\" } }"
    )

    try:
        completion = client.chat.completions.create(
            model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=700,
            temperature=0.6,
        )

        ai_message = completion.choices[0].message.content.strip()

        # Parse JSON safely
        try:
            roadmap_dict = json.loads(ai_message)
        except Exception:
            print("❌ JSON decode failed, returning fallback")
            roadmap_dict = {"steps": {"Step 1": ai_message}}

        return roadmap_dict

    except Exception as e:
        print("❌ Hugging Face API error:", e)
        return {"steps": {"Step 1": "AI generation failed, try again."}}



# ============================================================
# CHAT MODEL — Modify roadmap dynamically
# ============================================================
def roadmap_chat_ai(user_message, roadmap, preferences):
    """
    Chat mode for the split-screen UI.
    Two possible outputs:

    1️⃣ Normal chat:
        {
            "message": "answer..."
        }

    2️⃣ Roadmap update request:
        {
            "message": "I updated the roadmap.",
            "updated_roadmap": {
                "Step 1": "...",
                "Step 2": "..."
            }
        }
    """

    prompt = f"""
You are an AI Roadmap Mentor.

User is chatting about their roadmap.

Your tasks:
1. Answer questions clearly.
2. If user REQUESTS CHANGES, update the roadmap.
3. If NOT, return a normal message.

STRICT RULES:
- Always return valid JSON ONLY.
- No markdown.
- No ```.

If updating roadmap, respond ONLY as:
{{
  "message": "<your explanation>",
  "updated_roadmap": {{
      "Step 1": "...",
      "Step 2": "..."
  }}
}}

If NOT updating:
{{
  "message": "<your explanation>"
}}

------------------------------------
User message:
{user_message}

Current roadmap:
{json.dumps(roadmap)}

User preferences:
{json.dumps(preferences)}
------------------------------------
"""

    return generate_ai_response(prompt)

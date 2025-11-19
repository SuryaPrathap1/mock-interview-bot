from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import uuid
import os

app = Flask(__name__, template_folder="templates", static_folder="static")


GEMINI_KEY = os.environ.get("GEMINI_KEY", "gemini_key")
genai.configure(api_key=GEMINI_KEY)


SESSIONS = {}

def new_session():
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "chat": [],  
        "type": None,
        "topic": None
    }
    return sid

def get_session(sid):
    return SESSIONS.get(sid)

def generate_text_from_gemini(prompt, model_name="gemini-2.5-flash", max_output_tokens=512, temperature=0.2):
    try:
        model = genai.GenerativeModel(model_name)
        
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        
        return f"[MODEL_ERROR] {e}"


@app.route("/")
def index():
    sid = new_session()
    
    welcome = "Welcome to the interview panel. Select Technical, Managerial or HR round."
    
    SESSIONS[sid]["chat"].append({"role":"system", "content": "You are an interviewer AI. Follow instructions from the UI."})
    return render_template("index.html", session_id=sid, welcome_text=welcome)

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    sid = data.get("session_id")
    interview_type = data.get("type")
    topic = data.get("topic")  

    session = get_session(sid)
    if not session:
        return jsonify({"error":"session not found"}), 400

    session["type"] = interview_type
    session["topic"] = topic

    system_prompt = f"You are an interviewer conducting a {interview_type} interview."
    if interview_type == "TR" and topic:
        system_prompt += f" Focus on {topic}."
    system_prompt += (
        " Ask one question at a time. After each user answer, give brief feedback on:\n"
        "1) Content\n2) Modulation/Tone (infer from text)\n3) Confidence and score out of 10\nThen ask the next question. If user says 'end interview' provide a final summary with strengths, weaknesses and suggestions."
    )
   
    session["chat"].append({"role":"system", "content": system_prompt})

    
    prompt = system_prompt + "\n\nNow ask the first interview question."
    question = generate_text_from_gemini(prompt, model_name="gemini-2.5-flash")
    session["chat"].append({"role":"assistant", "content": question})
    return jsonify({"question": question})

@app.route("/answer", methods=["POST"])
def answer():
    data = request.json
    sid = data.get("session_id")
    user_text = data.get("answer", "")

    session = get_session(sid)
    if not session:
        return jsonify({"error":"session not found"}), 400

    session["chat"].append({"role":"user", "content": user_text})

    
    if user_text.strip().lower() in ["end", "exit", "end interview", "finish", "quit"]:
        
        chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in session["chat"]])
        prompt = chat_text + "\n\nProvide a final performance summary with strengths, weaknesses, suggestions, and an overall score out of 10."
        summary = generate_text_from_gemini(prompt, model_name="gemini-2.5-flash")
        session["chat"].append({"role":"assistant", "content": summary})
        return jsonify({"final": True, "summary": summary})

    
    context_msgs = session["chat"][-12:]
    context_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in context_msgs])

    prompt = (
        context_text +
        "\n\nFor the user's most recent answer, provide FEEDBACK (content, modulation/tone, confidence with score out of 10), then provide the NEXT QUESTION.\n"
        "Return both parts clearly labeled like:\nFEEDBACK:\n...\n\nQUESTION:\n..."
    )

    output = generate_text_from_gemini(prompt, model_name="gemini-2.5-flash")

    
    feedback = ""
    question = ""
    if "QUESTION:" in output.upper():
        
        idx = output.upper().rfind("QUESTION:")
        feedback = output[:idx].strip()
        question = output[idx+len("QUESTION:"):].strip()
        
        if feedback.upper().startswith("FEEDBACK:"):
            feedback = feedback.split(":",1)[1].strip()
    else:
        
        feedback = output.strip()
        q_prompt = "Now ask a single next interview question based on the conversation above."
        question = generate_text_from_gemini(context_text + "\n\n" + q_prompt, model_name="gemini-2.5-flash")

    session["chat"].append({"role":"assistant", "content": feedback})
    session["chat"].append({"role":"assistant", "content": question})

    return jsonify({"feedback": feedback, "next_question": question})

if __name__ == "__main__":
    
    app.run(debug=True)

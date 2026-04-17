from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Required for your frontend to communicate with this API
import time
import os
import traceback
from groq import Groq

app = Flask(__name__)

# Allow your frontend domain to make requests to this backend
CORS(app)

# Pull the API key from the server environment, NEVER hardcode it
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = None
def initialize_client():
    global client
    try:
        if not GROQ_API_KEY:
            print("✗ Error: GROQ_API_KEY environment variable not set.")
            return False
        client = Groq(api_key=GROQ_API_KEY)
        print("✓ Groq client initialized")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

initialize_client()

SYSTEM_PROMPT = """You are 'AeroBot', the official AI assistant for the Tejastra Aeromodelling Club.

RESPONSE RULES:
1. Be concise: 1-2 sentences for direct questions, 3-4 for "explain" requests
2. Use markdown formatting
3. Key formulas: Wing Loading = Weight/Area, RPM = KV×V, Max Current = Ah×C-Rating, ESC = Motor Amps × 1.3

Examples:
Q: "What is ESC?" → "An ESC (Electronic Speed Controller) regulates power from battery to motor. It controls throttle response and protects against voltage spikes."
Q: "Explain ESC" → "An Electronic Speed Controller manages power flow between battery and brushless motor. It converts DC to three-phase AC and regulates speed. Always match ESC rating to 130% of motor max current."""

@app.route("/")
def home():
    return "AeroBot Backend is Running!"
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    # --- THE FIX: Intercept the browser's invisible CORS preflight ping ---
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS ok"}), 200
        
    # --- Normal Chat Logic Continues ---
    if not client:
        return jsonify({"error": "AI client not initialized"}), 503
    
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400
        
        user_message = data["message"].strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        start_time = time.time()
        
        msg_lower = user_message.lower()
        is_explain = any(word in msg_lower for word in ["explain", "tell me about", "describe", "elaborate", "book callback", "virtual campus tour"])
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=600 if is_explain else 180,
            temperature=0.1
        )
        
        response_text = chat_completion.choices[0].message.content
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            "response": response_text,
            "processing_time_ms": processing_time
        })
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
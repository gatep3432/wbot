from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get all credentials from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Validate required environment variables
required_vars = {
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
    "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN
}

for var_name, var_value in required_vars.items():
    if not var_value:
        raise ValueError(f"❌ Missing required environment variable: {var_name}")

print("🔑 All credentials loaded successfully!")

# Initialize Flask app
app = Flask(__name__)

# Enhanced system prompt
system_prompt = """
You are an AI Assistant that provides helpful, friendly, and concise responses.
Keep your answers conversational and engaging while being informative.
"""

def get_ai_reply(user_input):
    """Get AI response from OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
    "model": "deepseek/deepseek-r1-distill-llama-70b:free",  # Upgraded to 70B!
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
        "max_tokens": 500,
        "temperature": 0.7
    }


    try:
        print(f"📤 Processing message: {user_input[:50]}...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        print(f"✅ OpenRouter Status: {response.status_code}")
        response.raise_for_status()
        
        ai_response = response.json()['choices'][0]['message']['content'].strip()
        return ai_response
        
    except requests.exceptions.Timeout:
        return "⏱️ Sorry, I'm thinking too hard right now. Try again in a moment!"
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenRouter API Error: {e}")
        return "🤖 I'm having some technical difficulties. Please try again later."
    except KeyError as e:
        print(f"❌ Unexpected API response format: {e}")
        return "🔧 Something went wrong processing your request. Please try again."

@app.route("/whatsapp", methods=["GET", "POST"])
def handle_whatsapp_message():
    """Handle incoming WhatsApp messages"""
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")
    
    print(f"📥 Message from {sender}: {incoming_msg}")
    
    # Create Twilio response
    resp = MessagingResponse()
    msg = resp.message()
    
    if incoming_msg:
        ai_reply = get_ai_reply(incoming_msg)
        msg.body(ai_reply)
        print(f"📤 Sending reply: {ai_reply[:50]}...")
    else:
        msg.body("👋 Hi there! Send me a message and I'll chat with you!")
    
    return str(resp)

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "WhatsApp AI Bot"}, 200
@app.route('/')
def home():
    return 'Bot is running 👋'
if __name__ == "__main__":
    print("🚀 Starting WhatsApp AI Bot...")
    app.run(debug=True, host="0.0.0.0", port=5000)

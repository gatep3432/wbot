from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import requests
import os
from dotenv import load_dotenv
from flask_apscheduler import APScheduler
import pytz

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

# === Scheduler Setup ===
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def scheduled_whatsapp_message():
    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)
    from_whatsapp_number = 'whatsapp:+14155238886'  # Your Twilio WhatsApp number here (use sandbox number if testing)
    to_whatsapp_number = 'whatsapp:+919999999999'   # The recipient's number here, E.164 format

    try:
        message = client.messages.create(
            body="Hi bro",
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        print(f"✅ Scheduled message sent to {to_whatsapp_number}")
    except Exception as e:
        print(f"❌ Failed to send scheduled message: {e}")

# Set timezone for IST
IST = pytz.timezone('Asia/Kolkata')

# Schedule the message at 12:50 PM IST every day
scheduler.add_job(
    id='whatsapp_hi_bro',
    func=scheduled_whatsapp_message,
    trigger='cron',
    hour=12,
    minute=55,
    timezone=IST
)

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
        "model": "pygmalionai/mythalion-13b",
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
    if request.method == "GET":
        return "✅ WhatsApp bot is alive and waiting for messages.", 200

    # POST logic stays the same:
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")
    
    print(f"📥 Message from {sender}: {incoming_msg}")
    
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
    return {"status": "healthy", "service": "WhatsApp AI Bot"}, 200

@app.route('/')
def home():
    return 'Bot is running 👋'

if __name__ == "__main__":
    print("🚀 Starting WhatsApp AI Bot...")
    app.run(debug=True, host="0.0.0.0", port=5000)

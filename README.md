# 🤖 WhatsApp AI Assistant

This is a smart, AI-powered WhatsApp assistant built with **Flask**, **Twilio**, **MongoDB**, and **OpenAI**. It can onboard new users, manage sessions, handle customer service requests, and escalate conversations to human agents when needed — all through WhatsApp.

---

## 🧠 Features

- 💬 **AI Conversations** powered by OpenAI (ChatGPT)
- 📱 **WhatsApp Integration** using Twilio
- 🧾 **Smart Onboarding** (captures user info like name and email)
- 🗣️ **Escalation to Human Staff** based on intent or unknown queries
- 📦 **Session Persistence** using MongoDB
- 🔐 Secure setup via `.ini` configuration

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Flask** – Web framework
- **Twilio** – WhatsApp messaging API
- **MongoDB Atlas** – Cloud database
- **OpenAI** – ChatGPT for intelligent responses
- **ConfigParser** – Manages API keys and credentials

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/whatsapp-ai-assistant.git
cd whatsapp-ai-assistant
```
### 2. Install Dependencies

```bash
pip install -r requirements.txt
```
### 3. Configure Your .ini File
Create a config.ini file in the root directory with the following format:

```bash
[OPENAI]
APIKEY=your_openai_api_key

[MONGODB]
USERNAME=your_mongodb_username
PASSWORD=your_mongodb_password

[TWILLIO]
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth
TWILIO_NUMBER=whatsapp:+your_twilio_number
```

## 📩 Webhook Configuration
In your Twilio Console, set your WhatsApp number's webhook to the link of your deploy server.

## Project Structure
```
.
├── bot.py                     # Handles OpenAI chat logic
├── app.py                     # Main Flask server
├── config.ini                 # Configuration file (excluded from Git)
├── requirements.txt           # Project dependencies
└── README.md                  # You're here
```


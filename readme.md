# 🌾 MandiQ

> **AI-Powered Voice-Based Smart Procurement & Queue Management System for Agricultural Mandis**

> *"A farmer should know **when** to come, not **how long** to wait."*

Built for **Smart India Hackathon (SIH) 2026**

---

## 📌 Problem Statement

Farmers often wake up before dawn, load their produce onto tractors, travel long distances to agricultural mandis, and wait for hours—or sometimes even days—without knowing when their turn will actually come.

Existing systems mainly focus on farmer registration and procurement records but do not provide intelligent queue management or real-time arrival scheduling.

This results in:

- ⏳ Long waiting times
- 🚜 Fuel wastage
- 🚦 Traffic congestion around mandis
- 🌾 Crop quality degradation
- 😞 Farmer frustration and uncertainty

---

# 💡 Our Solution

MandiQ is an AI-powered multilingual voice-based procurement management system that allows farmers to book mandi procurement slots using a simple phone call.

Instead of requiring a smartphone or internet connection, farmers interact with the system using natural speech or keypad inputs.

The platform intelligently manages procurement queues, predicts waiting times, and informs farmers exactly when they should arrive.

If procurement is interrupted for any reason, mandi officials can immediately halt operations, automatically reschedule affected farmers, generate new tokens, and notify everyone through SMS and voice calls.

---

# ✨ Key Features

- 📞 Voice-based slot booking
- 🌐 Multilingual support
- 📱 Feature phone compatible
- 🎟 Smart token generation
- ⏱ Dynamic queue estimation
- 📊 Live mandi dashboard
- 🚨 HALT Procurement System
- 🔄 Automatic farmer rescheduling
- 📩 SMS notifications
- 🔊 Voice notifications
- 📈 Analytics dashboard
- ⚡ Real-time queue monitoring

---

# 🚜 How It Works

```text
Farmer

↓

Calls MandiQ

↓

Voice Agent

↓

Language Selection

↓

Booking Engine

↓

Queue Engine

↓

Slot Allocation

↓

Token Generation

↓

SMS Confirmation

↓

Live Dashboard

↓

HALT (if required)

↓

Automatic Rescheduling

↓

Voice + SMS Notification
```

---

# 🏗️ System Architecture

```text
                 Farmer

                    │

             Phone Call / DTMF

                    │

            Voice Processing Layer

                    │

          Booking & Queue Engine

                    │

              PostgreSQL Database

                    │

         Smart Mobilization Engine

                    │

        Live Dashboard & Analytics

                    │

       SMS / Voice Notifications
```

---

# 🧩 Core Modules

### 📞 Voice Agent

- Hindi voice interaction
- Speech-to-Text
- Text-to-Speech
- DTMF fallback
- Language selection

---

### 🎟 Booking Engine

- Slot allocation
- Token generation
- Capacity validation
- Double-booking prevention

---

### 📈 Queue Engine

- Queue calculation
- ETA prediction
- Waiting time estimation
- Live queue updates

---

### 🚨 HALT Procurement

A unique emergency management feature.

Whenever procurement stops unexpectedly due to equipment failure, weather, operational issues, or any other disruption, mandi staff can press a single **HALT** button.

The system automatically:

- Stops further processing
- Releases affected slots
- Generates new slots
- Assigns fresh token numbers
- Updates the dashboard
- Sends SMS notifications
- Schedules voice callbacks

---

### 📊 Dashboard

A live control room for mandi officials.

Features include:

- Live queue monitoring
- Active token tracking
- Waiting farmers
- Served farmers
- No-show tracking
- Exception Center
- HALT Procurement
- Analytics

---

### ⚠️ Exception Center

The dashboard continuously monitors operational issues.

Supported alerts:

- Farmer Delay
- Medical Emergency
- Vehicle Breakdown
- Road Block
- Weather Delay
- Queue Delay
- Smart Reschedule Suggestions

---

# 🛠 Tech Stack

| Layer | Technology |
|---------|------------|
| Frontend | React + Vite + TailwindCSS |
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| AI Voice | Sarvam AI |
| SMS | Twilio / Exotel (Prototype) |
| Deployment | Docker |
| Version Control | Git + GitHub |

---

# 📂 Repository Structure

```text
mandiq/

├── README.md
├── HACKATHON_PLAN.md
├── PROJECT_CONTEXT.md
├── API_CONTRACT.md
├── backend/
├── frontend/
├── docs/
├── scripts/
├── data/
└── docker-compose.yml
```

---

# 👥 Team

| Member | Responsibility |
|---------|----------------|
| Abhishek | Booking Engine & Database |
| Parv | Backend APIs & Queue Engine |
| Pushkar | Dashboard, Documentation & Deployment |
| Medhavi | Feature Phone Interface |
| Priyanshu | Voice Processing |
| Bhawana | Testing, Demo & Presentation |

---

# 🚀 Current Status

| Module | Status |
|----------|--------|
| Project Planning | ✅ |
| Database Design | 🚧 |
| Dashboard | 🚧 |
| Booking Engine | 🚧 |
| Queue Engine | 🚧 |
| Voice Integration | ⏳ |
| HALT System | ⏳ |
| Deployment | ⏳ |

---

# 🔮 Future Scope

- Government API Integration
- Weather-based Queue Prediction
- AI-based Procurement Forecasting
- WhatsApp Notifications
- GPS-assisted Arrival Prediction
- Multi-Mandi Support
- National Scale Deployment

---

# 🏆 Smart India Hackathon 2026

MandiQ is being developed as a prototype for the Smart India Hackathon with the goal of making agricultural procurement smarter, faster, and more farmer-friendly through AI-assisted voice technology.

---

# 📄 License

This repository is created for academic and Smart India Hackathon purposes.

© 2026 Team RootCause

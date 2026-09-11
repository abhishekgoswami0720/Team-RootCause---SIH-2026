# MandiQ — 48 Hour Battle Plan

**Team RootCause · Team ID 19 · SIH26032 · GLA University**

> Target: Top 10 of 60 → SIH Grand Finale

---

## Read this first (2 minutes)

### What we are building

A farmer calls one phone number. He speaks in Hindi (or presses keys). The system books him a mandi slot, gives him a token number, and tells him exactly when to come. Mandi staff get a dashboard to run the queue. If procurement suddenly stops, staff press one red button and every affected farmer is automatically rescheduled and notified.

**In one line:** BookMyShow for mandi slots, but over a normal phone call instead of an app.

### Why this matters

Farmers today load their tractor at 4 AM, drive to the mandi, and wait — sometimes 6 hours, sometimes 4 days. Nobody tells them when their turn is. Existing government portals *register* the farmer but never tell him **when to come**. That is the gap we fill.

### The one rule that governs everything

**AI never makes booking decisions.**

The AI only listens (speech → text) and speaks (text → speech). The actual decisions — which slot, which token, is it available — are made by plain, predictable code.

If a judge asks *"what if your AI hallucinates?"* the answer is:
**"The AI cannot book anything. Only our deterministic code touches the database."**

---

## Who does what

Six people, six tracks. Everybody owns one thing completely, end to end. Nobody waits for anybody.

### 1. Abhishek — Booking Engine (Team Lead)

**You own the heart of the system.**

- The database design (which tables, which columns)
- The `/book` endpoint — farmer's phone number goes in, slot + token comes out
- **Double-booking protection** — two farmers grabbing the last seat at the same millisecond
- The HALT feature — stop the mandi, move everyone, notify everyone
- Reviewing other people's code before it merges

**Why this is yours:** everything else depends on it. If booking breaks, nothing works.

---

### 2. Parv — Backend Support

**You own everything the dashboard and the phone read.**

- `/status/{phone}` — "where am I in the queue?"
- `/queue` — the full live list for the dashboard
- `/queue/update` — mark a farmer as served or no-show
- The wait-time calculation
- The notification pipeline — queue messages, track delivery, retry failures

**Why this matters:** Abhishek writes data in, you read data out. Two people, no collisions.

---

### 3. Pushkar — Staff Dashboard

**You own the screen the judges stare at longest.**

- Live queue table — token, farmer name, village, crop, slot time, status
- Stat boxes — Now serving / Waiting / Served / No-show
- "Served" and "No-show" buttons
- The red **HALT PROCUREMENT** button
- The alerts panel showing who got rescheduled and what message they received

**Design rule:** this is a control room, not a website. Dense, functional, high contrast. The HALT button is the only loud thing on the page.

**Start before the backend is ready** — build it with fake hardcoded data, swap in real API calls later.

---

### 4. Medhavi — Farmer's Phone

**You own the first 90 seconds of the demo.**

- A phone that looks like an actual **feature phone** — plastic body, small green LCD screen, physical keypad. Not a web form.
- The keypad flow: press 1 to book, press 2 for status
- The mic button for voice input
- The SMS panel — messages landing on the farmer's phone

**Why the feature phone look matters:** a judge sees it and instantly understands why an app would never reach these farmers. The design *is* the argument.

**Start before the backend is ready** — hardcoded fake responses first.

---

### 5. Priyanshu — Voice

**You own the hardest remaining piece.**

- **TTS (text → speech):** system speaks Hindi to the farmer. Sarvam AI.
- **ASR (speech → text):** farmer speaks, system understands. Sarvam AI.
- **NLU (understanding):** turn "मेरा गाँव नांगल है, फसल गेहूँ है" into `{"village": "Nangal", "crop": "Wheat"}`
- The fallback ladder (below) so nothing ever fully fails

**The voice ladder — never depend on one service:**

| Rung | What | When used |
|---|---|---|
| 1 | Sarvam AI | Normal — best quality |
| 2 | Browser speech | If Sarvam is down |
| 3 | Keypad | If both fail — always works |

**Never say numbers as standalone words.** "एक दबाइए" works; "1 दबाएँ" gets swallowed. Use the phrasing "स्लॉट बुक करना है, तो एक दबाइए।"

---

### 6. Bhawana — Data, Testing & Pitch

**You own whether a working prototype actually looks Top-10.**

This is not a small job. A flawless backend with a bad demo script loses to a decent backend with a great one.

- **Seed data:** 30 farmer names + phone numbers, 15 village names (Karnal/Patiala region), 4 crops, realistic slot timings. Three farmers on a dashboard looks like homework; thirty looks like a system.
- **Adversarial testing:** try to break it. Empty input. Wrong key. Booking twice. Full slots. Halt with nobody booked. Keep a bug list.
- **Demo script:** exactly what gets said and clicked, timed to 4 minutes.
- **Judge questions:** write 30 hard ones, we write the answers together.
- **Final PPT:** real screenshots from the working prototype.

**Pair up when idle:** help Pushkar with dashboard screens during the middle hours.

---

## Hard deadlines — miss these and we are in trouble

| By hour | This must be true |
|---|---|
| **H3** | Repo live, everyone pushing. Database tables created. Sarvam key working. |
| **H8** | `/book` returns a real token. Double-booking test passes. |
| **H14** | Phone books through the real API. Dashboard shows the real queue. |
| **H20** | HALT works end to end, notifications queued. |
| **H26** | Farmer can **speak** and get booked. |
| **H32** | 🔒 **FEATURE FREEZE** — bugs only from here. |
| **H36** | Backup video recorded. Build untouched. |
| **H44** | Demo rehearsed 3+ times. All 6 can explain their own module. |

---

## Hour by hour

### H0–H3 · Foundation

Everyone works in parallel. Nobody blocks anybody.

| Who | Task |
|---|---|
| Abhishek | Create repo + branches. Write `schema.sql`. Create tables. |
| Parv | Set up Python environment. Then pair with Abhishek on schema. |
| Pushkar | React project (Vite). Agree shared colours/fonts with Medhavi. Nav bar. |
| Medhavi | Phone shell — static LCD + keypad. No logic yet. |
| Priyanshu | Sarvam signup, API key, play one Hindi audio file successfully. |
| Bhawana | Write seed data into a Google Sheet — 30 farmers, 15 villages, 4 crops. |

**Gate at H3:** everyone has pushed at least once. Tables exist. Hindi audio plays.

---

### H3–H8 · Core engine

| Who | Task |
|---|---|
| Abhishek | `/book` endpoint. Double-booking protection. Race test script. |
| Parv | `/status`, `/queue`, `/queue/update`. |
| Pushkar | Dashboard layout with fake hardcoded data. |
| Medhavi | Keypad flow with fake hardcoded responses. |
| Priyanshu | `/speak` endpoint with audio caching. |
| Bhawana | Load seed data into the database. Write the testing checklist. |

**Gate at H8:** `/book` gives a token. Two simultaneous bookings for one seat → exactly one wins.

---

### H8–H14 · Integration ⚠️ the dangerous part

This is where teams lose hours. Fake data becomes real data and everything that can mismatch, will.

| Who | Task |
|---|---|
| Abhishek | Enable CORS. Review and merge both frontend branches. |
| Pushkar | Replace fake data with real `fetch()` calls. |
| Medhavi | Same — connect the phone to the real booking API. |
| Priyanshu | Wire `/speak` into the phone so it talks. |
| Parv | Wait-time calculation. Hindi message strings. |
| Bhawana | First full end-to-end test. Write down every bug. |

**Gate at H14:** book on the phone → row appears on the dashboard within 3 seconds.

> **CORS explained:** browsers block a page on one address from calling a server on another address. Our UI runs on port 5173, backend on 8000. Without CORS enabled, every request silently fails. One line of code fixes it.

---

### H14–H20 · The HALT feature (our differentiator)

| Who | Task |
|---|---|
| Abhishek | `/halt` — find affected farmers, free their seats, rebook them, reissue tokens. |
| Parv | Notifications table. Queue messages. Track delivery. |
| Pushkar | HALT button + confirmation + the alerts panel. |
| Medhavi | SMS inbox panel on the phone. |
| Priyanshu | Hindi voice message for the reschedule. |
| Bhawana | Test HALT with 20 bookings. Does everyone get moved? |

**Gate at H20:** one click moves every waiting farmer and generates their Hindi message.

**Important:** each rescheduled farmer gets a **new** token, because tokens are unique per day. The message says "नया टोकन" so he knows it changed.

---

### H20–H26 · Voice input (the new piece)

| Who | Task |
|---|---|
| Priyanshu + Abhishek | Mic → Sarvam ASR → extract village/crop → dialog engine → booking. |
| Medhavi | Mic button + "सुन रहे हैं…" listening state. |
| Parv | Match spoken village/crop names against the seed lists. |
| Pushkar | Dashboard polish. |
| Bhawana | Test 20 spoken phrases. Log which ones fail. |

**Gate at H26:** a farmer speaks Hindi and gets a booking, with keypad still working as fallback.

---

### H26–H32 · Proof & polish

| Who | Task |
|---|---|
| Abhishek | Make the race test a **visible screen** — two farmers, one seat, live on screen. |
| Everyone | Loading states, error messages, check it works on a small screen. |
| Bhawana | Break it deliberately: empty input, wrong crop, full slots, no-show, walk-in. |

**Gate at H32:** 🔒 **FEATURE FREEZE.** No new features. Bugs only.

> The most common way a working prototype dies is somebody adding "one small thing" at hour 40 and breaking the build an hour before judging.

---

### H32–H36 · Lock it down

- Fix only critical bugs
- **H34: record the backup video** — full demo, screen recording with audio
- **H35: zip everything, upload to Drive, final commit**

**Gate at H36:** video exists. Nobody touches the code again.

---

### H36–H48 · Pitch preparation

This is 12 full hours on presentation, and that is correct. Most teams give this 2 hours and lose because of it.

| Hours | Task |
|---|---|
| H36–38 | Write the demo script. Exact words, exact clicks, timed to 4 minutes. |
| H38–40 | Rehearsal 1 and 2. Fix what feels slow. |
| H40–42 | Judge Q&A — 30 hard questions, written answers, everyone learns them. |
| H42–44 | Update the PPT with real screenshots from the prototype. |
| H44–46 | Rehearsal 3 and 4. Full run with Q&A. |
| H46–48 | Buffer. Sleep. Do not code. |

---

## The demo — 4 minutes

| Time | What happens |
|---|---|
| 0:00–0:20 | **The problem.** One photo of a tractor queue. "He does not know when his turn is." |
| 0:20–1:30 | **Farmer books by voice.** Hindi speech → slot → token → SMS appears. |
| 1:30–2:00 | **Dashboard.** His booking appears live in the mandi queue. |
| 2:00–3:00 | **🔴 HALT.** Staff stops procurement. Every farmer rescheduled and notified in seconds. |
| 3:00–3:30 | **Engineering proof.** Two farmers race for the last seat. One wins, other auto-moved. |
| 3:30–4:00 | **Impact.** From an unknown wait to a known slot time. |

**Highest-impact moment:** the HALT. Everybody else built a booking system. Only we built one that handles the mandi breaking down.

---

## Things we say honestly, before judges ask

Judges reward teams who know exactly where the prototype ends and reality begins.

| Honest statement | Why we say it |
|---|---|
| Telephony is simulated in the browser | Real phone lines need KYC + DLT registration — weeks, not days. Architecture supports swapping in Exotel. |
| SMS is queued, not actually sent | DLT registration required by Indian telecom law. Pipeline is real; only the last hop is stubbed. |
| The dashboard is the source of truth for live mandi status | No public government API exists for live procurement data. |
| The farmer needs no internet — our servers obviously do | "Works without internet" means the farmer's side. |
| Dialect accuracy varies | Exactly why keypad fallback exists at every step. |
| We use polling, not WebSockets | Simpler and more reliable for one mandi. WebSockets when we scale. |

---

## Rules for the whole team

1. **Never** put an API key or password inside a `.py` or `.jsx` file. Only `.env`. Always `.gitignore` the `.env`.
2. **Never** screenshot or share `.env` contents.
3. Work on **your own branch**. Never push straight to `main`.
4. **Replace means:** Ctrl+A → Delete → paste. Not just paste. Then Ctrl+F to confirm the old version is gone. *(Duplicate pasted code cost us 40 minutes once already.)*
5. When something breaks, **read the terminal**, not the browser. The browser says "something failed." The terminal says what.
6. **Backup every 6 hours.** Zip → Drive. Takes 2 minutes.
7. Ask for help after **20 minutes** stuck. Not after 2 hours.

---

## Where to type what

| Place | What goes there |
|---|---|
| **Terminal** (Ctrl + ` in VS Code) | Commands: `pip`, `python`, `npm`, `cd`, `uvicorn` |
| **VS Code editor** | File contents: `.py`, `.jsx`, `.sql`, `.env` |
| **Browser** | Testing: `localhost:5173` (app), `127.0.0.1:8000/docs` (API) |

**Open backend and frontend in two separate VS Code windows.** Using File → Open Folder in the same window kills your running servers.

---

## Every person must be able to explain their own module

A judge will point at a random member and say "explain this part."

If Pushkar cannot explain the dashboard, the panel concludes the team did not build it. That suspicion costs more than any feature gains.

**Before H44, every person spends 10 minutes walking the others through their own code.** Non-negotiable.

---

## If things go wrong

| Problem | Do this |
|---|---|
| Internet dies | Local database + local servers. Already works offline. |
| Sarvam API dies | Browser speech, then keypad. Ladder handles it. |
| Laptop dies | Everything is on GitHub + Drive. Another member continues. |
| Demo breaks on stage | Play the backup video. Stay calm, keep talking. |
| Behind schedule at H14 | Cut the race-demo screen. **Never** cut the rehearsals. |

---

## One sentence to remember

**Every decision from here answers one question: does this increase our chance of Top 10?**

Adding a feature at hour 40 does not. Rehearsing the demo a fourth time does.

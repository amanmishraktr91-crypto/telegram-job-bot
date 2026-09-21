# 🤖 AI-Powered Telegram Job Market & Anti-Scam Bot

Ek highly advanced Telegram Bot jo kisi bhi Job Role aur Location (e.g. `UI/UX Designer Noida`) ke liye live market scan karta hai, **Fake/Scam jobs ko khud filter karke hata deta hai**, aur aapke **New Telegram Channel** par verified jobs, salary ranges, aur recruiter requirements broadcast karta hai.

---

## ✨ Features
1. **Multi-Source Aggregation:** LinkedIn, Google Jobs, Naukri, Indeed se live openings track karta hai.
2. **2-Layer Anti-Scam Engine:**
   - Registration fee, fake task scams, unverified recruiters, aur generic spam listings ko automatically block kar deta hai.
3. **AI Deep Market Analysis (Gemini):**
   - Fresher, Mid-Level aur Senior CTC package breakdown (in LPA).
   - Top 5-7 in-demand tools aur skills jo recruiters maang rahe hain.
4. **Direct Channel Broadcast:**
   - Kisi bhi new Telegram channel ka ID daal kar direct wahan automated alerts post kar sakte hain.

---

## 🚀 Setup Guide (Step-by-Step)

### Step 1: Telegram Par New Channel Banayein
1. Telegram open karein -> **New Channel** par click karein.
2. Channel ka naam rakhein (e.g., *Verified Tech Jobs India*).
3. Channel ko **Public** rakhein aur ek username chunen (e.g., `@my_new_job_channel`).
   *(Agar private banana chahein toh uska chat ID use kar sakte hain).*

### Step 2: Bot Banayein (@BotFather)
1. Telegram par `@BotFather` search karein aur `/newbot` bhejein.
2. Bot ka naam aur username rakhein.
3. Aapko ek **API Token** milega (e.g., `7123456789:AAH...`).

### Step 3: Bot Ko Apne New Channel Ka Admin Banayein
1. Apne New Channel ki settings mein jayein -> **Administrators** -> **Add Administrator**.
2. Apne naye bot ka username search karke select karein.
3. **"Post Messages"** permission ON karke save karein.

### Step 4: Environment Variables Configure Karein
`telegram-job-bot` folder mein `.env` file banayein (`.env.example` ko copy karke):

```env
TELEGRAM_BOT_TOKEN=7123456789:AAH_your_token_from_botfather
GEMINI_API_KEY=your_gemini_api_key_from_google_ai_studio
TELEGRAM_CHANNEL_ID=@my_new_job_channel
```

### Step 5: Dependencies Install Karein
```bash
cd C:\Users\Niroja\.gemini\antigravity\scratch\telegram-job-bot
pip install -r requirements.txt
```

### Step 6: Test & Run
Local pipeline test karne ke liye:
```bash
python test_pipeline.py "UI/UX Designer" "Noida"
```

Telegram Bot ko live run karne ke liye:
```bash
python telegram_bot.py
```

---

## 💬 Usage Examples
Bot ya Channel me jaakar simple text message bhejein:
- `UI/UX Designer Noida`
- `Python Developer Bangalore`
- `Data Analyst Delhi NCR`
- `Frontend Engineer Pune`

# 🚀 Evolution API - Quick Start Guide

**Get WhatsApp connected in 3 minutes!**

---

## ⚡ Super Fast Setup

### Step 1: Start Evolution API (30 seconds)

```bash
cd C:\Users\Ruan\Desktop\autopromo
docker compose up -d evolution-api
```

Wait ~30 seconds for initialization.

### Step 2: Generate QR Code (10 seconds)

```bash
cd backend
python scripts\setup_evolution_instance.py
```

This will create `qrcode_whatsapp.png` in the current directory.

### Step 3: Scan QR Code (30 seconds)

1. Open `qrcode_whatsapp.png`
2. Open WhatsApp on your phone
3. Go to: **Settings → Linked Devices → Link a Device**
4. Scan the QR Code
5. Done! ✅

---

## 🔍 Verify Connection

```bash
curl -H "apikey: f708f2fc-471f-4511-83c3-701229e766d5" http://localhost:8081/instance/connectionState/AutoPromo_Main
```

Expected: `{"state":"open"}` = Connected!

---

## 🌐 Use in AutoPromo Dashboard

1. Start backend:
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open: `http://localhost:3000/dashboard/whatsapp`

4. Your WhatsApp should show as **Connected**!

---

## 🔑 Credentials

**Evolution API URL**: `http://localhost:8081`  
**API Key**: `f708f2fc-471f-4511-83c3-701229e766d5`

---

## ❓ Troubleshooting

### Evolution API not starting?

```bash
# Check logs
docker compose logs evolution-api

# Restart
docker compose restart evolution-api
```

### QR Code script fails?

```bash
# Make sure Evolution API is running
docker compose ps evolution-api

# Should show "Up" status
```

### Can't connect to localhost:8081?

```bash
# Test connection
curl http://localhost:8081/

# Should return: {"status":"ok"} or similar
```

---

## 📚 Full Documentation

For complete guide, see: [docs/evolution_setup.md](docs/evolution_setup.md)

---

**That's it! You're ready to use WhatsApp in AutoPromo!** 🎉

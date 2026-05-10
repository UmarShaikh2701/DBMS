# ⚡ ShopForge — Online Shopping Platform Management System

> A full-stack shopping platform management dashboard built with **Python**, **Flask**, and **SQLite** — demonstrating advanced SQL concepts through a clean, modern dark UI.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3+-000000?style=flat&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## ✨ Features

- 📊 **Live Dashboard** — KPIs, revenue charts, order status, customer tiers
- 📦 **Product Management** — Add, view, search, sort with performance metrics
- 🛍 **Order Management** — Create orders, update statuses, drill into details
- 👥 **Customer CRM** — Ranked by lifetime value, tier segmentation
- 📈 **Analytics** — Running totals, weekday patterns, category rankings
- 🔍 **SQL Explorer** — Run live SELECT queries against the database
- 📋 **Audit Log** — Trigger-generated event history

---

## 🗄️ SQL Concepts Demonstrated

| Concept | Where Used |
|---|---|
| `CREATE TABLE` + constraints (`CHECK`, `UNIQUE`, `NOT NULL`) | Schema design |
| Foreign Keys + `ON DELETE CASCADE` | orders → customers, items → products |
| `CREATE INDEX` (5 indexes) | Query performance optimization |
| `CREATE VIEW` | `vw_order_summary`, `vw_product_performance` |
| `CREATE TRIGGER` | Auto-update ratings; log status changes |
| `TRANSACTION` + `ROLLBACK` | Atomic order creation with stock check |
| `INNER JOIN` / `LEFT JOIN` | Order summaries, product performance |
| `GROUP BY` + aggregates (`SUM`, `AVG`, `COUNT`) | Revenue, order counts |
| Subqueries | KPI calculations, low-stock detection |
| `WITH … AS` (CTEs) | Customer stats, leaderboards |
| `RANK()`, `DENSE_RANK()`, `NTILE()` | Window functions |
| `SUM() OVER (ORDER BY …)` | Running revenue totals |
| `PARTITION BY` | Product rank per category |
| `strftime()` | Monthly/weekday groupings |
| `PRAGMA journal_mode = WAL` | Write-Ahead Logging for concurrency |

---

## 🚀 Quick Start (3 steps)

### Prerequisites
- Python **3.8 or higher** — [Download here](https://www.python.org/downloads/)
- That's it. SQLite is built into Python.

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/shopforge.git
cd shopforge
```

---

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Tip:** Use a virtual environment to keep things clean (optional but recommended):
> ```bash
> # macOS / Linux
> python3 -m venv venv && source venv/bin/activate
>
> # Windows
> python -m venv venv && venv\Scripts\activate
>
> # Then install:
> pip install -r requirements.txt
> ```

---

### Step 3 — Run the app

```bash
python app.py
```

> On macOS/Linux you may need `python3 app.py`

**Open your browser and go to:**

```
http://localhost:5000
```

🎉 The SQLite database is **automatically created and seeded** with demo data on first run — no setup required.

---

## 📁 Project Structure

```
shopforge/
├── app.py                  # Flask app + all SQL logic
├── requirements.txt        # Dependencies (just Flask)
├── README.md               # This file
├── HOST_SOP.txt            # Detailed hosting SOP for all platforms
└── templates/
    └── index.html          # Full frontend (HTML + CSS + JS, no build step)
```

> `shopforge.db` is created automatically on first run and is git-ignored.

---

## 🖥️ Platform-Specific Notes

<details>
<summary><strong>Windows</strong></summary>

- Use `python` instead of `python3` if the latter isn't recognised
- Or use `py app.py` (Python Launcher)
- Run Command Prompt or PowerShell as Administrator if you hit permission errors

</details>

<details>
<summary><strong>macOS</strong></summary>

- Use `python3 app.py`
- If Python 3 isn't installed: `brew install python3` ([Homebrew](https://brew.sh))

</details>

<details>
<summary><strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
sudo apt update && sudo apt install python3 python3-pip
python3 app.py
```

</details>

---

## 🔧 Configuration

| Setting | Default | How to Change |
|---|---|---|
| Port | `5000` | Edit last line of `app.py`: `port=8080` |
| Host | `127.0.0.1` (local only) | Change to `host='0.0.0.0'` for LAN access |
| Database path | `shopforge.db` | Edit `DB_PATH` variable in `app.py` |
| Debug mode | `True` | Set `debug=False` for production |

---

## 🔄 Resetting the Database

To wipe and reseed with fresh demo data:

```bash
# Stop the app first (Ctrl+C), then:

# macOS / Linux
rm shopforge.db && python3 app.py

# Windows
del shopforge.db && python app.py
```

---

## 🌐 Access from Another Device (Same Network)

1. Edit the last line of `app.py`:
   ```python
   # Change this:
   app.run(debug=True, port=5000)
   # To this:
   app.run(debug=True, port=5000, host='0.0.0.0')
   ```

2. Find your local IP (`ipconfig` on Windows, `ifconfig` on macOS/Linux)

3. Visit `http://192.168.X.X:5000` from any device on the same Wi-Fi

> ⚠️ For local/development use only. Do not expose to the public internet without adding authentication and HTTPS.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Use `python3` or `py` |
| `No module named flask` | Run `pip install flask` |
| `Address already in use` | Change port in `app.py` to `8080` |
| Page loads but no data | Check terminal for Python errors |
| Database errors on startup | Delete `shopforge.db` and re-run |

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<p align="center">Built with Python · Flask · SQLite · No frameworks, no ORMs, just SQL.</p>

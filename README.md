# Web-project_work-hours
# work_hour
#  README.md

## 1. Project Name

**WorkHourTracker System (Django + Telegram Bot Integration)**

---

## 2. Project Description

WorkHourTracker System is a fully functional time tracking platform built on Django with an integrated Telegram bot.

The system provides identical core functionality in both interfaces, while the Django web application offers extended features and a more detailed management system.

Key features:

*  Start of workday tracking
*  End of workday tracking
*  Work time statistics and analytics
*  User roles (User / Admin)
* Full history of sessions stored in database
* Web interface (main system)
*  Telegram bot (lightweight access layer)

The Django site is the **primary system**, while the bot mirrors core functionality for quick access.

---

## 3. Technologies Used

* Python 3.x
* Django
* Django ORM
* aiogram (Telegram Bot API)
* SQLite / PostgreSQL (depending on configuration)
* HTML, CSS (Django Templates)
* JavaScript (basic UI interactions)
* asgiref (async integration layer)
* Git & GitHub

---

## 4. Installation Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/timetracker-system.git
cd timetracker-system
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / Mac:**

```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure environment variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
DEBUG=True
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_database_url_if_needed
```

---

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create admin user

```bash
python manage.py createsuperuser
```

---

## 5. How to Run the Project

### Start Django server (main system)

```bash
python manage.py runserver
```

Web application will be available at:

```
http://127.0.0.1:8000/
```

---

### Start Telegram Bot

```bash
python bot.py
```

The bot works in parallel with the Django backend and uses the same database.

---

## 6. Bot Usage Examples

### Available commands:

* `/start` — initialize user session
*  Start Day — records start time
*  End Day — records end time
*  Statistics — shows working time summary

### Example workflow:

1. User presses **Start Day**
2. System records timestamp in database
3. User presses **End Day**
4. System calculates total worked hours
5. Statistics are updated automatically
6. User can view full history in bot or website

---

## 7. Website Features (Extended Version)

Unlike the bot, the Django web platform includes:

###  User Panel

* Detailed daily and monthly statistics
* Work session history table
* Profile management (username/email updates)
* Password change functionality

###  Admin Panel

* Full user management
* Monitoring all sessions
* Editing or correcting time entries
* System-wide analytics



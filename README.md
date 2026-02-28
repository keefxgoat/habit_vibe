Habit Tracker

A habit tracker with a 40-day system, authentication, dark/light theme, and statistics

Tech Stack
- FastAPI
- SQLAlchemy
- SQLite
- JWT authentication
- HTML/CSS/JS

Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # for Linux/Mac
   venv\Scripts\activate     # for Windows

Install dependencies:

bash
pip install -r requirements.txt
Run the server:

bash
uvicorn main:app --reload
open http://127.0.0.1:8000/static/landing.html

✨ Features
Registration and login

Create habits

Track progress (streak)

40-day habit formation rule

Sorting and filtering

Dark/light theme

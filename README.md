# 📚 Liane's Library — Book-Lending Manager

A full **CRUD application** for managing a personal book-lending library — built with Python, MySQL and Streamlit. Track books, friends, and who borrowed what, with a clean interactive dashboard.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

---

## About

Built during the WBS Coding School Data Analytics bootcamp as a Python-to-SQL project. The goal: connect a Python application to a relational database and expose full Create / Read / Update / Delete operations through an interactive UI — not just query data, but manage it.

## Features

- **📖 Books** — add, view, update and remove books with availability tracking
- **👥 Friends** — manage the people who borrow books
- **📤 Lend / 📥 Return** — record loans and returns with transactional integrity
- **📋 All Loans** — see active and historical loans at a glance
- **🏠 Dashboard** — overview of library status

## Tech & Structure

| Path | Description |
|------|-------------|
| `src/app.py` | Streamlit front end — multi-page navigation, dashboard, all CRUD flows |
| `src/crud.py` | Database layer — CRUD functions over a MySQL schema |
| `notebooks/` | Development notebooks (Python-to-SQL workflow, Streamlit prototype) |

**Stack:** Python · MySQL · SQLAlchemy / mysql-connector · Streamlit · pandas

## Running it locally

1. Create the MySQL schema (`lianes_library`) and load the book/friend/loan tables.
2. Copy `.env.example` to `.env` and set your database credentials.
3. Install dependencies:
   ```bash
   pip install streamlit pandas sqlalchemy pymysql mysql-connector-python
   ```
4. Launch the app:
   ```bash
   streamlit run src/app.py
   ```

> **Note:** Database credentials are read from environment variables — no secrets are committed to this repository.

---

**Aylin Yildiz** · [LinkedIn](https://linkedin.com/in/aylinyildiz26) · [GitHub](https://github.com/AylinYildiz26)

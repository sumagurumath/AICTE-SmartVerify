import hashlib
import json
import sqlite3
from datetime import date, datetime

import pandas as pd
import streamlit as st

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="AICTE SmartVerify",
    page_icon="🔎",
    layout="wide",
)

DB_NAME = "smartverify.db"

# ---------------- SAMPLE DEMO REGISTRY ----------------
# Synthetic demonstration data only; not connected to official AICTE records.
INSTITUTION_REGISTRY = {
    "AICTE-DEMO-001": {
        "name": "Demo Institute A",
        "approved_programme": "Computer Science Engineering",
    },
    "AICTE-DEMO-002": {
        "name": "Demo Institute B",
        "approved_programme": "Artificial Intelligence and Machine Learning",
    },
    "AICTE-DEMO-003": {
        "name": "Demo Institute C",
        "approved_programme": "Information Science Engineering",
    },
}


# ---------------- DATABASE SETUP ----------------
def init_database():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution TEXT,
                institution_id TEXT,
                application_type TEXT,
                certificate_number TEXT,
                expiry_date TEXT,
                uploaded_documents TEXT,
                status TEXT,
                findings TEXT,
                submitted_at TEXT,
                review_decision TEXT DEFAULT 'Pending Review',
                reviewer_comment TEXT DEFAULT ''
            )
            """
        )

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(applications)").fetchall()
        }

        if "review_decision" not in columns:
            conn.execute(
                """
                ALTER TABLE applications
                ADD COLUMN review_decision TEXT DEFAULT 'Pending Review'
                """
            )

        if "reviewer_comment" not in columns:
            conn.execute(
                """
                ALTER TABLE applications
                ADD COLUMN reviewer_comment TEXT DEFAULT ''
                """
            )


def save_application(
    institution,
    institution_id,
    application_type,
    certificate_number,
    expiry_date,
    document_names,
    status,
    findings,
):
    with sqlite3.connect(DB_NAME) as conn:
    conn.execute(
        """
        INSERT INTO applications (
            institution, institution_id, application_type,
            certificate_number, expiry_date, uploaded_documents,
            status, findings, submitted_at, review_decision,
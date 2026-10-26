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
                reviewer_comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                institution.strip(),
                institution_id.strip(),
                application_type,
                certificate_number.strip(),
                expiry_date.isoformat(),
                json.dumps(document_names),
                status,
                "; ".join(findings) if findings else "No issues found",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Pending Review",
                "",
            ),
        )


def validate_application(institution, institution_id, certificate_number, expiry_date, uploaded_files):
    findings = []

    if not institution.strip():
        findings.append("Institution name is missing.")
    if not institution_id.strip():
        findings.append("Institution ID is missing.")
    if not certificate_number.strip():
        findings.append("Certificate number is missing.")
    if not uploaded_files:
        findings.append("No supporting documents uploaded.")
    if expiry_date < date.today():
        findings.append("Certificate expiry date has passed.")

    record = INSTITUTION_REGISTRY.get(institution_id.strip())
    if institution_id.strip() and record is None:
        findings.append("Institution ID was not found in the synthetic demo registry.")
    elif record and institution.strip().casefold() != record["name"].casefold():
        findings.append(
            f"Institution name mismatch. The demo registry lists '{record['name']}'."
        )

    if uploaded_files:
        hashes = [
            hashlib.sha256(uploaded_file.getvalue()).hexdigest()
            for uploaded_file in uploaded_files
        ]
        if len(hashes) != len(set(hashes)):
            findings.append("Duplicate document detected among uploaded files.")

    status = "Ready for official review" if not findings else "Needs review"
    return status, findings, record


def get_applications():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(
            """
            SELECT id, institution, institution_id, application_type,
                   certificate_number, expiry_date, uploaded_documents,
                   status, findings, submitted_at, review_decision,
                   reviewer_comment
            FROM applications
            ORDER BY id DESC
            """,
            conn,
        )


init_database()

# ---------------- THEME ----------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5EFE5;
        color: #292C2A;
    }
    h1, h2, h3, h4, p, label,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stMarkdownContainer"] p {
        color: #292C2A !important;
    }
    [data-testid="stWidgetLabel"] p {
        font-size: 16px !important;
        font-weight: 700 !important;
    }
    input, textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background-color: #FFFDF8 !important;
        color: #292C2A !important;
        -webkit-text-fill-color: #292C2A !important;
        border: 1px solid #8C8172 !important;
    }
    [data-baseweb="select"] > div {
        background-color: #FFFDF8 !important;
        color: #292C2A !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #FFFDF8 !important;
        color: #292C2A !important;
        border: 1px solid #B99A64 !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] * {
        color: #292C2A !important;
    }
    .stApp button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFileUploader"] button {
        background-color: #292C2A !important;
        color: #FFFFFF !important;
        border: 2px solid #B99A64 !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    .stApp button p, .stApp button span {
        color: #FFFFFF !important;
    }
    .stApp button:hover {
        background-color: #526354 !important;
        color: #FFFFFF !important;
    }
    input::placeholder, textarea::placeholder {
        color: #6B6B6B !important;
        -webkit-text-fill-color: #6B6B6B !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE ----------------
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "logged_in_role" not in st.session_state:
    st.session_state.logged_in_role = None
if "logged_in_id" not in st.session_state:
    st.session_state.logged_in_id = ""

# ---------------- LOGIN SCREEN ----------------
if not st.session_state.logged_in:
    st.title("✦ AICTE SmartVerify")
    st.subheader("Application Validation & Compliance Assistant")
    st.write("A smarter workspace for institutional applications and regulatory review.")
    st.divider()
    st.markdown("### Welcome")
    st.write("Choose your workspace to continue.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏛️ Institution")
        st.write("Submit applications, track progress and view reviewer feedback.")
        if st.button("Institution Login", use_container_width=True):
            st.session_state.user_role = "Institution"
    with col2:
        st.markdown("#### 🧾 Reviewer")
        st.write("Review applications, record decisions and provide comments.")
        if st.button("Reviewer Login", use_container_width=True):
            st.session_state.user_role = "Reviewer"

    if st.session_state.user_role == "Institution":
        st.divider()
        st.subheader("Institution Login")
        with st.form("institution_login_form"):
            login_id = st.text_input(
                "Institution ID",
                placeholder="Example: AICTE-DEMO-001",
            )
            login_password = st.text_input("Demo Password", type="password")
            login_clicked = st.form_submit_button("Continue as Institution")

        if login_clicked:
            if login_id.strip() and login_password:
                st.session_state.logged_in = True
                st.session_state.logged_in_role = "Institution"
                st.session_state.logged_in_id = login_id.strip()
                st.rerun()
            else:
                st.error("Enter both Institution ID and demo password.")

    elif st.session_state.user_role == "Reviewer":
        st.divider()
        st.subheader("Reviewer Login")
        with st.form("reviewer_login_form"):
            reviewer_email = st.text_input(
                "Reviewer Email",
                placeholder="reviewer@demo.com",
            )
            reviewer_password = st.text_input("Demo Password", type="password")
            reviewer_login_clicked = st.form_submit_button("Continue as Reviewer")

        if reviewer_login_clicked:
            if reviewer_email.strip() and reviewer_password:
                st.session_state.logged_in = True
                st.session_state.logged_in_role = "Reviewer"
                st.rerun()
            else:
                st.error("Enter both reviewer email and demo password.")

    st.caption("Hackathon prototype • Uses synthetic demo data")
    st.stop()

# ---------------- LOGGED-IN WORKSPACES ----------------
st.title("✦ AICTE SmartVerify")
st.caption("Hackathon prototype • Uses synthetic demo data")

if st.session_state.logged_in_role == "Institution":
    st.markdown("## 🏛️ Institution Workspace")
    st.markdown("### 📄 Your Application Portal")
    st.write("Submit your institution's application below.")

    with st.form("institution_application_form"):
        institution_name = st.text_input("Institution Name")
        institution_id = st.text_input(
            "Institution ID",
            value=st.session_state.get("logged_in_id", ""),
        )
        application_type = st.selectbox(
            "Application Category",
            ["New Approval", "Extension of Approval", "Course Addition", "Other"],
        )
        certificate_number = st.text_input("Certificate Number")
        expiry_date = st.date_input("Certificate Expiry Date", value=date.today())
        uploaded_files = st.file_uploader(
            "Upload Supporting Documents",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Demo: file names are saved; uploaded file contents are not stored.",
        )
        submitted = st.form_submit_button("Submit Application", use_container_width=True)

    if submitted:
        if not institution_name.strip() or not institution_id.strip():
            st.error("Please enter the institution name and ID.")
        elif not certificate_number.strip():
            st.error("Please enter the certificate number.")
        else:
            status, findings, record = validate_application(
                institution_name,
                institution_id,
                certificate_number,
                expiry_date,
                uploaded_files,
            )
            document_names = [uploaded_file.name for uploaded_file in (uploaded_files or [])]
            save_application(
                institution_name,
                institution_id,
                application_type,
                certificate_number,
                expiry_date,
                document_names,
                status,
                findings,
            )
            st.success("Application submitted and saved successfully.")
            st.write(f"**Automated check status:** {status}")
            if findings:
                st.warning("Please review these findings:")
                for finding in findings:
                    st.write(f"- {finding}")
            elif record:
                st.info(f"Demo registry match: {record['name']} — {record['approved_programme']}")
            st.caption(
                "These are preliminary demo checks only, not official AICTE verification."
            )

    st.divider()
    st.subheader("📋 Your Application History")
    all_apps = get_applications()
    if not all_apps.empty:
        own_apps = all_apps[
            all_apps["institution_id"].astype(str)
            == str(st.session_state.get("logged_in_id", ""))
        ]
    else:
        own_apps = all_apps

    if own_apps.empty:
        st.info("No applications found for this Institution ID yet.")
    else:
        institution_history = own_apps[
            [
                "id", "institution", "institution_id", "application_type",
                "status", "findings", "review_decision", "reviewer_comment",
                "submitted_at",
            ]
        ].rename(
            columns={
                "id": "Application ID",
                "institution": "Institution",
                "institution_id": "Institution ID",
                "application_type": "Application Category",
                "status": "Automated Status",
                "findings": "Findings",
                "review_decision": "Reviewer Decision",
                "reviewer_comment": "Reviewer Comment",
                "submitted_at": "Submitted At",
            }
        )
        st.dataframe(institution_history, use_container_width=True, hide_index=True)

    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.logged_in_role = None
        st.session_state.user_role = None
        st.session_state.logged_in_id = ""
        st.rerun()

    st.stop()

# ---------------- REVIEWER WORKSPACE ----------------
st.sidebar.title("🔎 SmartVerify")
st.sidebar.caption("Reviewer workspace")
st.sidebar.success("Reviewer signed in")
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.logged_in_role = None
    st.session_state.user_role = None
    st.session_state.logged_in_id = ""
    st.rerun()

st.header("Application Dashboard")
applications = get_applications()
total_applications = len(applications)
ready_count = int((applications["status"] == "Ready for official review").sum()) if total_applications else 0
needs_review_count = int((applications["status"] == "Needs review").sum()) if total_applications else 0
pending_review_count = int((applications["review_decision"] == "Pending Review").sum()) if total_applications else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Applications", total_applications)
m2.metric("Checks Passed", ready_count)
m3.metric("Needs Review", needs_review_count)
m4.metric("Pending Reviewer Decision", pending_review_count)

st.caption("Data comes from this prototype's local SQLite database, not live AICTE records.")
st.divider()

st.subheader("Sample Institutional Registry")
with st.expander("View synthetic demo registry"):
    for demo_id, record in INSTITUTION_REGISTRY.items():
        st.write(f"**Institution ID:** {demo_id}")
        st.write(f"**Name:** {record['name']}")
        st.write(f"**Programme:** {record['approved_programme']}")
        st.divider()

st.header("Reviewer Interface")
applications = get_applications()
if applications.empty:
    st.info("No applications available for review yet.")
else:
    selected_id = st.selectbox("Select Application ID", applications["id"].tolist())
    selected_app = applications[applications["id"] == selected_id].iloc[0]
    st.write(f"**Institution:** {selected_app['institution']}")
    st.write(f"**Institution ID:** {selected_app['institution_id']}")
    st.write(f"**Application Category:** {selected_app['application_type']}")
    st.write(f"**Automated Check Status:** {selected_app['status']}")
    st.write(f"**Findings:** {selected_app['findings']}")

    decisions = [
        "Pending Review",
        "Need Correction",
        "Ready for Official Review",
        "Escalate for Official Review",
    ]
    current_decision = selected_app["review_decision"]
    decision_index = decisions.index(current_decision) if current_decision in decisions else 0

    with st.form("reviewer_decision_form"):
        review_decision = st.selectbox(
            "Reviewer Decision",
            decisions,
            index=decision_index,
        )
        reviewer_comment = st.text_area(
            "Reviewer Comment",
            value=selected_app["reviewer_comment"] or "",
            placeholder="Enter corrections required or review notes...",
        )
        save_decision = st.form_submit_button("Save Reviewer Decision")

    if save_decision:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                """
                UPDATE applications
                SET review_decision = ?, reviewer_comment = ?
                WHERE id = ?
                """,
                (review_decision, reviewer_comment, int(selected_id)),
            )
        st.success("Reviewer decision saved successfully.")
        st.rerun()

st.divider()
st.header("📋 Application History")
history = get_applications()
if history.empty:
    st.info("No applications saved yet.")
else:
    history = history.rename(
        columns={
            "id": "Application ID",
            "institution": "Institution",
            "institution_id": "Institution ID",
            "application_type": "Application Category",
            "certificate_number": "Certificate Number",
            "expiry_date": "Expiry Date",
            "uploaded_documents": "Document Names (files are not stored)",
            "status": "Automated Status",
            "findings": "Findings",
            "submitted_at": "Submitted At",
            "review_decision": "Reviewer Decision",
            "reviewer_comment": "Reviewer Comment",
        }
    )
    st.dataframe(history, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "AICTE SmartVerify | Smart India Hackathon Prototype | "
    "Synthetic data for demonstration only. Not an official AICTE service."
)

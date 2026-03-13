# ==========================================
# IMPORTS
# ==========================================
import pytesseract
from PIL import Image
import pdfplumber
import pandas as pd
import re
from docx import Document
from openai import OpenAI

# ==========================================
# CONFIG
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OPENROUTER_API_KEY = "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"

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

MODEL_NAME = "openai/gpt-3.5-turbo"

# ==========================================
# CLEAN NUMERIC DATA
# ==========================================
def clean_numeric_columns(df):

    for col in df.columns:
        if col != "name":
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# ==========================================
# FILE READERS
# ==========================================
def read_from_csv(path):

    df = pd.read_csv(path)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    df = df.rename(columns={
        "attendance": "attendance_percent",
        "attendance%": "attendance_percent",
        "grade": "average_score",
        "avg_grade": "average_score",
        "study_hours": "study_hours_per_week",
        "backlogs": "backlog"
    })

    subject_cols = ["subject1", "subject2", "subject3", "subject4"]

    for col in subject_cols:
        if col not in df.columns:
            df[col] = 0

    df = clean_numeric_columns(df)

    df["average_score"] = df[subject_cols].mean(axis=1)

    # Add unique student id
    df.insert(0, "student_id", range(1, len(df) + 1))

    return df


def read_from_excel(path):
    return read_from_csv(path)


def read_from_word(path):
    doc = Document(path)

    rows = []
    for row in doc.tables[0].rows[1:]:
        rows.append([c.text.strip() for c in row.cells])

    df = pd.DataFrame(rows, columns=[
        "name", "subject1", "subject2", "subject3", "subject4",
        "attendance_percent", "study_hours_per_week", "backlog"
    ])

    df = clean_numeric_columns(df)

    df["average_score"] = df[
        ["subject1", "subject2", "subject3", "subject4"]
    ].mean(axis=1)

    df.insert(0, "student_id", range(1, len(df) + 1))

    return df


def read_from_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            if p.extract_text():
                text += p.extract_text() + "\n"

    return text_to_dataframe(text)


def read_from_image(path):

    text = pytesseract.image_to_string(Image.open(path))

    return text_to_dataframe(text)


# ==========================================
# TEXT → DATAFRAME
# ==========================================
def text_to_dataframe(text):

    rows = []

    for line in text.split("\n"):

        parts = re.sub(r"[^\w\s]", " ", line).split()

        nums = [i for i, x in enumerate(parts) if x.isdigit()]

        if nums and len(parts) - nums[0] >= 7:
            rows.append(
                [" ".join(parts[:nums[0]])] + parts[nums[0]:nums[0] + 7]
            )

    df = pd.DataFrame(rows, columns=[
        "name", "subject1", "subject2", "subject3", "subject4",
        "attendance_percent", "study_hours_per_week", "backlog"
    ])

    df = clean_numeric_columns(df)

    df["average_score"] = df[
        ["subject1", "subject2", "subject3", "subject4"]
    ].mean(axis=1)

    df.insert(0, "student_id", range(1, len(df) + 1))

    return df


# ==========================================
# RISK LOGIC
# ==========================================
def analyze_risk(df):

    df["Risk"] = (
        (df["attendance_percent"] < 60) |
        (df["average_score"] < 40) |
        (df["study_hours_per_week"] < 10) |
        (df["backlog"] >= 3)
    )

    return df


def calculate_risk_score_and_level(df):

    df["Risk_Score"] = 0

    df.loc[df["attendance_percent"] < 60, "Risk_Score"] += 30
    df.loc[(df["attendance_percent"] >= 60) &
           (df["attendance_percent"] < 75), "Risk_Score"] += 15

    df.loc[df["average_score"] < 40, "Risk_Score"] += 30
    df.loc[(df["average_score"] >= 40) &
           (df["average_score"] < 60), "Risk_Score"] += 20
    df.loc[(df["average_score"] >= 60) &
           (df["average_score"] < 75), "Risk_Score"] += 10

    df.loc[df["study_hours_per_week"] < 10, "Risk_Score"] += 20
    df.loc[(df["study_hours_per_week"] >= 10) &
           (df["study_hours_per_week"] < 15), "Risk_Score"] += 10

    df.loc[df["backlog"] >= 3, "Risk_Score"] += 20
    df.loc[(df["backlog"] >= 1) &
           (df["backlog"] < 3), "Risk_Score"] += 10

    df["Risk_Level"] = pd.cut(
        df["Risk_Score"],
        bins=[-1, 39, 69, 100],
        labels=["Low Risk", "Medium Risk", "High Risk"]
    )

    return df

# ==========================================
# AI ADVICE
# ==========================================
def get_individual_ai_advice(student):

    prompt = f"""
You are an academic counselor.

Give:
• short diagnosis
• 2 improvement actions
• motivational line

Student:
Name: {student['name']}
Attendance: {student['attendance_percent']}%
Score: {student['average_score']}
Study Hours: {student['study_hours_per_week']}
Backlogs: {student['backlog']}
Risk: {student['Risk_Level']}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=45
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return "AI temporarily unavailable."


# ==========================================
# CHAT AI
# ==========================================
def counselor_chat(question, df):

    small_df = df[['name', 'Risk_Level']].head(50)

    prompt = f"""
You are a student counselor.

Student Risk Data:
{small_df.to_dict(orient='records')}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=45
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Chat Error:", e)
        return "AI unavailable."

# ==========================================
# STUDY PLAN
# ==========================================
def generate_study_plan(student):

    plan = []

    if student["attendance_percent"] < 75:
        plan.append(
            f"Improve attendance to 75%+ (now {student['attendance_percent']}%)"
        )

    weak = [
        f"Sub{i+1}({student[f'subject{i+1}']}%)"
        for i in range(4)
        if student[f"subject{i+1}"] < 60
    ]

    if weak:
        plan.append("Focus on weak subjects: " + ", ".join(weak))

    if student["study_hours_per_week"] < 15:
        plan.append("Increase study hours to 15+ per week")

    if student["backlog"] > 0:
        plan.append(f"Clear {student['backlog']} backlog subject(s)")

    if not plan:
        plan.append("Maintain current performance")

    return " • ".join(plan)


# ==========================================
# SUMMARY FUNCTIONS
# ==========================================
def get_risk_distribution(df):
    return df["Risk_Level"].value_counts().to_dict()


def get_average_metrics(df):

    return {
        "avg_score": df["average_score"].mean(),
        "avg_attendance": df["attendance_percent"].mean(),
        "avg_study_hours": df["study_hours_per_week"].mean(),
        "total_backlogs": df["backlog"].sum(),
        "avg_risk_score": df["Risk_Score"].mean()
    }


def get_top_performers(df):
    return df[df["average_score"] >= 90].sort_values(
        "average_score",
        ascending=False
    )


def get_students_by_risk(df, risk_level):
    return df[df["Risk_Level"] == risk_level]


def search_students(df, query):
    return df[df["name"].str.contains(query, case=False, na=False)]

# ==========================================
# DATABASE SAVE
# ==========================================

import psycopg2

def save_students_to_db(df):

    conn = psycopg2.connect(
        database="student_risk_db",
        user="postgres",
        password="18112005itachi$MJ",
        host="localhost",
        port="5432"
    )

    cursor = conn.cursor()

    for _, row in df.iterrows():

        cursor.execute("""
        INSERT INTO students(
            student_id,
            name,
            subject1,
            subject2,
            subject3,
            subject4,
            attendance_percent,
            study_hours_per_week,
            backlog,
            average_score,
            risk_score,
            risk_level
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (student_id) DO NOTHING
        """, (
            int(row["student_id"]),
            row["name"],
            float(row["subject1"]),
            float(row["subject2"]),
            float(row["subject3"]),
            float(row["subject4"]),
            float(row["attendance_percent"]),
            float(row["study_hours_per_week"]),
            int(row["backlog"]),
            float(row["average_score"]),
            int(row["Risk_Score"]),
            str(row["Risk_Level"])
        ))

    conn.commit()
    cursor.close()
    conn.close()
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

# 🔑 OpenRouter API Key
OPENROUTER_API_KEY = "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"

# OpenRouter Client
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

MODEL_NAME = "openai/gpt-3.5-turbo"

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

    subject_cols = ['subject1','subject2','subject3','subject4']

    for col in subject_cols:
        if col not in df.columns:
            df[col] = 0

    df["average_score"] = df[subject_cols].mean(axis=1)

    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce").fillna(0)
    return df

def read_from_excel(path):
    return read_from_csv(path)

def read_from_word(path):
    doc = Document(path)
    rows=[]
    for row in doc.tables[0].rows[1:]:
        rows.append([c.text.strip() for c in row.cells])

    df = pd.DataFrame(rows, columns=[
        "name","subject1","subject2","subject3","subject4",
        "attendance_percent","study_hours_per_week","backlog"
    ])

    df = df.apply(pd.to_numeric, errors="ignore")
    df["average_score"] = df[['subject1','subject2','subject3','subject4']].mean(axis=1)
    return df

def read_from_pdf(path):
    text=""
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            if p.extract_text():
                text += p.extract_text()+"\n"
    return text_to_dataframe(text)

def read_from_image(path):
    text = pytesseract.image_to_string(Image.open(path))
    return text_to_dataframe(text)

# ==========================================
# TEXT → DATAFRAME
# ==========================================

def text_to_dataframe(text):
    rows=[]
    for line in text.split("\n"):
        parts=re.sub(r"[^\w\s]"," ",line).split()
        nums=[i for i,x in enumerate(parts) if x.isdigit()]
        if nums and len(parts)-nums[0]>=7:
            rows.append([" ".join(parts[:nums[0]])]+parts[nums[0]:nums[0]+7])

    df=pd.DataFrame(rows,columns=[
        "name","subject1","subject2","subject3","subject4",
        "attendance_percent","study_hours_per_week","backlog"
    ])

    df=df.apply(pd.to_numeric,errors="ignore")
    df["average_score"]=df[['subject1','subject2','subject3','subject4']].mean(axis=1)
    return df

# ==========================================
# RISK LOGIC (IMPROVED)
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
    scores=[]
    levels=[]

    for _,r in df.iterrows():
        score=0

        if r["attendance_percent"] < 60: score+=30
        elif r["attendance_percent"] < 75: score+=15

        if r["average_score"] < 40: score+=30
        elif r["average_score"] < 60: score+=20
        elif r["average_score"] < 75: score+=10

        if r["study_hours_per_week"] < 10: score+=20
        elif r["study_hours_per_week"] < 15: score+=10

        if r["backlog"] >= 3: score+=20
        elif r["backlog"] >= 1: score+=10

        level = (
            "High Risk" if score >= 70 else
            "Medium Risk" if score >= 40 else
            "Low Risk"
        )

        scores.append(score)
        levels.append(level)

    df["Risk_Score"]=scores
    df["Risk_Level"]=levels
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
            max_tokens=100
        )
        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return "AI temporarily unavailable."

# ==========================================
# CHAT AI
# ==========================================

def counselor_chat(question, df):
    prompt = f"""
Students:
{df[['name','Risk_Level']].to_dict(orient='records')}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content

    except Exception as e:
        print("Chat Error:", e)
        return "AI unavailable."

# ==========================================
# STUDY PLAN
# ==========================================

def generate_study_plan(student):
    plan=[]

    if student["attendance_percent"] < 75:
        plan.append(f"Improve attendance to 75%+ (now {student['attendance_percent']}%)")

    weak = [f"Sub{i+1}({student[f'subject{i+1}']}%)"
            for i in range(4) if student[f'subject{i+1}'] < 60]
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
    return df['Risk_Level'].value_counts().to_dict()

def get_average_metrics(df):
    return {
        'avg_score': df['average_score'].mean(),
        'avg_attendance': df['attendance_percent'].mean(),
        'avg_study_hours': df['study_hours_per_week'].mean(),
        'total_backlogs': df['backlog'].sum(),
        'avg_risk_score': df['Risk_Score'].mean()
    }

def get_top_performers(df):
    return df.sort_values("average_score",ascending=False).head(5)

def get_students_by_risk(df,risk_level):
    return df[df['Risk_Level']==risk_level]

def search_students(df,query):
    return df[df['name'].str.contains(query,case=False,na=False)]

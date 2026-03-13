import streamlit as st
import tempfile
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.core import (
    read_from_csv,
    read_from_excel,
    read_from_word,
    read_from_pdf,
    read_from_image,
    analyze_risk,
    calculate_risk_score_and_level,
    get_individual_ai_advice,
    counselor_chat,
    generate_study_plan,
    get_top_performers,
    get_risk_distribution,
    get_average_metrics
)

st.set_page_config(
    page_title="AI Student Risk Predictor",
    page_icon="SR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# DARK THEME CSS
# ==========================================

def load_dark_theme():
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Global Dark Theme Styles */
        .stApp {
            font-family: 'Inter', sans-serif;
            background: #0E1117;
            color: #FAFAFA;
        }
        
        /* Main container styling */
        .main-header {
            background: linear-gradient(135deg, #1E1E2E 0%, #2D2D44 100%);
            padding: 2rem;
            border-radius: 20px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            text-align: center;
            border: 1px solid #333;
        }
        
        /* Metric cards */
        .metric-card {
            background: #1E1E2E;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            text-align: center;
            transition: transform 0.3s ease;
            border: 1px solid #333;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: #667eea;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
        }
        .metric-label {
            font-size: 1rem;
            color: #AAA;
            margin-top: 0.5rem;
        }
        
        /* Upload area styling */
        .upload-area {
            background: #1E1E2E;
            border: 2px dashed #667eea;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background: #1E1E2E;
            padding: 0.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            border: 1px solid #333;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            color: #AAA;
        }
        .stTabs [aria-selected="true"] {
            background: #2D2D44;
            color: white;
        }
        
        /* Student cards */
        .student-card {
            background: #1E1E2E;
            border-radius: 12px;
            padding: 1.2rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            border-left: 4px solid;
            transition: all 0.3s ease;
            border: 1px solid #333;
        }
        .student-card:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
            border-color: #667eea;
        }
        .student-card h4 {
            color: white;
        }
        .student-card p {
            color: #AAA;
        }
        .high-risk { border-left-color: #ff4d4d; }
        .medium-risk { border-left-color: #ffa64d; }
        .low-risk { border-left-color: #4CAF50; }
        
        /* Progress bar styling */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 2rem;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid #333;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        /* Info boxes */
        .info-box {
            background: #1E1E2E;
            border-radius: 10px;
            padding: 1rem;
            border-left: 4px solid #667eea;
            margin: 1rem 0;
            border: 1px solid #333;
        }
        .info-box p {
            color: #AAA;
        }
        .info-box strong {
            color: white;
        }
        
        /* Sidebar styling */
        .css-1d391kg, .css-1wrcr25 {
            background: #1E1E2E !important;
        }
        .sidebar-content {
            background: #1E1E2E;
            color: white;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            color: #AAA;
            padding: 2rem;
            background: #1E1E2E;
            border-radius: 10px;
            margin-top: 2rem;
            border: 1px solid #333;
        }
        
        /* Chat container styling */
        .chat-container {
            background: #1E1E2E;
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            border: 1px solid #333;
        }
        
        .chat-message-user {
            background: #2D2D44;
            border-radius: 15px 15px 15px 5px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #667eea;
            color: white;
        }
        
        .chat-message-bot {
            background: #1E1E2E;
            border-radius: 15px 15px 5px 15px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #333;
            color: #AAA;
        }
        
        /* Text input styling */
        .stTextInput > div > div > input {
            background: #1E1E2E;
            color: white;
            border: 1px solid #333;
            border-radius: 10px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div > select {
            background: #1E1E2E;
            color: white;
            border: 1px solid #333;
        }
        
        /* Dataframe styling */
        .dataframe {
            background: #1E1E2E;
            color: white;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: #1E1E2E;
            color: white;
            border: 1px solid #333;
        }
        .streamlit-expanderContent {
            background: #1E1E2E;
            border: 1px solid #333;
            color: #AAA;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# HEADER SECTION
# ==========================================

def display_header():
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; font-size:3rem;">🎓 AI Student Risk Predictor</h1>
        <p style="font-size:1.2rem; opacity:0.9; margin-top:0.5rem;">
            Early identification • Smart counseling • Better outcomes
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================

def create_sidebar():
    with st.sidebar:
        st.markdown("## 🎓 Student Risk AI")
        st.markdown("### Powered by OCR + AI")
        st.divider()
        
        st.markdown("### 📤 Upload File")
        st.caption("Upload CSV/Excel/Word/PDF/Image")
        
        # File uploader
        file = st.file_uploader(
            "",
            type=["csv", "xlsx", "docx", "pdf", "png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="file_uploader"
        )
        
        st.divider()
        
        # File info
        if file:
            file_size = len(file.getvalue()) / 1024  # KB
            st.markdown(f"**📄 File:** {file.name}")
            st.markdown(f"**📊 Size:** {file_size:.1f} KB")
            st.markdown(f"**🕒 Uploaded:** {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.markdown("""
            <div class="upload-area">
                <p style="font-size:2rem; margin:0;">📁</p>
                <p style="font-weight:500; color:white;">Drag and drop file here</p>
                <p style="color:#AAA; font-size:0.9rem;">Limit 200MB per file • CSV, XLSX, DOCX, PDF, PNG, JPG</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        st.caption("© 2024 Student Risk AI • All rights reserved")
        
        return file

# ==========================================
# FILE LOADER FUNCTION
# ==========================================

def load_file(file):
    """Load and parse uploaded file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
        tmp.write(file.getvalue())
        path = tmp.name

    if file.name.endswith(".csv"):
        return read_from_csv(path)
    elif file.name.endswith(".xlsx"):
        return read_from_excel(path)
    elif file.name.endswith(".docx"):
        return read_from_word(path)
    elif file.name.endswith(".pdf"):
        return read_from_pdf(path)
    else:
        return read_from_image(path)

# ==========================================
# METRICS DISPLAY
# ==========================================

def display_metrics(df):
    """Display metric cards"""
    total_students = len(df)
    top_performers = len(get_top_performers(df))
    high_risk = len(df[df["Risk_Level"] == "High Risk"])
    low_risk = len(df[df["Risk_Level"] == "Low Risk"])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_students}</div>
            <div class="metric-label">Total Students</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#4CAF50;">{top_performers}</div>
            <div class="metric-label">Top Performers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#ff4d4d;">{high_risk}</div>
            <div class="metric-label">High Risk</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#4CAF50;">{low_risk}</div>
            <div class="metric-label">Low Risk</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# EXECUTIVE SUMMARY TAB (UPDATED)
# ==========================================

def executive_summary_tab(df):
    """Display executive summary tab content with subjects and risk score"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Student Data Overview")
        
        # Create display dataframe with subjects and risk score
        display_df = df[['name', 'subject1', 'subject2', 'subject3', 'subject4', 
                        'attendance_percent', 'study_hours_per_week', 'backlog', 
                        'Risk_Score', 'Risk_Level']].copy()
        
        # Rename columns for better display
        display_df.columns = ['Name', 'Sub1', 'Sub2', 'Sub3', 'Sub4', 
                             'Attendance %', 'Study Hrs', 'Backlogs', 
                             'Risk Score', 'Risk Level']
        
        # Round numeric columns
        display_df['Sub1'] = display_df['Sub1'].round(1)
        display_df['Sub2'] = display_df['Sub2'].round(1)
        display_df['Sub3'] = display_df['Sub3'].round(1)
        display_df['Sub4'] = display_df['Sub4'].round(1)
        display_df['Attendance %'] = display_df['Attendance %'].round(1)
        display_df['Risk Score'] = display_df['Risk Score'].round(0).astype(int)
        
        # Style the dataframe
        def color_cells(val):
            if pd.isna(val):
                return ''
            try:
                if 'Risk Level' in str(val):
                    if 'High' in str(val):
                        return 'background-color: #ff4d4d33; color: #ff4d4d'
                    elif 'Medium' in str(val):
                        return 'background-color: #ffa64d33; color: #ffa64d'
                    elif 'Low' in str(val):
                        return 'background-color: #4CAF5033; color: #4CAF50'
                elif isinstance(val, (int, float)):
                    if val > 80:
                        return 'color: #4CAF50'
                    elif val < 60:
                        return 'color: #ff4d4d'
            except:
                pass
            return ''
        
        styled_df = display_df.style.applymap(color_cells)
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=400
        )
    
    with col2:
        st.markdown("### 📊 Risk Distribution")
        
        # Create pie chart with dark theme
        risk_dist = get_risk_distribution(df)
        fig = go.Figure(data=[go.Pie(
            labels=list(risk_dist.keys()),
            values=list(risk_dist.values()),
            hole=0.3,
            marker_colors=['#ff4d4d', '#ffa64d', '#4CAF50']
        )])
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=0, b=0, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        metrics = get_average_metrics(df)
        st.markdown("### 📈 Quick Stats")
        st.markdown(f"""
        <div class="info-box">
            <p><strong>📊 Avg Subject Scores:</strong></p>
            <p>Sub1: {df['subject1'].mean():.1f}% | Sub2: {df['subject2'].mean():.1f}%</p>
            <p>Sub3: {df['subject3'].mean():.1f}% | Sub4: {df['subject4'].mean():.1f}%</p>
            <p><strong>📝 Avg Attendance:</strong> {metrics['avg_attendance']:.1f}%</p>
            <p><strong>⚠️ Avg Risk Score:</strong> {metrics['avg_risk_score']:.0f}/100</p>
            <p><strong>📚 Total Backlogs:</strong> {int(metrics['total_backlogs'])}</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TOP PERFORMERS TAB
# ==========================================

def top_performers_tab(df):
    """Display top performers tab content"""
    st.markdown("### 🌟 Top 5 Performing Students")
    
    top_df = get_top_performers(df)
    
    if top_df.empty:
        st.info("No top performers found.")
    else:
        cols = st.columns(3)
        for idx, (_, student) in enumerate(top_df.iterrows()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="student-card low-risk">
                    <h4 style="margin:0;">{student['name']}</h4>
                    <p style="color:#AAA; margin:0.5rem 0;">
                        📊 Score: {student['average_score']:.1f}%<br>
                        📝 Attendance: {student['attendance_percent']:.1f}%<br>
                        📚 Study: {student['study_hours_per_week']}/week
                    </p>
                    <p style="color:#4CAF50; font-weight:600; margin:0;">✅ Performing Well</p>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# STUDENTS AT RISK TAB
# ==========================================

def students_at_risk_tab(df):
    """Display students at risk tab content"""
    st.markdown("### ⚠️ Students Requiring Attention")
    
    risk_df = df[df["Risk"]]
    
    if risk_df.empty:
        st.success("🎉 No students currently at risk!")
    else:
        # Filter options
        risk_filter = st.selectbox(
            "Filter by risk level:",
            ["All", "High Risk", "Medium Risk"]
        )
        
        filtered_df = risk_df
        if risk_filter != "All":
            filtered_df = risk_df[risk_df["Risk_Level"] == risk_filter]
        
        for _, student in filtered_df.iterrows():
            risk_class = "high-risk" if student["Risk_Level"] == "High Risk" else "medium-risk"
            
            st.markdown(f"""
            <div class="student-card {risk_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;">{student['name']}</h4>
                    <span style="font-weight:600;">{student['Risk_Level']}</span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:1rem;">
                    <div>
                        <p style="color:#AAA; margin:0;">Score</p>
                        <p style="font-weight:600; margin:0; color:white;">{student['average_score']:.1f}%</p>
                    </div>
                    <div>
                        <p style="color:#AAA; margin:0;">Attendance</p>
                        <p style="font-weight:600; margin:0; color:white;">{student['attendance_percent']:.1f}%</p>
                    </div>
                    <div>
                        <p style="color:#AAA; margin:0;">Study Hours</p>
                        <p style="font-weight:600; margin:0; color:white;">{student['study_hours_per_week']}/wk</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# AI RECOMMENDATION TAB WITH CHAT BOT
# ==========================================

def ai_recommendation_tab(df):
    """Display AI recommendation tab with integrated chat bot"""

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("### 🤖 AI Counselor Chat Bot")
    st.markdown("Ask me anything about student performance, risks, or recommendations!")

    # Layout columns
    col1, col2 = st.columns([1, 1])

    # ✅ LEFT SIDE — STUDENT SELECTOR (FIXED)
    with col1:
        st.markdown("#### 📊 Student Selector")

        selected_student = st.selectbox(
            "Choose a student for personalized advice:",
            df['name'].tolist(),
            key="student_selector"
        )

        student_data = df[df['name'] == selected_student].iloc[0]

        st.markdown(f"""
        <div class="info-box">
            <p><strong>📚 Subject Scores:</strong></p>
            <p>Subject 1: {student_data['subject1']:.1f}% | Subject 2: {student_data['subject2']:.1f}%</p>
            <p>Subject 3: {student_data['subject3']:.1f}% | Subject 4: {student_data['subject4']:.1f}%</p>
            <p><strong>📊 Average:</strong> {student_data['average_score']:.1f}%</p>
            <p><strong>📝 Attendance:</strong> {student_data['attendance_percent']:.1f}%</p>
            <p><strong>⚠️ Risk Score:</strong> {student_data['Risk_Score']}/100 ({student_data['Risk_Level']})</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🎯 Get Personalized Advice", use_container_width=True):
            with st.spinner("🤔 AI is analyzing..."):
                advice = get_individual_ai_advice(student_data)

                st.session_state.chat_history.append({
                    "role": "user",
                    "message": f"Advice for {selected_student}"
                })
                st.session_state.chat_history.append({
                    "role": "bot",
                    "message": advice
                })

    # ✅ RIGHT SIDE — STUDY PLAN + GAUGE
    with col2:
        st.markdown("#### 💬 Study Plan")

        study_plan = generate_study_plan(student_data)

        st.markdown(f"""
        <div class="info-box">
            <p style="font-weight:600; color:white;">📚 Recommended Plan:</p>
            <p style="color:#AAA;">{study_plan}</p>
        </div>
        """, unsafe_allow_html=True)

        success = 100 - student_data['Risk_Score']

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=success,
            title={'text': "Success Probability", 'font': {'color': 'white'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': 'white'},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 40], 'color': "#ffebee"},
                    {'range': [40, 70], 'color': "#fff3e0"},
                    {'range': [70, 100], 'color': "#e8f5e8"}
                ],
            }
        ))

        fig.update_layout(
            height=220,
            margin=dict(t=30, b=0, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white'}
        )

        st.plotly_chart(fig, use_container_width=True)

    # =====================================
    # CHAT SECTION
    # =====================================

    st.markdown("---")
    st.markdown("#### 💭 Chat with AI Counselor")

    for message in st.session_state.chat_history[-6:]:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message-user"><strong>You:</strong> {message['message']}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message-bot"><strong>AI:</strong> {message['message']}</div>
            """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])

    with col1:
        question = st.text_input(
            "Ask anything...",
            placeholder="e.g., Who needs immediate attention?",
            label_visibility="collapsed"
        )

    with col2:
        ask = st.button("Send", use_container_width=True)

    if ask and question:
        with st.spinner("🤖 Thinking..."):
            st.session_state.chat_history.append({"role": "user", "message": question})
            response = counselor_chat(question, df)
            st.session_state.chat_history.append({"role": "bot", "message": response})
            st.rerun()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ==========================================
# MAIN APP
# ==========================================

def main():
    """Main application"""
    # Load dark theme
    load_dark_theme()
    
    # Display header
    display_header()
    
    # Create sidebar and get uploaded file
    file = create_sidebar()
    
    # Main content
    if file:
        try:
            # Load and process data
            with st.spinner("🔄 Analyzing student data..."):
                df = load_file(file)
                df = analyze_risk(df)
                df = calculate_risk_score_and_level(df)
            
            # Display metrics
            display_metrics(df)
            
            # Create tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Executive Summary",
                "⭐ Top Performers",
                "⚠️ Students at Risk",
                "🤖 AI Recommendation"
            ])
            
            # Populate tabs
            with tab1:
                executive_summary_tab(df)
            
            with tab2:
                top_performers_tab(df)
            
            with tab3:
                students_at_risk_tab(df)
            
            with tab4:
                ai_recommendation_tab(df)
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your file format is correct and try again.")
    
    else:
        # Show upload prompt
        st.markdown("""
        <div style="text-align:center; padding:4rem 2rem; background:#1E1E2E; border-radius:20px; 
                    box-shadow:0 10px 30px rgba(0,0,0,0.3); margin-top:2rem; border:1px solid #333;">
            <p style="font-size:4rem; margin:0;">📤</p>
            <h3 style="color:#667eea;">Upload a file to begin analysis</h3>
            <p style="color:#AAA; margin:1rem 0;">Support for CSV, Excel, Word, PDF, and Images</p>
            <p style="color:#666; font-size:0.9rem;">Your data will be processed securely using OCR + AI technology</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>Powered by OCR + AI • Secure Processing • Real-time Analysis</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# RUN APP
# ==========================================

if __name__ == "__main__":
    main()
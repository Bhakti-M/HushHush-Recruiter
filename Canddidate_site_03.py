import streamlit as st
import pandas as pd
import time
from datetime import datetime
from pathlib import Path

# Configure theme colors
THEME_COLOR = "#4f0202"
ACCENT_COLOR = "#F4D03F"
BACKGROUND_COLOR = "#595353"

def load_questions():
    """Load questions from the question bank Excel file."""
    BASE_DIR = Path(__file__).resolve().parent
    QUESTION_BANK_FILE = BASE_DIR / "AI_ML_Coding_Challenge_Questions.xlsx"
    if not QUESTION_BANK_FILE.exists():
        st.error("Question bank file not found. Please ensure AI_ML_Coding_Challenge_Questions.xlsx is in the directory.")
        return None
    try:
        df = pd.read_excel(QUESTION_BANK_FILE, engine='openpyxl')
        required_columns = ["Question", "Difficulty", "Topics", "Expected Output Example"]
        if not all(col in df.columns for col in required_columns):
            st.error("Missing required columns in the question bank")
            return None
        return df[required_columns].dropna()
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return None

def initialize_session():
    defaults = {
        'questions': None, 'current_q': 0, 'answers': {},
        'quiz_active': False, 'progress': 0, 'start_time': None,
        'quiz_duration': 60 * 60, 'user_name': "", 'user_id': "",
        'selected_topics': [], 'difficulty': "All Levels",
        'answered': {}
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)

def select_questions(df, num=15):
    # Difficulty filter
    if st.session_state.difficulty != "All Levels":
        df = df[df["Difficulty"] == st.session_state.difficulty]
    
    # Topic filter
    if st.session_state.selected_topics:
        topic_mask = df["Topics"].apply(
            lambda t: any(topic.strip() in st.session_state.selected_topics 
                     for topic in t.split(','))
        )
        df = df[topic_mask]
    
    return df.sample(min(num, len(df))).reset_index(drop=True)

def start_quiz():
    df = load_questions()
    if df is not None:
        st.session_state.questions = select_questions(df)
        if not st.session_state.questions.empty:
            st.session_state.quiz_active = True
            st.session_state.current_q = 0  # Reset index on new quiz start
            st.session_state.start_time = time.time()
            st.rerun()

def time_remaining():
    elapsed = time.time() - st.session_state.start_time
    remaining = st.session_state.quiz_duration - elapsed
    return max(0, int(remaining))

def question_navigator():
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("⏮ Previous", disabled=st.session_state.current_q == 0):
            st.session_state.current_q -= 1
    with col2:
        if st.button("Next ⏭", disabled=st.session_state.current_q == len(st.session_state.questions)-1):
            st.session_state.current_q += 1

def save_answer(q_index, answer):
    st.session_state.answers[q_index] = answer
    st.session_state.answered[q_index] = True  # Mark question as answered
    if len(st.session_state.questions) > 0:
        st.session_state.progress = len(st.session_state.answers) / len(st.session_state.questions) * 100
    else:
        st.session_state.progress = 0

def submit_quiz():
    st.session_state.quiz_active = False
    try:
        # Initialize the results dictionary
        results = {
            "Candidate": st.session_state.user_name,
            "UserID": st.session_state.user_id,
            "CompletionTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add each question and its details as separate columns
        for idx, row in st.session_state.questions.iterrows():
            results[f"Q{idx+1}"] = row['Question']
            results[f"Topics_Q{idx+1}"] = row['Topics']
            results[f"Difficulty_Q{idx+1}"] = row['Difficulty']
            results[f"ExpectedOutput_Q{idx+1}"] = row['Expected Output Example']
            results[f"Answer_Q{idx+1}"] = st.session_state.answers.get(idx, "No response")
        
        # Save to Excel
        results_dir = Path("TechnicalResults")
        results_dir.mkdir(exist_ok=True)
        filename = results_dir / f"{st.session_state.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame([results]).to_excel(filename, index=False, engine='openpyxl')
        
        st.success("✅ Answers submitted successfully! Results saved.")
    except Exception as e:
        st.error(f"Submission error: {str(e)}")

def quiz_interface():
    # Bounds check for current_q
    if st.session_state.current_q >= len(st.session_state.questions):
        st.session_state.current_q = max(0, len(st.session_state.questions) - 1)
    if st.session_state.current_q < 0:
        st.session_state.current_q = 0
    
    current_q = st.session_state.current_q
    question_data = st.session_state.questions.iloc[current_q]
    
    st.markdown(f"""
    <style>
        .stProgress > div > div {{ background-color: {THEME_COLOR}; }}
        .stTextArea textarea {{ border: 2px solid {THEME_COLOR}; }}
        .stExpander {{ border: 1px solid {THEME_COLOR}; }}
        .stButton button:disabled {{ background-color: #4CAF50; color: white; }}  /* Green color for answered questions */
    </style>
    """, unsafe_allow_html=True)

    st.header("💻 Technical Screening Challenge")
    
    # Time display
    time_left = time_remaining()
    mins, secs = divmod(time_left, 60)
    time_col, prog_col = st.columns([1, 4])
    with time_col:
        st.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
    with prog_col:
        st.progress(st.session_state.progress/100)
    
    # Question display
    with st.expander(f"Question {current_q+1} of {len(st.session_state.questions)}", expanded=True):
        st.markdown(f"""
        **Difficulty:** {question_data['Difficulty']}  
        **Topics:** {question_data['Topics']}
        """)
        st.markdown(f"#### {question_data['Question']}")
        st.info(f"**Expected Output Format:**\n```\n{question_data['Expected Output Example']}\n```")
        
        answer = st.text_area(
            "Your Solution:", 
            key=f"answer_{current_q}", 
            height=200,
            help="Write your code implementation or detailed explanation here"
        )
        
        if st.button("💾 Save Response", use_container_width=True, disabled=st.session_state.answered.get(current_q, False)):
            save_answer(current_q, answer)
            st.rerun()  # Rerun to update the button state
    
    question_navigator()
    
    if st.button("🏁 Final Submission", type="primary", use_container_width=True, disabled=len(st.session_state.answers) != len(st.session_state.questions)):
        submit_quiz()

def main():
    st.set_page_config(
        page_title="Hush Hush Recruiter", 
        page_icon="💻", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    initialize_session()
    
    # Get user_id from URL query parameter
    user_id = st.query_params.get("user_id", "")
    if user_id:
        st.session_state.user_id = user_id  # Pre-fill user_id from URL

    if not st.session_state.quiz_active:
        st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;500;700&display=swap');
            
            .main-container {{
                padding: 4rem 2rem;
                background: linear-gradient(135deg, {BACKGROUND_COLOR}, #3a3434);
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                margin: 2rem 0;
            }}
            
            .title-container {{
                text-align: center;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                backdrop-filter: blur(10px);
                margin-bottom: 3rem;
                animation: fadeIn 1s ease-in;
            }}
            
            .feature-card {{
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 15px;
                margin: 1rem 0;
                transition: transform 0.3s ease;
                border-left: 4px solid {ACCENT_COLOR};
            }}
            
            .feature-card:hover {{
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.1);
            }}
            
            @keyframes floating {{
                0% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
                100% {{ transform: translateY(0px); }}
            }}
            
            .hero-icon {{
                font-size: 4rem;
                animation: floating 3s ease-in-out infinite;
                color: {ACCENT_COLOR};
                margin: 1rem;
            }}
            
            .start-form {{
                background: rgba(255, 255, 255, 0.05);
                padding: 2rem;
                border-radius: 15px;
                margin-top: 2rem;
            }}
            
        </style>
        
        <div class="main-container">
            <div class="title-container">
                <div class="hero-icon">💼🚀</div>
                <h1 style="color: {THEME_COLOR}; font-family: 'Roboto', sans-serif; font-weight: 700; font-size: 2.5rem;">
                    Hush Hush Recruiter
                </h1>
                <h3 style="color: {ACCENT_COLOR}; font-family: 'Roboto', sans-serif; font-weight: 300; margin-top: 1rem;">
                    Next-Gen Technical Assessment Platform
                </h3>
            </div>
            
        <div class="feature-grid-container" style="display: flex; justify-content: center; width: 100%; padding: 1rem 0;">
            <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; max-width: 1200px; width: 100%;">
                <!-- Feature cards remain the same -->
                </div>
            </div>

        <div class="start-form" style="text-align: center;">
            <h3 style="color: #F4D03F; margin-bottom: 1.5rem; padding: 0 1rem; display: inline-block; border-bottom: 2px solid #F4D03F;">
                    🚀 Start Your Assessment
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("candidate_info"):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.user_name = st.text_input("👤 Candidate Name", placeholder="John Doe", value=st.session_state.user_name if st.session_state.user_name else "")
            with col2:
                st.session_state.user_id = st.text_input("🆔 Unique Candidate ID", placeholder="ABC-1234", value=st.session_state.user_id if st.session_state.user_id else "")
            
            df = load_questions()
            if df is not None:
                # Topic selection
                all_topics = set()
                for topics in df['Topics']:
                    for topic in topics.split(','):
                        all_topics.add(topic.strip())
                
                st.session_state.selected_topics = st.multiselect(
                    "📚 Select assessment topics:",
                    options=sorted(all_topics),
                    help="Select at least one topic for question filtering",
                    placeholder="Choose your focus areas..."
                )
                
                # Difficulty selection
                difficulties = ["All Levels"] + sorted(df['Difficulty'].unique())
                st.session_state.difficulty = st.selectbox(
                    "⚡ Select difficulty level:",
                    options=difficulties,
                    index=0
                )
            
            if st.form_submit_button("🚀 Start Assessment", use_container_width=True):
                if st.session_state.user_name and st.session_state.user_id:
                    start_quiz()
                else:
                    st.error("⚠️ Please provide both name and candidate ID")
        
        st.markdown("""
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 2rem; color: #ffffff99;">
            <p>🔒 All assessments are securely recorded and encrypted</p>
            <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1rem;">
                <span>📞 Contact Support</span>
                <span>|</span>
                <span>📄 Privacy Policy</span>
                <span>|</span>
                <span>⚙️ System Requirements</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    else:
        quiz_interface()

if __name__ == "__main__":
    main()
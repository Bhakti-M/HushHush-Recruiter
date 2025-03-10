import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import glob
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Import functions from separate files
try:
    from Data_extracation_Processing import fetch_github_profiles, clean_and_process_data
    from mailing import send_emails_to_good_candidates
except ImportError as e:
    st.error(f"Error importing required modules: {str(e)}. Ensure Data_extraction_Processing.py and mailing.py are in the same directory.")

# Theme colors with green and blue shades
THEME_COLOR = "#28A745"  # Green for primary accents
ACCENT_COLOR = "#00C4CC"  # Softer blue shade (replacing pink)
BACKGROUND_COLOR = "#0A0A23"  # Dark navy background
TEXT_COLOR = "#FFFFFF"  # White for main text (including headers)
SUBTEXT_COLOR = "#B0BEC5"  # Softer gray for subtext
CARD_BACKGROUND = "rgba(255, 255, 255, 0.05)"  # Subtle card background

# Initialize session state
if 'selected_submission' not in st.session_state:
    st.session_state.selected_submission = None
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"
if 'classified_candidates' not in st.session_state:
    st.session_state.classified_candidates = None
if 'candidate_counts' not in st.session_state:
    st.session_state.candidate_counts = None
if 'email_sending_complete' not in st.session_state:
    st.session_state.email_sending_complete = False

# Path to the question bank file
BASE_DIR = Path(__file__).resolve().parent
QUESTION_BANK_FILE = BASE_DIR / "AI_ML_Coding_Challenge_Questions.xlsx"

def load_submissions():
    """Load all submission files from the TechnicalResults directory."""
    results_dir = Path("TechnicalResults")
    submission_files = list(results_dir.glob("*.xlsx"))
    
    if not submission_files:
        return pd.DataFrame()
    
    all_submissions = []
    for file in submission_files:
        try:
            df = pd.read_excel(file, engine='openpyxl')
            df['SubmissionFile'] = str(file)
            all_submissions.append(df)
        except Exception as e:
            st.error(f"Error reading {file}: {str(e)}")
    
    return pd.concat(all_submissions, ignore_index=True) if all_submissions else pd.DataFrame()

def load_questions():
    """Load questions from the question bank Excel file."""
    try:
        df = pd.read_excel(QUESTION_BANK_FILE, engine='openpyxl')
        required_columns = ["Question", "Difficulty", "Topics", "Expected Output Example"]
        if not all(col in df.columns for col in required_columns):
            st.error("Missing required columns in the question bank")
            return pd.DataFrame()
        return df[required_columns].dropna()
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return pd.DataFrame()

def save_questions(df):
    """Save updated questions to the question bank Excel file."""
    try:
        df.to_excel(QUESTION_BANK_FILE, index=False, engine='openpyxl')
        st.success("Question bank updated successfully!")
    except Exception as e:
        st.error(f"Error saving questions: {str(e)}")

def display_submission_details(submission):
    """Display detailed view of a selected submission."""
    if not isinstance(submission, pd.Series):
        st.error("Invalid submission data. Please select a valid submission.")
        return
    
    st.markdown(f"""
        <h2 style='color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Submission Details
        </h2>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Candidate:** {submission['Candidate']}")
    st.markdown(f"**User ID:** {submission['UserID']}")
    st.markdown(f"**Submission Time:** {submission['CompletionTime']}")
    
    # Dynamically find all questions in the submission
    idx = 1
    while f"Q{idx}" in submission:
        with st.expander(f"Question {idx}: {submission[f'Q{idx}']}", expanded=False):
            st.markdown(f"**Topics:** {submission[f'Topics_Q{idx}']}")
            st.markdown(f"**Difficulty:** {submission[f'Difficulty_Q{idx}']}")
            st.markdown(f"**Expected Output:**\n```\n{submission[f'ExpectedOutput_Q{idx}']}\n```")
            st.markdown(f"**Answer:**\n```\n{submission[f'Answer_Q{idx}']}\n```")
        idx += 1

def visualize_trends(df):
    """Visualize submission trends using Plotly."""
    if df.empty:
        st.warning("No data available for visualization.")
        return
    
    df['CompletionTime'] = pd.to_datetime(df['CompletionTime'])
    df['Date'] = df['CompletionTime'].dt.date
    submissions_per_day = df.groupby('Date').size().reset_index(name='Count')
    
    fig = px.line(
        submissions_per_day,
        x='Date',
        y='Count',
        title="Submissions Over Time",
        line_shape='spline',
        markers=True,
        color_discrete_sequence=[THEME_COLOR],
        template='plotly_dark'
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=8))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=TEXT_COLOR,
        title_font_color=ACCENT_COLOR,
        title_font_size=18,
        xaxis=dict(
            gridcolor='rgba(0, 196, 204, 0.1)',
            zerolinecolor='rgba(0, 196, 204, 0.1)'
        ),
        yaxis=dict(
            gridcolor='rgba(0, 196, 204, 0.1)',
            zerolinecolor='rgba(0, 196, 204, 0.1)'
        )
    )
    st.plotly_chart(fig, use_container_width=True)

def display_key_metrics(submissions_df, questions_df):
    """Display key metrics: Total Candidates, Total Submissions, Total Questions."""
    total_candidates = len(submissions_df['UserID'].unique()) if not submissions_df.empty else 0
    total_submissions = len(submissions_df) if not submissions_df.empty else 0
    total_questions = len(questions_df) if not questions_df.empty else 0
    
    st.markdown(f"""
        <h3 style='color: {ACCENT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Key Metrics
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div style='background: {CARD_BACKGROUND}; padding: 1.5rem; border-radius: 10px; border: 1px solid {ACCENT_COLOR}40; text-align: center; transition: all 0.3s ease;'>
                <h4 style='color: {SUBTEXT_COLOR}; text-shadow: 0 0 3px {SUBTEXT_COLOR}80; margin: 0;'>TOTAL CANDIDATES</h4>
                <p style='color: {TEXT_COLOR}; font-size: 2rem; margin: 0.5rem 0 0 0;'>{total_candidates}</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style='background: {CARD_BACKGROUND}; padding: 1.5rem; border-radius: 10px; border: 1px solid {ACCENT_COLOR}40; text-align: center; transition: all 0.3s ease;'>
                <h4 style='color: {SUBTEXT_COLOR}; text-shadow: 0 0 3px {SUBTEXT_COLOR}80; margin: 0;'>TOTAL SUBMISSIONS</h4>
                <p style='color: {TEXT_COLOR}; font-size: 2rem; margin: 0.5rem 0 0 0;'>{total_submissions}</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div style='background: {CARD_BACKGROUND}; padding: 1.5rem; border-radius: 10px; border: 1px solid {ACCENT_COLOR}40; text-align: center; transition: all 0.3s ease;'>
                <h4 style='color: {SUBTEXT_COLOR}; text-shadow: 0 0 3px {SUBTEXT_COLOR}80; margin: 0;'>TOTAL QUESTIONS</h4>
                <p style='color: {TEXT_COLOR}; font-size: 2rem; margin: 0.5rem 0 0 0;'>{total_questions}</p>
            </div>
        """, unsafe_allow_html=True)

def run_candidate_pipeline():
    """Run the pipeline to fetch, process, and classify candidates."""
    try:
        raw_data_file = fetch_github_profiles()
        processed_data_file = "Processed_GitHub_Candidates.csv"
        clean_and_process_data(raw_data_file, processed_data_file)
        df = pd.read_csv(processed_data_file)
        expected_features = ["Public Repos", "Followers"]
        available_features = [col for col in expected_features if col.lower() in df.columns.str.lower()]
        for feature in expected_features:
            if feature.lower() not in df.columns.str.lower():
                df[feature] = 0
            else:
                matching_col = next(col for col in df.columns if col.lower() == feature.lower())
                df[feature] = df[matching_col]
        scaler = StandardScaler()
        features_to_plot = expected_features
        df_transformed = df.copy()
        for feature in features_to_plot:
            df_transformed[feature] = np.log1p(df_transformed[feature])
        scaled_features_transformed = scaler.fit_transform(df_transformed[features_to_plot])
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        df_transformed["Cluster"] = kmeans.fit_predict(scaled_features_transformed)
        numeric_cols = df_transformed.select_dtypes(include=[np.number]).columns
        df_transformed_numeric = df_transformed[numeric_cols]
        cluster_means_transformed = df_transformed_numeric.groupby("Cluster").mean().sum(axis=1)
        good_cluster_transformed = cluster_means_transformed.idxmax()
        df_transformed["Candidate_Label"] = df_transformed["Cluster"].apply(lambda x: "Good" if x == good_cluster_transformed else "Bad")
        st.session_state.classified_candidates = df_transformed
        candidate_counts = df_transformed["Candidate_Label"].value_counts()
        st.session_state.candidate_counts = candidate_counts
        return True
    except Exception as e:
        st.error(f"Error running candidate pipeline: {str(e)}")
        return False

def display_candidate_list():
    """Display the list of classified candidates."""
    if "classified_candidates" not in st.session_state or st.session_state.classified_candidates is None:
        st.info("No classified candidates available. Please run 'Get Candidates' to fetch candidates.")
        return
    
    df = st.session_state.classified_candidates
    good_candidates = df[df["Candidate_Label"] == "Good"]
    bad_candidates = df[df["Candidate_Label"] == "Bad"]
    
    st.markdown(f"""
        <h4 style='color: {SUBTEXT_COLOR};'>Good Candidates ({len(good_candidates)})</h4>
    """, unsafe_allow_html=True)
    if not good_candidates.empty:
        display_df = good_candidates[["username", "name", "followers", "public repos", "github profile"]].copy()
        display_df.columns = ["Username", "Name", "Followers", "Public Repos", "GitHub Profile"]
        sort_column = st.selectbox("Sort Good Candidates by:", options=["Username", "Name", "Followers", "Public Repos"], index=0, key="sort_good")
        display_df = display_df.sort_values(sort_column)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No good candidates found.")
    
    st.markdown(f"""
        <h4 style='color: {SUBTEXT_COLOR};'>Bad Candidates ({len(bad_candidates)})</h4>
    """, unsafe_allow_html=True)
    if not bad_candidates.empty:
        display_df = bad_candidates[["username", "name", "followers", "public repos", "github profile"]].copy()
        display_df.columns = ["Username", "Name", "Followers", "Public Repos", "GitHub Profile"]
        sort_column = st.selectbox("Sort Bad Candidates by:", options=["Username", "Name", "Followers", "Public Repos"], index=0, key="sort_bad")
        display_df = display_df.sort_values(sort_column)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No bad candidates found.")

def display_quick_actions():
    """Display Quick Actions section with buttons."""
    st.markdown(f"""
        <h3 style='color: {ACCENT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Quick Actions
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔍 Review Submissions", use_container_width=True):
            st.session_state.page = "Submissions"
            st.session_state.email_sending_complete = False
            st.rerun()
    with col2:
        if st.button("📚 Manage Question Bank", use_container_width=True):
            st.session_state.page = "Question Bank"
            st.session_state.email_sending_complete = False
            st.rerun()
    with col3:
        if st.button("🌐 Get Candidates", use_container_width=True):
            with st.spinner("Fetching and classifying candidates..."):
                success = run_candidate_pipeline()
            if success:
                st.success("Candidates fetched and classified successfully!")
                st.session_state.page = "Classified Candidates"
                st.session_state.email_sending_complete = False
                st.rerun()
    with col4:
        if st.button("📧 Send Mail", use_container_width=True):
            if "classified_candidates" not in st.session_state or st.session_state.classified_candidates is None:
                st.warning("No classified candidates available. Please run 'Get Candidates' first.")
            else:
                email_status_container = st.empty()
                with st.spinner("Sending emails to good candidates..."):
                    try:
                        classified_df = st.session_state.classified_candidates
                        good_candidates = classified_df[classified_df["Candidate_Label"] == "Good"]
                        
                        if good_candidates.empty:
                            email_status_container.warning("No good candidates found to send emails.")
                        else:
                            st.write("Sending emails to the following good candidates:")
                            display_df = good_candidates[["username", "name"]].copy()
                            display_df.columns = ["Username", "Name"]
                            # Ensure the table spans the full width
                            st.dataframe(display_df, use_container_width=True)
                            
                            success, message = send_emails_to_good_candidates(classified_df, test_mode=True)
                            if success:
                                email_status_container.success(message)
                            else:
                                email_status_container.error(message)
                    except Exception as e:
                        email_status_container.error(f"Unexpected error sending emails: {str(e)}")
                st.write("Email sending completed. You can now navigate or perform other actions.")
                st.session_state.email_sending_complete = True

def question_bank_page():
    """Page for managing the question bank."""
    questions_df = load_questions()
    
    if questions_df.empty:
        st.warning("No questions available in the question bank.")
        questions_df = pd.DataFrame(columns=["Question", "Difficulty", "Topics", "Expected Output Example"])
    
    st.markdown(f"""
        <h2 style='color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Question Bank Management
        </h2>
    """, unsafe_allow_html=True)
    
    st.subheader("Add New Question")
    with st.form("add_question_form"):
        new_question = st.text_input("Question", placeholder="Enter the question here...")
        new_difficulty = st.selectbox("Difficulty", options=["Easy", "Medium", "Medium-Hard", "Hard"])
        new_topics = st.text_input("Topics (comma-separated)", placeholder="e.g., Graph Algorithms, DFS")
        new_expected_output = st.text_area("Expected Output Example", placeholder="e.g., True if cycle exists, else False")
        submit_button = st.form_submit_button("Add Question")
        
        if submit_button:
            if new_question and new_difficulty and new_topics and new_expected_output:
                new_row = pd.DataFrame({
                    "Question": [new_question],
                    "Difficulty": [new_difficulty],
                    "Topics": [new_topics],
                    "Expected Output Example": [new_expected_output]
                })
                questions_df = pd.concat([questions_df, new_row], ignore_index=True)
                save_questions(questions_df)
                st.success("Question added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields.")
    
    st.subheader("Existing Questions")
    for idx, row in questions_df.iterrows():
        with st.expander(f"Question {idx + 1}: {row['Question'][:50]}...", expanded=False):
            st.markdown(f"**Difficulty:** {row['Difficulty']}")
            st.markdown(f"**Topics:** {row['Topics']}")
            st.markdown(f"**Expected Output:**\n```\n{row['Expected Output Example']}\n```")
            
            with st.form(f"edit_form_{idx}"):
                edited_question = st.text_input("Question", value=row['Question'])
                edited_difficulty = st.selectbox("Difficulty", options=["Easy", "Medium", "Medium-Hard", "Hard"], index=["Easy", "Medium", "Medium-Hard", "Hard"].index(row['Difficulty']))
                edited_topics = st.text_input("Topics (comma-separated)", value=row['Topics'])
                edited_expected_output = st.text_area("Expected Output Example", value=row['Expected Output Example'])
                edit_button = st.form_submit_button("Update Question")
                
                if edit_button:
                    questions_df.at[idx, "Question"] = edited_question
                    questions_df.at[idx, "Difficulty"] = edited_difficulty
                    questions_df.at[idx, "Topics"] = edited_topics
                    questions_df.at[idx, "Expected Output Example"] = edited_expected_output
                    save_questions(questions_df)
                    st.success("Question updated successfully!")
                    st.rerun()
            
            if st.button(f"Delete Question {idx + 1}", key=f"delete_{idx}"):
                questions_df = questions_df.drop(idx).reset_index(drop=True)
                save_questions(questions_df)
                st.success("Question deleted successfully!")
                st.rerun()

def submissions_page(submissions_df):
    """Page for reviewing submissions."""
    st.markdown(f"""
        <h2 style='color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Candidate Submissions
        </h2>
    """, unsafe_allow_html=True)
    
    if not submissions_df.empty:
        # Prepare the display DataFrame with candidate info
        display_df = submissions_df[['Candidate', 'UserID', 'CompletionTime']].copy()
        display_df.columns = ['Candidate', 'User ID', 'Submission Time']
        
        # For each submission, find the first question's topics and difficulty as a summary
        display_df['Topics'] = ''
        display_df['Difficulty'] = ''
        for idx in range(len(submissions_df)):
            for q_idx in range(1, 100):  # Arbitrary large number to find all questions
                if f"Topics_Q{q_idx}" in submissions_df.columns:
                    display_df.at[idx, 'Topics'] = submissions_df.at[idx, f"Topics_Q{q_idx}"]
                    display_df.at[idx, 'Difficulty'] = submissions_df.at[idx, f"Difficulty_Q{q_idx}"]
                    break
        
        sort_column = st.selectbox("Sort by:", options=['Candidate', 'User ID', 'Submission Time', 'Difficulty'], index=0)
        display_df = display_df.sort_values(sort_column)
        
        st.dataframe(display_df, use_container_width=True)
        
        selected_index = st.selectbox(
            "Select a submission to view details:",
            options=range(len(submissions_df)) if not submissions_df.empty else [],
            format_func=lambda i: f"{submissions_df['Candidate'].iloc[i]} ({submissions_df['UserID'].iloc[i]})" if not submissions_df.empty else "No submissions"
        )
        
        if st.button("🔍 View Details", use_container_width=True) and selected_index is not None and 0 <= selected_index < len(submissions_df):
            st.session_state.selected_submission = submissions_df.iloc[selected_index]
        
        if st.session_state.selected_submission is not None:
            display_submission_details(st.session_state.selected_submission)
        
        if st.button("💾 Download Results as CSV", use_container_width=True):
            csv = submissions_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="submissions.csv",
                mime="text/csv"
            )
    else:
        st.info("No submissions available to display.")

def classified_candidates_page():
    """Page for displaying classified candidates."""
    st.markdown(f"""
        <h2 style='color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Classified Candidates
        </h2>
    """, unsafe_allow_html=True)
    
    display_candidate_list()

def dashboard_page(submissions_df, questions_df):
    """Dashboard page with metrics, quick actions, and trends."""
    st.markdown(f"""
        <h2 style='color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Dashboard
        </h2>
    """, unsafe_allow_html=True)
    
    display_key_metrics(submissions_df, questions_df)
    st.markdown("<br>", unsafe_allow_html=True)
    display_quick_actions()
    st.markdown("<br>", unsafe_allow_html=True)
    display_candidate_list()
    st.markdown("<br>", unsafe_allow_html=True)
    visualize_trends(submissions_df)

def main():
    st.set_page_config(
        page_title="Hush Hush Recruiter Dashboard",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
            
            .stApp {{
                background: linear-gradient(135deg, {BACKGROUND_COLOR}, #1B1B3A);
                color: {TEXT_COLOR};
                font-family: 'Orbitron', sans-serif;
            }}
            
            .sidebar .sidebar-content {{
                background: rgba(10, 10, 35, 0.9);
                border-right: 1px solid {ACCENT_COLOR}40;
                padding: 1.5rem;
            }}
            
            .stTextInput > div > input {{
                border: none;
                background: rgba(0, 196, 204, 0.1);
                color: {TEXT_COLOR};
                box-shadow: 0 0 5px {ACCENT_COLOR}40;
                transition: all 0.3s ease;
                border-radius: 5px;
                width: 100%;
            }}
            
            .stTextInput > div > input:hover {{
                box-shadow: 0 0 10px {ACCENT_COLOR}80;
            }}
            
            .stMultiSelect div, .stSelectbox div {{
                border: none;
                background: rgba(40, 167, 69, 0.1);
                color: {TEXT_COLOR};
                box-shadow: 0 0 5px {THEME_COLOR}40;
                border-radius: 5px;
                width: 100%;
            }}
            
            .stExpander {{
                background: {CARD_BACKGROUND};
                border: 1px solid {ACCENT_COLOR}40;
                box-shadow: 0 0 5px {ACCENT_COLOR}20;
                border-radius: 5px;
            }}
            
            .stButton > button {{
                background: linear-gradient(45deg, {THEME_COLOR}, {ACCENT_COLOR});
                color: {BACKGROUND_COLOR};
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                transition: all 0.3s ease;
                box-shadow: 0 0 5px {THEME_COLOR}40;
                width: 100%;
            }}
            
            .stButton > button:hover {{
                box-shadow: 0 0 10px {THEME_COLOR}80;
                transform: scale(1.02);
            }}
            
            h1, h2, h3, h4 {{
                font-family: 'Orbitron', sans-serif;
                text-shadow: 0 0 5px {ACCENT_COLOR}80;
            }}
            
            .stDataFrame {{
                width: 100% !important;
                max-width: 100% !important;
            }}
            
            .stDataFrame table {{
                background: {CARD_BACKGROUND};
                border: 1px solid {ACCENT_COLOR}40;
                color: {TEXT_COLOR};
                border-radius: 5px;
                width: 100% !important;
                max-width: 100% !important;
            }}
            
            .stDataFrame table th {{
                background: {THEME_COLOR}80;
                color: {BACKGROUND_COLOR};
            }}
            
            .stDataFrame table td:hover {{
                background: rgba(0, 196, 204, 0.1);
                cursor: pointer;
            }}

            .doodle-logo {{
                text-align: center;
                font-size: 2rem;
                color: {ACCENT_COLOR};
                text-shadow: 0 0 5px {ACCENT_COLOR}80;
                animation: neonBlink 2s infinite alternate;
                margin-bottom: 1.5rem;
            }}
            
            @keyframes neonBlink {{
                0% {{ opacity: 0.8; }}
                50% {{ opacity: 1; text-shadow: 0 0 10px {ACCENT_COLOR}80; }}
                100% {{ opacity: 0.8; }}
            }}
            
            .nav-container {{
                margin-top: 1rem;
            }}
            
            .nav-item {{
                display: flex;
                align-items: center;
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 5px;
                transition: all 0.3s ease;
                cursor: pointer;
                color: {SUBTEXT_COLOR};
            }}
            
            .nav-item.active {{
                background: rgba(40, 167, 69, 0.3);
                box-shadow: 0 0 8px {THEME_COLOR}60;
                color: {TEXT_COLOR};
            }}
            
            .nav-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 0.75rem;
                background: {ACCENT_COLOR};
            }}
            
            .nav-dot.inactive {{
                background: #444;
            }}
            
            input[type="radio"] {{
                display: none;
            }}
            
            label.nav-label {{
                display: flex;
                align-items: center;
                width: 100%;
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 5px;
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            
            label.nav-label:hover {{
                background: rgba(40, 167, 69, 0.1);
                box-shadow: 0 0 5px {THEME_COLOR}40;
            }}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <h1 style='text-align: center; color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            🔍 Hush Hush Recruiter Dashboard
        </h1>
        <h3 style='text-align: center; color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Uncover Talent in a Neon World
        </h3>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
        <div class="doodle-logo">
            Doodle
        </div>
        <h3 style='color: {TEXT_COLOR}; text-shadow: 0 0 5px {ACCENT_COLOR}80;'>
            Admin Panel
        </h3>
        <p style='color: {SUBTEXT_COLOR}; text-shadow: 0 0 3px {SUBTEXT_COLOR}80;'>
            Hush Hush Recruiter
        </p>
        <h4 style='color: {SUBTEXT_COLOR}; margin-top: 2rem;'>
            Navigate
        </h4>
    """, unsafe_allow_html=True)
    
    pages = ["Dashboard", "Submissions", "Question Bank", "Classified Candidates"]
    selected_page = st.sidebar.radio(
        "navigation",
        pages,
        index=pages.index(st.session_state.page),
        key="nav_radio",
        label_visibility="hidden"
    )
    
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.session_state.email_sending_complete = False
        st.rerun()
    
    submissions_df = load_submissions()
    questions_df = load_questions()
    
    if st.session_state.page == "Dashboard":
        dashboard_page(submissions_df, questions_df)
    elif st.session_state.page == "Submissions":
        submissions_page(submissions_df)
    elif st.session_state.page == "Question Bank":
        question_bank_page()
    elif st.session_state.page == "Classified Candidates":
        classified_candidates_page()

if __name__ == "__main__":
    main()
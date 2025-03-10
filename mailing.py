import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  
SENDER_EMAIL = 'hushhushrecruiter09@gmail.com'  
SENDER_PASSWORD = 'aydn ibmn nisy oifp'  # Ensure this is an App Password if using Gmail

def send_email(receiver_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {receiver_email}")
        return True, f"Email sent to {receiver_email}"
    except Exception as e:
        print(f"Failed to send email to {receiver_email}: {e}")
        return False, f"Failed to send email to {receiver_email}: {e}"

def send_emails_to_good_candidates(classified_df=None, test_mode=False):
    if classified_df is None or classified_df.empty:
        return False, "No classified candidates provided."
    
    good_candidates = classified_df[classified_df['Candidate_Label'] == 'Good']
    if good_candidates.empty:
        return False, "No good candidates found to send emails."
    
    if 'email' not in good_candidates.columns.str.lower():
        if test_mode:
            good_candidates['Email'] = good_candidates['username'].apply(lambda x: f"{x}@example.com")
        else:
            return False, "No email addresses found in candidate data. Cannot send emails."
    
    success_count = 0
    for index, row in good_candidates.iterrows():
        receiver_email = row['Email']
        name = row.get('name', row['username'])
        subject = "Invitation to Online Assessment for [Job Title]"
        body = f"""
        Dear {name},

        We were impressed with your skills and would like to invite you to participate in the next stage of our hiring process: an online assessment.

        This assessment is designed to evaluate your skills and knowledge relevant to the role. It will consist of multiple-choice questions and coding challenges. Please allow approximately 1 hour to complete the assessment.

        To begin, please click on the following link: http://localhost:8501

        This link will be active for 48 hours from the time of this email. Please ensure you complete the assessment within this timeframe.

        If you have any questions or encounter any technical difficulties, please do not hesitate to contact us at {SENDER_EMAIL}.

        We wish you the best of luck with the assessment.

        Best regards,
        Your Hush Hush Team
        """
        if test_mode:
            print(f"Test mode: Would send email to {receiver_email}")
            success_count += 1
        else:
            success, message = send_email(receiver_email, subject, body)
            if success:
                success_count += 1
    
    if success_count == len(good_candidates):
        return True, f"Successfully sent emails to {success_count} good candidates."
    else:
        return False, f"Sent emails to {success_count} out of {len(good_candidates)} good candidates."

def send_emails_from_excel(excel_file):
    df = pd.read_excel(excel_file)
    for index, row in df.iterrows():
        receiver_email = row['Email']
        name = row.get('Name', 'Candidate')
        subject = "Invitation to Online Assessment for [Job Title]"
        body = f"""
        Dear {name},

        We were impressed with your Skills and would like to invite you to participate in the next stage of our hiring process: an online assessment.

        This assessment is designed to evaluate your skills and knowledge relevant to the role. It will consist of [briefly describe the exam format, e.g., multiple-choice questions, coding challenges, etc.]. Please allow approximately [estimated time] to complete the assessment.

        To begin, please click on the following link: http://localhost:8501

        This link will be active for [duration, e.g., 48 hours] from the time of this email. Please ensure you complete the assessment within this timeframe.

        If you have any questions or encounter any technical difficulties, please do not hesitate to contact us at {SENDER_EMAIL}.

        We wish you the best of luck with the assessment.

        Best regards,
        Your Team
        """
        send_email(receiver_email, subject, body)

if __name__ == "__main__":
    excel_file = 'mails.xlsx'
    send_emails_from_excel(excel_file)
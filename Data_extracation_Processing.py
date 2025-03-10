import requests
import csv
import time
import pandas as pd
from datetime import datetime, timedelta

# GitHub API Token (Replace with your actual token)
GITHUB_TOKEN = "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"
GITHUB_API_URL = "https://api.github.com"

# Headers for authentication
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Search criteria
KEYWORDS = ["Python", "SQL", "Machine Learning", "ML", "Artificial Intelligence", "AI", "Data Science", "Natural Language Processing", "NLP", "Computer Vision"]
LOCATION = "Germany"
MIN_FOLLOWERS = 10

# API settings
PER_PAGE = 5
MAX_PAGES = 6


def fetch_github_profiles():
    """Fetch GitHub profiles matching the criteria."""
    all_candidates = []
    keyword_chunks = [KEYWORDS[i:i + 5] for i in range(0, len(KEYWORDS), 5)]
    
    for chunk in keyword_chunks:
        for page in range(1, MAX_PAGES + 1):
            search_query = f"{' OR '.join(chunk)} in:bio location:{LOCATION} followers:>{MIN_FOLLOWERS}"
            search_url = f"{GITHUB_API_URL}/search/users?q={search_query}&per_page={PER_PAGE}&page={page}"
            response = requests.get(search_url, headers=HEADERS)
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.json()}")
                break

            users = response.json().get("items", [])
            for user in users:
                user_data = fetch_user_details(user["login"])
                if user_data:
                    all_candidates.append(user_data)
            
            time.sleep(2)
    
    save_to_csv(all_candidates, "GitHub_Candidates.csv")
    return "GitHub_Candidates.csv"


def fetch_user_details(username):
    """Fetch detailed GitHub profile information."""
    user_url = f"{GITHUB_API_URL}/users/{username}"
    response = requests.get(user_url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error fetching user {username}: {response.status_code}")
        return None
    
    user_data = response.json()
    return {
        "Username": user_data.get("login"),
        "Name": user_data.get("name", ""),
        "Bio": user_data.get("bio", ""),
        "GitHub Profile": user_data.get("html_url"),
        "Location": user_data.get("location", ""),
        "Followers": user_data.get("followers", 0),
        "Public Repos": user_data.get("public_repos", 0),
    }


def save_to_csv(data, filename):
    """Save extracted data to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"📁 Data saved to {filename}")


def clean_and_process_data(input_csv, output_csv):
    """Clean and preprocess the extracted data."""
    df = pd.read_csv(input_csv)
    
    # Drop duplicates and missing values
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["Username", "GitHub Profile"], inplace=True)
    
    # Convert column names to lowercase
    df.columns = df.columns.str.lower()
    
    # Normalize text data
    df["bio"] = df["bio"].str.replace("[^a-zA-Z0-9 ]", "", regex=True).str.lower()
    
    df.to_csv(output_csv, index=False)
    print(f"📊 Processed data saved to {output_csv}")


def main():
    """Main function to execute the pipeline."""
    raw_data = fetch_github_profiles()
    processed_data = "Processed_GitHub_Candidates.csv"
    clean_and_process_data(raw_data, processed_data)


if __name__ == "__main__":
    main()
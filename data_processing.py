# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import MinMaxScaler

def load_data(filepath):
    """Load dataset from a CSV file."""
    return pd.read_csv(filepath)

def filter_candidates(df, skills):
    """Filter candidates based on required skills."""
    target = {s.strip().lower() for s in skills}
    match_scores = []
    mask = []

    for _, row in df.iterrows():
        combined = f"{row['Bio']}, {row['Top Languages']}".lower()
        skills_found = {s.strip() for s in combined.split(',') if s.strip()}
        match_pct = (len(skills_found & target) / len(target)) * 100
        match_scores.append(match_pct)
        mask.append(match_pct >= 10)

    df['Match_Score'] = match_scores
    return df[mask].reset_index(drop=True)

def clean_data(df):
    """Remove duplicates and irrelevant columns."""
    df.drop_duplicates(inplace=True)
    return df.drop(columns=['Username', 'Name', 'Bio', 'GitHub Profile', 'Location', 'Email', 'Top Languages'])

def extract_contributions(contribution_str):
    """Extract numerical values from contribution text."""
    if isinstance(contribution_str, str):
        commits = re.search(r'Commits:\s*(\d+)', contribution_str)
        prs = re.search(r'PRs:\s*(\d+)', contribution_str)
        issues = re.search(r'Issues:\s*(\d+)', contribution_str)
        return (int(commits.group(1)) if commits else 0,
                int(prs.group(1)) if prs else 0,
                int(issues.group(1)) if issues else 0)
    return (0, 0, 0)

def transform_data(df):
    """Apply transformations to extract structured information."""
    df[['Recent_Commits', 'Recent_PRs', 'Recent_Issues']] = df['Recent Contributions'].apply(
        lambda x: pd.Series(extract_contributions(x))
    )
    df[['Total_Commits', 'Total_PRs', 'Total_Issues']] = df['Total Contributions'].apply(
        lambda x: pd.Series(extract_contributions(x))
    )
    df.drop(columns=['Recent Contributions', 'Total Contributions', 'Total Commits', 'Organizations'], inplace=True)
    return df

def scale_data(df):
    """Normalize numerical columns using MinMaxScaler."""
    scaler = MinMaxScaler()
    return pd.DataFrame(scaler.fit_transform(df), columns=df.columns)

def main(filepath, output_path):
    df = load_data(filepath)
    skills_needed = ["Python", "Machine Learning", "Artificial Intelligence", "NLP"]
    df = filter_candidates(df, skills_needed)
    df = clean_data(df)
    df = transform_data(df)
    df = scale_data(df)
    df.to_csv(output_path, index=False)
    print("Data processing complete. Cleaned file saved.")

if __name__ == "__main__":
    main("/content/GitHub_Candidates (5).csv", "cleaned_data.csv")
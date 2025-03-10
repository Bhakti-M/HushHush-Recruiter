# -*- coding: utf-8 -*-

import requests
import csv
import time
from datetime import datetime, timedelta

# GitHub API Token (Replace with your actual token)
GITHUB_TOKEN = "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"

# GitHub API URL
GITHUB_API_URL = "https://api.github.com"

# Headers for authentication
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Search criteria
KEYWORDS = ["Python", "SQL", "Machine Learning", "ML", "Artificial Intellegence", "AI", "Data Science", "Natural Language Processing", "NLP", "Computer Vision"]  # Add more keywords here
LOCATION = "Germany"  # Try "United States" if no results
MIN_FOLLOWERS = 10

# API settings
PER_PAGE = 5  # Max allowed is 100
MAX_PAGES = 2  # Increase for more results

def fetch_github_profiles():
    all_candidates = []

    # Split keywords into chunks of 5 (to avoid exceeding the API limit)
    keyword_chunks = [KEYWORDS[i:i + 5] for i in range(0, len(KEYWORDS), 5)]

    for chunk in keyword_chunks:
        for page in range(1, MAX_PAGES + 1):
            print(f"Fetching page {page} for keywords: {chunk}...")

            # Combine keywords into a query string
            keyword_query = " OR ".join([f'"{keyword}"' for keyword in chunk])

            # Modify the search query to include keywords in the bio
            search_query = f"{keyword_query} in:bio location:{LOCATION} followers:>{MIN_FOLLOWERS}"
            print(f"Using search query: {search_query}")  # Add this line to see the query
            search_url = f"{GITHUB_API_URL}/search/users?q={search_query}&per_page={PER_PAGE}&page={page}"

            response = requests.get(search_url, headers=HEADERS)
            print(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining')}")

            if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.json()}")
                break

            users = response.json().get("items", [])
            print(f"API returned {len(users)} users on page {page}")

            for user in users:
                user_data = fetch_user_details(user["login"])
                if user_data:
                    # Ensure Bio is not None before filtering
                    bio = user_data.get("Bio", "")
                    if bio and any(keyword.lower() in bio.lower() for keyword in KEYWORDS):
                        all_candidates.append(user_data)

            time.sleep(2)  # Prevent rate limiting

    save_to_csv(all_candidates, "GitHub_Candidates.csv")


def fetch_user_details(username):
    """Fetch detailed profile data of a GitHub user"""
    user_url = f"{GITHUB_API_URL}/users/{username}"
    repos_url = f"{GITHUB_API_URL}/users/{username}/repos?per_page=100"  # Fetch more repos
    events_url = f"{GITHUB_API_URL}/users/{username}/events/public?per_page=100"  # Fetch more events
    orgs_url = f"{GITHUB_API_URL}/users/{username}/orgs"
    gists_url = f"{GITHUB_API_URL}/users/{username}/gists?per_page=100"  # Fetch more gists

    try:
        user_response = requests.get(user_url, headers=HEADERS)
        if user_response.status_code != 200:
            print(f"Error fetching user {username}: {user_response.status_code}")
            return None

        user_data = user_response.json()
        repos_data = fetch_all_pages(repos_url)
        events_data = fetch_all_pages(events_url)
        orgs_data = fetch_all_pages(orgs_url)
        gists_data = fetch_all_pages(gists_url)

        # Extract top languages
        top_languages = extract_languages(repos_data)

        # Extract public repositories count
        public_repos = user_data.get("public_repos", 0)

        # Extract top repositories count (repositories with at least 10 stars)
        top_repos = sum(1 for repo in repos_data if repo.get("stargazers_count", 0) >= 10)

        # Extract recent contribution activity (last 3 months)
        recent_contributions = extract_recent_contributions(events_data)

        # Extract GitHub organizations
        orgs_count = len(orgs_data)

        # Extract total gists
        total_gists = len(gists_data)

        # Get starred repositories count
        starred_repos_count = fetch_starred_repos_count(username)

        # Calculate total commits, pull requests, and issues
        total_commits = fetch_total_commits(username)
        total_pull_requests = fetch_total_pull_requests(username)
        total_issues = fetch_total_issues(username)
        total_contributions = fetch_total_contributions(username)

        return {
            "Username": user_data.get("login"),
            "Name": user_data.get("name", ""),
            "Bio": user_data.get("bio", ""),
            "GitHub Profile": user_data.get("html_url"),
            "Location": user_data.get("location", ""),
            "Email": user_data.get("email", "N/A"),
            "Public Repos": public_repos,
            "Top Repositories": top_repos,
            "Followers": user_data.get("followers"),
            "Top Languages": ", ".join(top_languages),
            "Recent Contributions": recent_contributions,
            "Organizations": orgs_count,
            "Total Gists": total_gists,
            "Starred Repositories": starred_repos_count,
            "Total Stars": sum(repo.get("stargazers_count", 0) for repo in repos_data),
            "Forked Repositories": sum(1 for repo in repos_data if repo.get("fork")),
            "Total Commits": total_commits,
            "Total Pull Requests": total_pull_requests,
            "Total Issues": total_issues,
            "Total Contributions": total_contributions,
        }
    except Exception as e:
        print(f"Error fetching details for {username}: {e}")
        return None


def fetch_total_commits(username):
    """Fetch total commits (including contributions to other repositories)"""
    search_url = f"{GITHUB_API_URL}/search/commits?q=author:{username}"
    response = requests.get(search_url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("total_count", 0)
    else:
        print(f"Error fetching total commits for {username}: {response.status_code}")
        return 0


def fetch_total_pull_requests(username):
    """Fetch total pull requests (including contributions to other repositories)"""
    search_url = f"{GITHUB_API_URL}/search/issues?q=author:{username}+type:pr"
    response = requests.get(search_url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("total_count", 0)
    else:
        print(f"Error fetching total pull requests for {username}: {response.status_code}")
        return 0


def fetch_total_issues(username):
    """Fetch total issues (including contributions to other repositories)"""
    search_url = f"{GITHUB_API_URL}/search/issues?q=author:{username}+type:issue"
    response = requests.get(search_url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("total_count", 0)
    else:
        print(f"Error fetching total issues for {username}: {response.status_code}")
        return 0


def fetch_total_contributions(username):
    """Fetch total contributions (commits, issues, and pull requests)"""
    total_commits = fetch_total_commits(username)
    total_pull_requests = fetch_total_pull_requests(username)
    total_issues = fetch_total_issues(username)
    return f"Commits: {total_commits}, PRs: {total_pull_requests}, Issues: {total_issues}"


def fetch_starred_repos_count(username):
    """Fetch the count of starred repositories for a GitHub user"""
    starred_url = f"{GITHUB_API_URL}/users/{username}/starred?per_page=100"  # Max per page is 100
    total_starred = 0

    while starred_url:
        response = requests.get(starred_url, headers=HEADERS)
        if response.status_code == 200:
            total_starred += len(response.json())
            # Check if there are more pages
            link_header = response.headers.get('link', '')
            if 'rel="next"' in link_header:
                next_link = [link.strip() for link in link_header.split(",") if 'rel="next"' in link]
                if next_link:
                    starred_url = next_link[0].split(";")[0].strip("<>")
                else:
                    starred_url = None
            else:
                starred_url = None
            time.sleep(1)  # Add a delay to avoid rate limiting
        else:
            print(f"Error fetching starred repos for {username}: {response.status_code}")
            break

    return total_starred


def fetch_all_pages(url):
    """Fetch all pages of data from a GitHub API endpoint"""
    all_data = []
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            all_data.extend(response.json())
            # Check if there are more pages
            link_header = response.headers.get('link', '')
            if 'rel="next"' in link_header:
                next_link = [link.strip() for link in link_header.split(",") if 'rel="next"' in link]
                if next_link:
                    url = next_link[0].split(";")[0].strip("<>")
                else:
                    url = None
            else:
                url = None
            time.sleep(1)  # Add a delay to avoid rate limiting
        else:
            print(f"Error fetching data from {url}: {response.status_code}")
            break
    return all_data


def extract_languages(repos_data):
    """Extracts top languages from a user's repositories"""
    languages = {}
    for repo in repos_data:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    return [lang[0] for lang in sorted(languages.items(), key=lambda x: x[1], reverse=True)]  # Top 3 languages


def extract_recent_contributions(events_data):
    """Extracts recent public contribution activity (last 3 months)"""
    three_months_ago = datetime.now() - timedelta(days=90)
    recent_events = [event for event in events_data if datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') > three_months_ago]

    commit_count = sum(1 for event in recent_events if event.get("type") == "PushEvent")
    pull_requests = sum(1 for event in recent_events if event.get("type") == "PullRequestEvent")
    issues = sum(1 for event in recent_events if event.get("type") == "IssuesEvent")

    return f"Commits: {commit_count}, PRs: {pull_requests}, Issues: {issues}"


def save_to_csv(data, filename):
    """Save the extracted data to a CSV file"""
    keys = [
        "Username", "Name", "Bio", "GitHub Profile", "Location", "Email",
        "Public Repos", "Followers", "Top Languages", "Top Repositories",
        "Recent Contributions", "Organizations", "Total Gists", "Starred Repositories", "Total Stars",
        "Forked Repositories", "Total Commits", "Total Pull Requests", "Total Issues", "Total Contributions"
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"📁 Data saved to {filename}")


if __name__ == "__main__":
    fetch_github_profiles()

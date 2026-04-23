import requests
import pandas as pd

class GitHubAnalyzer:
    def __init__(self, token=None):
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if token:
            self.headers['Authorization'] = f'token {token}'
        self.base_url = "https://api.github.com"

    def _make_request(self, url, params=None):
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 404:
            raise ValueError("Repository not found. Please check the 'owner/repo' format and ensure it exists.")
        elif response.status_code == 403 and 'rate limit' in response.text.lower():
            raise Exception("GitHub API rate limit exceeded. Please provide a Personal Access Token in the sidebar.")
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP Error occurred: {str(e)}")
            
        return response.json()

    def get_repo_metadata(self, owner_repo):
        url = f"{self.base_url}/repos/{owner_repo}"
        return self._make_request(url)

    def get_commits(self, owner_repo, limit=100):
        url = f"{self.base_url}/repos/{owner_repo}/commits"
        params = {'per_page': limit}
        return self._make_request(url, params)

    def get_open_issues(self, owner_repo, limit=10):
        url = f"{self.base_url}/repos/{owner_repo}/issues"
        # The GitHub API may return PRs as issues, we get slightly more to filter them and still yield 10
        params = {'state': 'open', 'per_page': limit * 2}
        issues_data = self._make_request(url, params)
        
        # Filter out pull requests
        real_issues = [issue for issue in issues_data if 'pull_request' not in issue]
        return real_issues[:limit]

    def process_commits(self, commits_data):
        if not commits_data:
            return pd.DataFrame()
            
        data = []
        for c in commits_data:
            commit = c.get('commit', {})
            author_info = commit.get('author', {})
            
            if not author_info:
                author_info = {}
                
            date_str = author_info.get('date')
            author_name = author_info.get('name', 'Unknown')
            
            data.append({
                'date': date_str,
                'author': author_name,
                'sha': c.get('sha')
            })
            
        df = pd.DataFrame(data)
        if not df.empty:
            # Convert raw JSON commit history to Pandas DataFrame with cleaned datetime objects
            df['date'] = pd.to_datetime(df['date'])
            df['date_only'] = df['date'].dt.date
        return df

    def calculate_commit_velocity(self, df):
        if df.empty:
            return pd.DataFrame()
        # Calculate 'Commit Velocity' (number of commits per day)
        velocity = df.groupby('date_only').size().reset_index(name='commits')
        return velocity

    def calculate_contributor_rankings(self, df):
        if df.empty:
            return pd.DataFrame()
        # Calculate 'Contributor Rankings'
        rankings = df['author'].value_counts().reset_index()
        rankings.columns = ['author', 'commits']
        return rankings

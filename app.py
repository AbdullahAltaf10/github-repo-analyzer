import streamlit as st
import pandas as pd
import plotly.express as px
from analyzer import GitHubAnalyzer

st.set_page_config(page_title="GitHub Repo Analyzer", page_icon="📊", layout="wide")

st.title("GitHub Repository Analyzer")

# Sidebar
st.sidebar.header("Configuration")
repo_url = st.sidebar.text_input("Repository URL or Path (e.g., 'owner/repo')", value="streamlit/streamlit")
token = st.sidebar.text_input("GitHub Personal Access Token (Optional)", type="password", help="Recommended to avoid API rate limits.")

analyze_btn = st.sidebar.button("Analyze Repository")

if analyze_btn and repo_url:
    # Handle the case where user pastes a full URL instead of just owner/repo
    if "github.com/" in repo_url:
        owner_repo = repo_url.split("github.com/")[-1].strip("/")
    else:
        owner_repo = repo_url.strip("/")
        
    analyzer = GitHubAnalyzer(token if token else None)
    
    with st.spinner(f"Fetching data for '{owner_repo}'..."):
        try:
            # Fetch metadata
            metadata = analyzer.get_repo_metadata(owner_repo)
            
            # Fetch commits
            commits_data = analyzer.get_commits(owner_repo, limit=100)
            
            # Fetch issues
            issues_data = analyzer.get_open_issues(owner_repo, limit=10)
            
            # --- Rendering UI ---
            st.subheader(f"Repository Overview: {metadata.get('full_name', owner_repo)}")
            
            # Metrics Cards
            col1, col2, col3 = st.columns(3)
            col1.metric("⭐ Stars", f"{metadata.get('stargazers_count', 0):,}")
            col2.metric("🍴 Forks", f"{metadata.get('forks_count', 0):,}")
            col3.metric("🐛 Open Issues", f"{metadata.get('open_issues_count', 0):,}")
            
            st.divider()
            
            # Process commits and plot charts
            df_commits = analyzer.process_commits(commits_data)
            
            if not df_commits.empty:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.subheader("Commit Frequency Over Time (Velocity)")
                    velocity_df = analyzer.calculate_commit_velocity(df_commits)
                    fig_line = px.line(
                        velocity_df, 
                        x='date_only', 
                        y='commits', 
                        markers=True, 
                        title='Commit Velocity (Last 100 Commits)',
                        labels={'date_only': 'Date', 'commits': 'Number of Commits'}
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                with col_chart2:
                    st.subheader("Top 5 Contributors")
                    rankings_df = analyzer.calculate_contributor_rankings(df_commits).head(5)
                    fig_bar = px.bar(
                        rankings_df, 
                        x='author', 
                        y='commits', 
                        title='Top 5 Contributors (Last 100 Commits)',
                        color='commits',
                        labels={'author': 'Contributor Name', 'commits': 'Commits'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No commits found for this repository.")
                
            st.divider()
            
            # Display Issues Table
            st.subheader("Recent 10 Open Issues")
            if issues_data:
                issues_list = []
                for issue in issues_data:
                    labels = ", ".join([label['name'] for label in issue.get('labels', [])])
                    issues_list.append({
                        "Number": issue.get('number'),
                        "Title": issue.get('title'),
                        "Created At": pd.to_datetime(issue.get('created_at')).strftime('%Y-%m-%d %H:%M:%S'),
                        "Labels": labels if labels else "None"
                    })
                issues_df = pd.DataFrame(issues_list)
                st.dataframe(issues_df, use_container_width=True, hide_index=True)
            else:
                st.info("No open issues found.")
                
        except ValueError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
elif analyze_btn:
    st.warning("Please enter a repository path or URL to analyze.")
else:
    st.info("👈 Enter a GitHub repository in the sidebar and click 'Analyze Repository'.")

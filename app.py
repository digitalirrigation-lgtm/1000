import streamlit as st
import pandas as pd
import requests
import base64
import io
from datetime import datetime, timedelta
import altair as alt
from bs4 import BeautifulSoup
import openpyxl

st.set_page_config(layout="wide", page_title="🎓 Scholarship Dashboard", page_icon="🎓")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton button { background: linear-gradient(145deg, #FFD700, #B8860B) !important; color: #1a1a2e !important; border-radius: 50px !important; font-weight: bold !important; }
    h1, h2, h3 { color: #1a1a2e !important; }
</style>
""", unsafe_allow_html=True)

def get_github_config():
    return {
        "token": st.secrets["github"]["token"],
        "username": "digitalirrigation-lgtm",
        "repo": "Scholarship-and-job-authomation",
        "file_path": "data/opportunities.xlsx",
        "branch": "main"
    }

def load_data_from_github():
    try:
        config = get_github_config()
        url = f"https://api.github.com/repos/{config['username']}/{config['repo']}/contents/{config['file_path']}"
        headers = {"Authorization": f"token {config['token']}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data["content"])
            df = pd.read_excel(io.BytesIO(content))
            return df, data["sha"]
        else:
            df = pd.DataFrame(columns=["Id", "Title", "Organization", "Category", "Deadline", "Status", "Link", "Description", "Country", "CreatedAt"])
            return df, None
    except:
        return pd.DataFrame(), None

def save_data_to_github(df, sha):
    try:
        config = get_github_config()
        content = io.BytesIO()
        df.to_excel(content, index=False, engine='openpyxl')
        encoded = base64.b64encode(content.getvalue()).decode()
        url = f"https://api.github.com/repos/{config['username']}/{config['repo']}/contents/{config['file_path']}"
        headers = {"Authorization": f"token {config['token']}"}
        payload = {"message": f"Update - {datetime.now()}", "content": encoded, "branch": config['branch']}
        if sha:
            payload["sha"] = sha
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return True, response.json().get('content', {}).get('sha', sha)
        return False, sha
    except:
        return False, sha

COUNTRIES = ["All", "Ethiopia", "USA", "UK", "Canada", "Australia", "Germany", "France", "India", "China", "Japan", "Brazil", "South Africa", "Kenya", "Nigeria", "Egypt", "Ghana"]

if "df" not in st.session_state:
    df, sha = load_data_from_github()
    st.session_state.df = df if not df.empty else pd.DataFrame(columns=["Id", "Title", "Organization", "Category", "Deadline", "Status", "Link", "Description", "Country", "CreatedAt"])
    st.session_state.sha = sha

def add_opportunity(data):
    df = st.session_state.df
    new_id = len(df) + 1 if not df.empty else 1
    new_row = pd.DataFrame([{"Id": new_id, "Title": data["title"], "Organization": data["organization"], "Category": data["category"], "Deadline": data["deadline"], "Status": "Not Applied", "Link": data.get("link", ""), "Description": data.get("description", ""), "Country": data.get("country", "All"), "CreatedAt": datetime.now().strftime("%Y-%m-%d %H:%M")}])
    df = pd.concat([df, new_row], ignore_index=True)
    success, new_sha = save_data_to_github(df, st.session_state.sha)
    if success:
        st.session_state.df = df
        st.session_state.sha = new_sha
        return True
    return False

def update_opportunity(opp_id, data):
    df = st.session_state.df
    idx = df[df["Id"] == opp_id].index
    if not idx.empty:
        for key, value in data.items():
            if key in df.columns:
                df.loc[idx, key] = value
        success, new_sha = save_data_to_github(df, st.session_state.sha)
        if success:
            st.session_state.df = df
            st.session_state.sha = new_sha
            return True
    return False

def delete_opportunity(opp_id):
    df = st.session_state.df
    df = df[df["Id"] != opp_id]
    success, new_sha = save_data_to_github(df, st.session_state.sha)
    if success:
        st.session_state.df = df
        st.session_state.sha = new_sha
        return True
    return False

with st.sidebar:
    st.markdown("## 🎯 Dashboard")
    df = st.session_state.df
    if not df.empty:
        st.markdown(f"**Total:** {len(df)}")
        st.markdown(f"**Applied:** {len(df[df['Status'] == 'Applied'])} ✅")
        st.markdown(f"**Pending:** {len(df[df['Status'] == 'Not Applied'])} ⏳")
    st.markdown("---")
    st.caption("⚡ Data stored on GitHub")

st.title("🎓 Scholarship & Job Dashboard")

col1, col2, col3, col4 = st.columns(4)
with col1:
    country_filter = st.selectbox("🌍 Country", COUNTRIES)
with col2:
    status_filter = st.selectbox("📌 Status", ["All", "Not Applied", "Applied"])
with col3:
    search_term = st.text_input("🔎 Search")
with col4:
    if st.button("🔄 Reset"):
        st.rerun()

df = st.session_state.df.copy()
if not df.empty:
    if country_filter != "All":
        df = df[df["Country"] == country_filter]
    if status_filter != "All":
        df = df[df["Status"] == status_filter]
    if search_term:
        df = df[df["Title"].str.contains(search_term, case=False, na=False)]

if not df.empty:
    st.dataframe(df[["Id", "Title", "Organization", "Deadline", "Status", "Country"]], use_container_width=True)
    
    selected_id = st.selectbox("Select opportunity:", df["Id"].tolist())
    if selected_id:
        row = df[df["Id"] == selected_id].iloc[0]
        with st.expander(f"📄 {row['Title']}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Organization:** {row['Organization']}")
                st.write(f"**Category:** {row['Category']}")
                st.write(f"**Country:** {row['Country']}")
                st.write(f"**Deadline:** {row['Deadline']}")
            with col2:
                st.write(f"**Status:** {row['Status']}")
                if row['Link']:
                    st.write(f"**Link:** [Click here]({row['Link']})")
            st.write(f"**Description:**")
            st.text_area("", row['Description'] if row['Description'] else "No description", height=100, key=f"desc_{selected_id}")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if row["Status"] != "Applied":
                    if st.button("✅ Mark Applied"):
                        if update_opportunity(selected_id, {"Status": "Applied"}):
                            st.success("Done!")
                            st.rerun()
            with c2:
                if st.button("🗑️ Delete"):
                    if delete_opportunity(selected_id):
                        st.success("Deleted!")
                        st.rerun()

st.markdown("---")
st.markdown("### ➕ Add New Opportunity")

with st.form("add_form"):
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Title *")
        organization = st.text_input("Organization *")
        category = st.selectbox("Category", ["Scholarship", "Job", "Fellowship", "Internship"])
    with col2:
        deadline = st.date_input("Deadline", value=datetime.today().date() + timedelta(days=30))
        country = st.selectbox("Country", COUNTRIES[1:])
        link = st.text_input("Link")
    description = st.text_area("Description", height=100)
    submitted = st.form_submit_button("➕ Add Opportunity")
    if submitted:
        if title and organization:
            if add_opportunity({"title": title, "organization": organization, "category": category, "deadline": deadline.strftime("%Y-%m-%d"), "country": country, "link": link, "description": description}):
                st.success("✅ Added!")
                st.rerun()
        else:
            st.error("❌ Title and Organization required!")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

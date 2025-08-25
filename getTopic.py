import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- Streamlit Title ---
st.title("🚀 YouTube Viral Topics Finder")

# --- API Key Input (Secure via st.secrets or user input) ---
API_KEY = st.text_input("Enter your YouTube API Key:", type="password")

# --- Config ---
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# --- User Inputs ---
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
custom_keywords = st.text_area(
    "Enter Keywords (comma separated):",
    "Affair Relationship Stories, Reddit Update, Reddit Relationship Advice, Open Marriage"
)
keywords = [kw.strip() for kw in custom_keywords.split(",") if kw.strip()]

sub_limit = st.number_input("Max Subscribers Filter:", min_value=0, max_value=100000, value=3000)
max_results = st.slider("Max Results per Keyword:", min_value=1, max_value=10, value=5)

# --- Fetch Button ---
if st.button("Fetch Data"):
    if not API_KEY:
        st.error("❌ Please enter your YouTube API Key first.")
    else:
        try:
            start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
            all_results = []

            progress = st.progress(0)
            for i, keyword in enumerate(keywords):
                st.write(f"🔍 Searching: **{keyword}**")

                search_params = {
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": start_date,
                    "maxResults": max_results,
                    "key": API_KEY,
                }

                response = requests.get(YOUTUBE_SEARCH_URL, params=search_params).json()

                if "error" in response:
                    st.error(f"API Error: {response['error']['message']}")
                    continue

                videos = response.get("items", [])
                if not videos:
                    st.warning(f"No videos found for keyword: {keyword}")
                    continue

                video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
                channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v and "channelId" in v["snippet"]]

                if not video_ids or not channel_ids:
                    continue

                # Video Stats
                stats = requests.get(YOUTUBE_VIDEO_URL, params={"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}).json().get("items", [])

                # Channel Stats
                channels = requests.get(YOUTUBE_CHANNEL_URL, params={"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}).json().get("items", [])

                for video, stat, channel in zip(videos, stats, channels):
                    title = video["snippet"].get("title", "N/A")
                    description = video["snippet"].get("description", "")[:200]
                    video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                    views = int(stat["statistics"].get("viewCount", 0))
                    subs = int(channel["statistics"].get("subscriberCount", 0))

                    if subs < sub_limit:
                        all_results.append({
                            "Keyword": keyword,
                            "Title": title,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Subscribers": subs
                        })

                progress.progress((i + 1) / len(keywords))

            # Display Results
            if all_results:
                df = pd.DataFrame(all_results).sort_values(by="Views", ascending=False)
                st.success(f"✅ Found {len(df)} results across {len(keywords)} keywords!")
                st.dataframe(df)

                # Download Option
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, "youtube_results.csv", "text/csv")
            else:
                st.warning("⚠️ No results found under given filters.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

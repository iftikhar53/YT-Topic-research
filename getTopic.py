import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Streamlit Title ---
st.set_page_config(page_title="YouTube Viral Topics Analyzer", layout="wide")
st.title("🚀 YouTube Viral Topics Analyzer Dashboard")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")

API_KEY = st.sidebar.text_input("Enter your YouTube API Key:", type="password")
days = st.sidebar.number_input("Search Last N Days:", min_value=1, max_value=30, value=7)
sub_limit = st.sidebar.number_input("Max Subscribers Filter:", min_value=0, max_value=100000, value=5000)
min_views = st.sidebar.number_input("Min Views Filter:", min_value=0, max_value=1000000, value=10000)
max_results = st.sidebar.slider("Results per Keyword:", 1, 10, 5)

custom_keywords = st.text_area(
    "Enter Keywords (comma separated):",
    "Reddit Relationship, Affair Stories, Cheating Story, Open Marriage"
)
keywords = [kw.strip() for kw in custom_keywords.split(",") if kw.strip()]

# --- API Endpoints ---
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# --- Fetch Button ---
if st.button("Fetch Viral Topics"):
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
                videos = response.get("items", [])
                if not videos:
                    continue

                video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
                channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v and "channelId" in v["snippet"]]

                stats = requests.get(YOUTUBE_VIDEO_URL, params={"part": "statistics,snippet,contentDetails", "id": ",".join(video_ids), "key": API_KEY}).json().get("items", [])
                channels = requests.get(YOUTUBE_CHANNEL_URL, params={"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}).json().get("items", [])

                for video, stat, channel in zip(videos, stats, channels):
                    snippet = stat.get("snippet", {})
                    statistics = stat.get("statistics", {})
                    channel_stats = channel.get("statistics", {})

                    title = snippet.get("title", "N/A")
                    description = snippet.get("description", "")[:200]
                    published = snippet.get("publishedAt", "N/A")
                    video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"

                    views = int(statistics.get("viewCount", 0))
                    likes = int(statistics.get("likeCount", 0)) if "likeCount" in statistics else 0
                    comments = int(statistics.get("commentCount", 0)) if "commentCount" in statistics else 0
                    subs = int(channel_stats.get("subscriberCount", 0))

                    if subs < sub_limit and views > min_views:
                        engagement = round(((likes + comments) / views) * 100, 2) if views > 0 else 0
                        all_results.append({
                            "Keyword": keyword,
                            "Title": title,
                            "Published": published,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Likes": likes,
                            "Comments": comments,
                            "Engagement %": engagement,
                            "Subscribers": subs
                        })

                progress.progress((i + 1) / len(keywords))

            if all_results:
                df = pd.DataFrame(all_results).sort_values(by="Views", ascending=False)
                st.success(f"✅ Found {len(df)} results across {len(keywords)} keywords!")
                st.dataframe(df)

                # --- Charts ---
                st.subheader("📊 Viral Insights")

                col1, col2 = st.columns(2)

                with col1:
                    top_videos = df.nlargest(10, "Views")
                    plt.figure(figsize=(8,5))
                    plt.barh(top_videos["Title"], top_videos["Views"])
                    plt.gca().invert_yaxis()
                    plt.title("Top 10 Videos by Views")
                    st.pyplot(plt)

                with col2:
                    plt.figure(figsize=(6,5))
                    plt.scatter(df["Subscribers"], df["Views"], s=df["Likes"]/10+10, alpha=0.6)
                    plt.xlabel("Subscribers")
                    plt.ylabel("Views")
                    plt.title("Views vs Subscribers (Bubble=Likes)")
                    st.pyplot(plt)

                # --- Downloads ---
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, "youtube_results.csv", "text/csv")

                excel = df.to_excel("youtube_results.xlsx", index=False)
                with open("youtube_results.xlsx", "rb") as f:
                    st.download_button("⬇️ Download Excel", f, "youtube_results.xlsx")

            else:
                st.warning("⚠️ No results found under given filters.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

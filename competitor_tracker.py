"""
competitor_tracker.py

Module to track competitor YouTube channels, fetch recent popular videos,
and analyze trend topics using YouTube Data API v3, YouTube RSS feeds, and Google Search.
"""

import re
import xml.etree.ElementTree as ET
import logging
import requests

class CompetitorTracker:
    def __init__(self, youtube_api_key: str = None):
        self.youtube_api_key = youtube_api_key

    def extract_channel_id(self, url_or_id: str) -> str:
        """Extracts channel ID or username/handle from input string/URL."""
        url_or_id = url_or_id.strip()
        # Direct channel ID UC...
        if re.match(r'^UC[\w-]{22}$', url_or_id):
            return url_or_id
        # Channel URL with UC...
        match = re.search(r'youtube\.com/channel/(UC[\w-]{22})', url_or_id)
        if match:
            return match.group(1)
        # Handle @username or custom url
        match = re.search(r'youtube\.com/@([\w.-]+)', url_or_id)
        if match:
            return match.group(1)
        if url_or_id.startswith('@'):
            return url_or_id[1:]
        return url_or_id

    def fetch_channel_videos_rss(self, channel_id: str) -> list:
        """Fetches recent videos from YouTube RSS feed for a channel ID."""
        if not channel_id.startswith("UC"):
            # If handle or username, RSS feed requires channel ID or resolved handle
            # Try searching or resolving via scrape
            resolved_id = self.resolve_handle_to_channel_id(channel_id)
            if resolved_id:
                channel_id = resolved_id
            else:
                return []

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        videos = []
        try:
            resp = requests.get(rss_url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                channel_title = root.find('atom:title', ns)
                ch_name = channel_title.text if channel_title is not None else "Competitor"

                for entry in root.findall('atom:entry', ns):
                    title_elem = entry.find('atom:title', ns)
                    link_elem = entry.find('atom:link', ns)
                    published_elem = entry.find('atom:published', ns)

                    title = title_elem.text if title_elem is not None else ""
                    link = link_elem.attrib.get('href', '') if link_elem is not None else ""
                    pub_date = published_elem.text if published_elem is not None else ""

                    videos.append({
                        'channel': ch_name,
                        'title': title,
                        'link': link,
                        'published': pub_date
                    })
        except Exception as e:
            logging.error(f"Error fetching RSS for channel {channel_id}: {e}")
        return videos

    def resolve_handle_to_channel_id(self, handle: str) -> str:
        """Attempts to resolve a YouTube @handle to a channel ID UC..."""
        clean_handle = handle.lstrip('@')
        try:
            url = f"https://www.youtube.com/@{clean_handle}"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if resp.status_code == 200:
                match = re.search(r'="https://www\.youtube\.com/channel/(UC[\w-]{22})"', resp.text)
                if match:
                    return match.group(1)
                match = re.search(r'"channelId":"(UC[\w-]{22})"', resp.text)
                if match:
                    return match.group(1)
        except Exception as e:
            logging.error(f"Error resolving handle @{clean_handle}: {e}")
        return ""

    def fetch_channel_videos_api(self, channel_id: str) -> list:
        """Fetches videos using YouTube Data API v3 if API key is provided."""
        if not self.youtube_api_key:
            return []

        videos = []
        try:
            # If channel_id is handle or name, resolve via search or channels API
            if not channel_id.startswith("UC"):
                search_url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    'key': self.youtube_api_key,
                    'q': channel_id,
                    'type': 'channel',
                    'part': 'snippet',
                    'maxResults': 1
                }
                res = requests.get(search_url, params=params, timeout=10).json()
                items = res.get('items', [])
                if items:
                    channel_id = items[0]['id']['channelId']
                else:
                    return []

            # Fetch channel's uploaded playlist ID or recent videos
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'key': self.youtube_api_key,
                'channelId': channel_id,
                'part': 'snippet',
                'order': 'viewCount', # Get top viewed recent videos
                'maxResults': 10,
                'type': 'video'
            }
            res = requests.get(url, params=params, timeout=10).json()
            for item in res.get('items', []):
                snippet = item.get('snippet', {})
                videos.append({
                    'channel': snippet.get('channelTitle', ''),
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'link': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'published': snippet.get('publishedAt', '')
                })
        except Exception as e:
            logging.error(f"Error calling YouTube Data API for {channel_id}: {e}")
        return videos

    def get_competitor_summary(self, channel_inputs: list) -> str:
        """Fetches videos for a list of channel URLs/IDs and builds a text summary for LLM analysis."""
        all_videos = []
        for inp in channel_inputs:
            if not inp.strip():
                continue
            chid = self.extract_channel_id(inp)
            vids = []
            if self.youtube_api_key:
                vids = self.fetch_channel_videos_api(chid)
            if not vids:
                vids = self.fetch_channel_videos_rss(chid)
            all_videos.extend(vids)

        if not all_videos:
            return "No recent competitor video data found. Relying on general niche trends."

        summary_lines = ["Recent Top Competitor Videos:"]
        for idx, v in enumerate(all_videos[:15]):
            summary_lines.append(f"{idx+1}. [{v.get('channel')}] '{v.get('title')}' (Published: {v.get('published')})")
            if v.get('description'):
                summary_lines.append(f"   Summary: {v.get('description')[:150]}...")

        return "\n".join(summary_lines)

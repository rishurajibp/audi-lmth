import os
import requests
import hashlib
import secrets
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import asyncio
import pytz
from pymongo import MongoClient

# ===== CONFIGURATION =====
API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "8013725761:AAHWr33qmoOgzWn_-7HS1g85KrZo8bNdxUM"
DEFAULT_THUMBNAIL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
SECRET_KEY = "hgygjugxchjhn"
CHANNEL_ID = "@kuvnypkyjk"
ADMIN_IDS = [1147534909, 6669182897, 5957208798]
OWNER_ID = ADMIN_IDS[0]  # First admin is owner

# MongoDB setup (replace with your connection string)
MONGO_URI = "mongodb://localhost:27017"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["secure_html_bot"]
users_col = db["users"]

app = Client("secure_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Utility functions
def generate_user_token(user_id):
    return hashlib.sha256(f"{user_id}{SECRET_KEY}".encode()).hexdigest()

def generate_access_code():
    return f"ER.BABU{{{''.join(secrets.choice('0123456789') for _ in range(6)}}}"

def format_phone_number(phone):
    return f"📞 {phone[:4]}****{phone[-3:]}" if phone else "🚫 Hidden"

async def get_user_details(client, user):
    try:
        full_user = await client.get_users(user.id)
    except Exception:
        full_user = user
    
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "🚫 None"
    details = [
        ("🆔 User ID", str(user.id)),
        ("👤 Username", f"@{user.username}" if user.username else "🚫 None"),
        ("📛 Full Name", full_name),
        ("🤖 Bot Account", "✅ Yes" if user.is_bot else "❌ No"),
        ("🌐 Language", user.language_code or "🚫 Unknown"),
        ("💎 Premium", "✨ Yes" if user.is_premium else "❌ No"),
        ("🔐 Restricted", "🔒 Yes" if user.is_restricted else "🔓 No"),
        ("✅ Verified", "☑️ Yes" if user.is_verified else "❌ No"),
        ("⚠️ Scam", "🚨 Yes" if user.is_scam else "✅ No"),
        ("🚫 Fake", "❌ Yes" if user.is_fake else "✅ No"),
        ("📅 Account Created", datetime.fromtimestamp(user.date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'date') else "🚫 Unknown"),
        ("📞 Phone Number", format_phone_number(getattr(full_user, 'phone_number', None))),
        ("🖼️ Profile Photo", "🖼️ Yes" if user.photo else "🚫 No"),
        ("📝 Bio", getattr(full_user, 'bio', "🚫 None")),
        ("📱 Last Seen", datetime.fromtimestamp(full_user.last_online_date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(full_user, 'last_online_date') else "🚫 Hidden"),
        ("🎂 Birthday", str(full_user.birthday) if hasattr(full_user, 'birthday') else "🚫 Not set"),
        ("🌍 Data Center", f"DC {full_user.dc_id}" if hasattr(full_user, 'dc_id') else "🚫 Unknown"),
    ]
    return details, full_user if hasattr(full_user, 'photo') else None

def extract_names_and_urls(file_content):
    return [(name.strip(), url.strip()) for line in file_content.strip().split("\n") if ":" in line for name, url in [line.split(":", 1)]]

def categorize_urls(urls):
    videos, pdfs, others = [], [], []
    
    for name, url in urls:
        if "classplusapp" in url:
            clean_url = url.split("://")[-1] if "://" in url else url
            videos.append((name, f"https://api.extractor.workers.dev/player?url={clean_url}"))
        elif ".zip" in url:
            videos.append((name, f"https://video.pablocoder.eu.org/appx-zip?url={url}"))
        elif "dragoapi.vercel" in url or "/master.mpd" in url:
            vid_id = url.split("/")[-2] if "/master.mpd" in url else None
            new_url = f"https://player.muftukmall.site/?id={vid_id}" if vid_id else url
            videos.append((name, new_url))
        elif any(x in url.lower() for x in ["youtube.com/embed", "youtu.be", "youtube.com/watch"]):
            videos.append((name, url))
        elif any(ext in url.lower() for ext in [".m3u8", ".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".flv", ".mpeg", ".mpd"]):
            videos.append((name, url))
        elif "pdf*" in url:
            pdfs.append((name, f"https://dragoapi.vercel.app/pdf/{url}"))
        elif "pdf" in url:
            pdfs.append((name, url))
        else:
            others.append((name, url))

    return videos, pdfs, others

def get_mime_type(url):
    ext_map = {
        ".m3u8": "application/x-mpegURL",
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".wmv": "video/x-ms-wmv",
        ".flv": "video/x-flv",
        ".mpeg": "video/mpeg",
        ".mpd": "application/dash+xml"
    }
    return next((v for k, v in ext_map.items() if k in url.lower()), "video/mp4")

def generate_html(file_name, videos, pdfs, others, user_id=None, access_code=None, user_details=None, profile_photo_url=None, is_admin=False):
    base_name = os.path.splitext(file_name)[0]
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    formatted_datetime = f"📅 {current_time.strftime('%d %B, %Y')} | ⏰ {current_time.strftime('%I:%M:%S %p')}"
    
    profile_photo_html = f"""
    <div class="profile-photo-container">
        <img src="{profile_photo_url or DEFAULT_THUMBNAIL}" alt="Profile Photo" class="profile-photo">
    </div>
    """ if profile_photo_url or DEFAULT_THUMBNAIL else ""

    if is_admin:
        user_details = [
            ("👤 Uploader", "🔓 Admin (Unrestricted Access)"),
            ("🔐 Security", "🛡️ No authentication required")
        ]
    elif not user_details:
        user_details = [
            ("👤 Uploader", "🚫 Unknown"),
            ("🔐 Security", "🔒 Authentication required")
        ]

    details_html = "\n".join(
        f'<div class="detail-item"><span class="detail-label">{label}</span> <span class="detail-value">{value}</span></div>'
        for label, value in user_details
    )
    
    video_links = "".join(f'<a href="#" onclick="playVideo(\'{url}\')">{name}</a>' for name, url in videos)
    pdf_links = "".join(f'<a href="{url}" target="_blank">{name}</a> <a href="{url}" download>📥 Download PDF</a>' for name, url in pdfs)
    other_links = "".join(f'<a href="{url}" target="_blank">{name}</a>' for name, url in others)

    auth_js = f"""
    const REQUIRED_USER_ID = "{user_id}";
    const ACCESS_CODE = "{access_code}";
    function checkAuth() {{
        const authData = localStorage.getItem('authData');
        if (authData) {{
            try {{
                const {{ userId, code }} = JSON.parse(authData);
                if (userId === REQUIRED_USER_ID && code === ACCESS_CODE) {{
                    document.getElementById('authModal').style.display = 'none';
                    document.getElementById('mainContent').style.display = 'block';
                    return true;
                }}
            }} catch (e) {{ console.error('Error parsing auth data:', e); }}
        }}
        return false;
    }}
    function verifyAccess() {{
        const userId = document.getElementById('userIdInput').value;
        const code = document.getElementById('accessCodeInput').value;
        if (userId === REQUIRED_USER_ID && code === ACCESS_CODE) {{
            localStorage.setItem('authData', JSON.stringify({{ userId: REQUIRED_USER_ID, code: ACCESS_CODE }}));
            document.getElementById('authModal').style.display = 'none';
            document.getElementById('mainContent').style.display = 'block';
            document.getElementById('errorMessage').style.display = 'none';
        }} else {{
            document.getElementById('errorMessage').style.display = 'block';
        }}
    }}
    if (!checkAuth()) document.getElementById('authModal').style.display = 'flex';
    """ if not is_admin and user_id and access_code else """
    document.getElementById('authModal').style.display = 'none';
    document.getElementById('mainContent').style.display = 'block';
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }}
        body {{ background: #f5f7fa; text-align: center; }}
        .auth-modal {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 1000; }}
        .auth-content {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; width: 90%; box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-align: center; }}
        .auth-content h1 {{ color: #007bff; margin-bottom: 10px; font-size: 28px; font-weight: bold; background: linear-gradient(90deg, #007bff, #6610f2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .auth-content h2 {{ color: #ff416c; margin-bottom: 20px; font-size: 22px; }}
        .auth-content input {{ width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #007bff; border-radius: 5px; font-size: 16px; }}
        .auth-content button {{ width: 100%; padding: 12px; background: linear-gradient(90deg, #007bff, #6610f2); color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 10px; transition: all 0.3s; }}
        .auth-content button:hover {{ background: linear-gradient(90deg, #0069d9, #5a0bd6); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .error-message {{ color: #ff416c; margin-top: 10px; display: none; text-align: center; font-weight: bold; }}
        .profile-photo-container {{ position: absolute; top: 20px; right: 20px; width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 3px solid #007bff; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .profile-photo {{ width: 100%; height: 100%; object-fit: cover; }}
        .user-details-modal {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: none; justify-content: center; align-items: center; z-index: 1001; }}
        .user-details-content {{ background: white; padding: 25px; border-radius: 10px; max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto; box-shadow: 0 5px 20px rgba(0,0,0,0.3); }}
        .user-details-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee; }}
        .user-details-header h3 {{ color: #007bff; margin: 0; }}
        .close-btn {{ background: #ff416c; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
        .detail-item {{ margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 8px; display: flex; justify-content: space-between; }}
        .detail-label {{ font-weight: bold; color: #007bff; }}
        .detail-value {{ color: #333; text-align: right; max-width: 60%; word-break: break-word; }}
        .header {{ background: linear-gradient(90deg, #007bff, #6610f2); color: white; padding: 15px; font-size: 24px; font-weight: bold; }}
        .subheading {{ font-size: 18px; margin-top: 10px; color: #555; font-weight: bold; }}
        .subheading a {{ background: linear-gradient(90deg, #ff416c, #ff4b2b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-decoration: none; font-weight: bold; }}
        .container {{ display: flex; justify-content: space-around; margin: 30px auto; width: 80%; }}
        .tab {{ flex: 1; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; transition: 0.3s; border-radius: 10px; font-size: 20px; font-weight: bold; }}
        .tab:hover {{ background: #007bff; color: white; }}
        .content {{ display: none; margin-top: 20px; }}
        .content.active {{ display: block; }}
        .footer {{ margin-top: 30px; font-size: 18px; font-weight: bold; padding: 15px; background: #1c1c1c; color: white; border-radius: 10px; }}
        .footer a {{ color: #ffeb3b; text-decoration: none; font-weight: bold; }}
        .video-list, .pdf-list, .other-list {{ text-align: left; max-width: 600px; margin: auto; }}
        .video-list a, .pdf-list a, .other-list a {{ display: block; padding: 10px; background: #fff; margin: 5px 0; border-radius: 5px; text-decoration: none; color: #007bff; font-weight: bold; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }}
        .video-list a:hover, .pdf-list a:hover, .other-list a:hover {{ background: #007bff; color: white; }}
        .search-bar {{ margin: 20px auto; width: 80%; max-width: 600px; }}
        .search-bar input {{ width: 100%; padding: 10px; border: 2px solid #007bff; border-radius: 5px; font-size: 16px; }}
        .no-results {{ color: red; font-weight: bold; margin-top: 20px; display: none; }}
        #video-player {{ display: none; margin: 20px auto; width: 80%; max-width: 800px; }}
        #youtube-player {{ display: none; margin: 20px auto; width: 80%; max-width: 800px; }}
        .download-button {{ margin-top: 10px; text-align: center; }}
        .download-button a {{ background: #007bff; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; }}
        .download-button a:hover {{ background: #0056b3; }}
        .datetime {{ margin-top: 10px; font-size: 18px; font-weight: bold; color: #2F4F4F; }}
        .user-details-btn {{
            background: linear-gradient(90deg, #007bff, #6610f2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin: 20px auto;
            display: block;
            width: fit-content;
        }}
    </style>
</head>
<body>
    <div id="authModal" class="auth-modal">
        <div class="auth-content">
            <h1>Welcome to 𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚</h1>
            <h2>🔒 Secure Content Access</h2>
            <input type="text" id="userIdInput" placeholder="Your User ID">
            <input type="text" id="accessCodeInput" placeholder="Access Code (ER.BABU{...})">
            <button onclick="verifyAccess()">Verify</button>
            <p id="errorMessage" class="error-message">Invalid credentials</p>
        </div>
    </div>

    <div id="userDetailsModal" class="user-details-modal">
        <div class="user-details-content">
            <div class="user-details-header">
                <h3>👤 User Information</h3>
                <button class="close-btn" onclick="closeUserDetails()">×</button>
            </div>
            {details_html}
        </div>
    </div>

    <div id="mainContent" style="display: none;">
        {profile_photo_html}
        <div class="header">{base_name}</div>
        <div class="subheading">📥 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div><br>
        <div class="datetime" id="datetime">{formatted_datetime}</div><br>
        <p>🔹𝐔𝐬𝐞 𝐓𝐡𝐢𝐬 𝐁𝐨𝐭 𝐟𝐨𝐫 𝐓𝐗𝐓 𝐭𝐨 𝐇𝐓𝐌𝐋 𝐟𝐢𝐥𝐞 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 : <a href="https://t.me/htmldeveloperbot" target="_blank"> @𝐡𝐭𝐦𝐥𝐝𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫𝐛𝐨𝐭 </a></p>

        <button class="user-details-btn" onclick="showUserDetails()">
            <i class="fas fa-user-circle"></i> View User Details
        </button>

        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search for videos, PDFs, or other resources..." oninput="filterContent()">
        </div>

        <div id="noResults" class="no-results">No results found.</div>

        <div id="video-player">
            <video id="engineer-babu-player" class="video-js vjs-default-skin" controls preload="auto" width="640" height="360">
                <p class="vjs-no-js">
                    To view this video please enable JavaScript, and consider upgrading to a web browser that
                    <a href="https://videojs.com/html5-video-support/" target="_blank">supports HTML5 video</a>
                </p>
            </video>
            <div class="download-button">
                <a id="download-link" href="#" download>Download Video</a>
            </div>
            <div style="text-align: center; margin-top: 10px; font-weight: bold; color: #007bff;">Engineer Babu Player</div>
        </div>

        <div id="youtube-player">
            <div id="player"></div>
            <div style="text-align: center; margin-top: 10px; font-weight: bold; color: #007bff;">Engineer Babu Player</div>
        </div>

        <div class="container">
            <div class="tab" onclick="showContent('videos')">Videos</div>
            <div class="tab" onclick="showContent('pdfs')">PDFs</div>
            <div class="tab" onclick="showContent('others')">Others</div>
        </div>

        <div id="videos" class="content active">
            <h2>All Video Lectures</h2>
            <div class="video-list">
                {video_links}
            </div>
        </div>

        <div id="pdfs" class="content">
            <h2>All PDFs</h2>
            <div class="pdf-list">
                {pdf_links}
            </div>
        </div>

        <div id="others" class="content">
            <h2>Other Resources</h2>
            <div class="other-list">
                {other_links}
            </div>
        </div>

        <div class="footer">Extracted By - <a href="https://t.me/Engineers_Babu" target="_blank">Engineer Babu</a></div>
    </div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        {auth_js}
        
        function showUserDetails() {{
            document.getElementById('userDetailsModal').style.display = 'flex';
        }}
        
        function closeUserDetails() {{
            document.getElementById('userDetailsModal').style.display = 'none';
        }}
        
        window.onclick = function(event) {{
            if (event.target == document.getElementById('userDetailsModal')) {{
                closeUserDetails();
            }}
        }};
        
        const player = videojs('engineer-babu-player', {{
            controls: true,
            autoplay: true,
            preload: 'auto',
            fluid: true,
        }});

        let youtubePlayer;

        function onYouTubeIframeAPIReady() {{
            youtubePlayer = new YT.Player('player', {{
                height: '360',
                width: '640',
                events: {{
                    'onReady': onPlayerReady,
                }}
            }});
        }}

        function onPlayerReady(event) {{
            // You can add additional functionality here if needed
        }}

        function playVideo(url) {{
            if (
                url.includes('.m3u8') ||
                url.includes('.mp4') ||
                url.includes('.mkv') ||
                url.includes('.webm') ||
                url.includes('.MP4') ||
                url.includes('.AVI') ||
                url.includes('.MOV') ||
                url.includes('.WMV') ||
                url.includes('.MKV') ||
                url.includes('.FLV') ||
                url.includes('.MPEG') ||
                url.includes('.mpd')
            ) {{
                document.getElementById('video-player').style.display = 'block';
                document.getElementById('youtube-player').style.display = 'none';
                const mimeType = getMimeType(url);
                player.src({{ src: url, type: mimeType }});
                player.play().catch(() => {{
                    window.open(url, '_blank');
                }});
                document.getElementById('download-link').href = url;
            }} else if (url.includes('youtube.com') || url.includes('youtu.be')) {{
                document.getElementById('video-player').style.display = 'none';
                document.getElementById('youtube-player').style.display = 'block';
                youtubePlayer.loadVideoByUrl(url);
            }} else {{
                window.open(url, '_blank');
            }}
        }}

        function getMimeType(url) {{
            if (url.includes('.m3u8')) {{
                return 'application/x-mpegURL';
            }} else if (url.includes('.mp4')) {{
                return 'video/mp4';
            }} else if (url.includes('.mkv')) {{
                return 'video/x-matroska';
            }} else if (url.includes('.webm')) {{
                return 'video/webm';
            }} else if (url.includes('.avi')) {{
                return 'video/x-msvideo';
            }} else if (url.includes('.mov')) {{
                return 'video/quicktime';
            }} else if (url.includes('.wmv')) {{
                return 'video/x-ms-wmv';
            }} else if (url.includes('.flv')) {{
                return 'video/x-flv';
            }} else if (url.includes('.mpeg')) {{
                return 'video/mpeg';
            }} else if (url.includes('.mpd')) {{
                return 'application/dash+xml';
            }} else {{
                return 'video/mp4';
            }}
        }}

        function showContent(tabName) {{
            const contents = document.querySelectorAll('.content');
            contents.forEach(content => {{
                content.classList.remove('active');
                content.style.display = 'none';
            }});
            const selectedContent = document.getElementById(tabName);
            if (selectedContent) {{
                selectedContent.classList.add('active');
                selectedContent.style.display = 'block';
            }}
            filterContent();
        }}

        function filterContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const activeTab = document.querySelector('.content.active') || document.getElementById('videos');
            const activeTabId = activeTab.id;
            let hasResults = false;

            let items;
            if (activeTabId === 'videos') {{
                items = document.querySelectorAll('#videos .video-list a');
            }} else if (activeTabId === 'pdfs') {{
                items = document.querySelectorAll('#pdfs .pdf-list a');
            }} else if (activeTabId === 'others') {{
                items = document.querySelectorAll('#others .other-list a');
            }}

            if (items) {{
                items.forEach(item => {{
                    let itemText;
                    if (activeTabId === 'videos') {{
                        itemText = item.textContent.toLowerCase();
                    }} else if (activeTabId === 'pdfs') {{
                        itemText = item.textContent.split('📥')[0].toLowerCase().trim();
                    }} else {{
                        itemText = item.textContent.toLowerCase();
                    }}

                    if (itemText.includes(searchTerm)) {{
                        item.style.display = 'block';
                        hasResults = true;
                    }} else {{
                        item.style.display = 'none';
                    }}
                }});
            }}

            const noResultsMessage = document.getElementById('noResults');
            if (noResultsMessage) {{
                noResultsMessage.style.display = hasResults ? 'none' : 'block';
            }}
        }}

        function updateDateTime() {{
            const now = new Date();
            const options = {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }};
            const formattedDateTime = now.toLocaleDateString('en-US', options);
            document.getElementById('datetime').innerText = `📅 ${{formattedDateTime}}`;
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            showContent('videos');
            setInterval(updateDateTime, 1000);
        }});
    </script>
</body>
</html>"""

# Telegram handlers
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    user = message.from_user
    users_col.update_one({"_id": user.id}, {"$set": {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "date": datetime.now()
    }}, upsert=True)
    
    await message.reply_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

@app.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats(client: Client, message: Message):
    total = users_col.count_documents({})
    await message.reply_text(f"📊 Total users: {total}")

@app.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
async def broadcast(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast <message>")
        return

    text = message.text.split(None, 1)[1]
    total, sent, failed = 0, 0, 0
    await message.reply("📢 Broadcasting...")

    for user in users_col.find({}):
        user_id = user["_id"]
        total += 1
        try:
            await client.send_message(user_id, text)
            sent += 1
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)

    await message.reply(f"✅ Broadcast done.\nTotal: {total}\nSent: {sent}\nFailed: {failed}")

@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("Please upload a .txt file.")
        return

    user = message.from_user
    users_col.update_one({"_id": user.id}, {"$set": {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "last_activity": datetime.now()
    }}, upsert=True)

    user_id = user.id
    is_admin = user.id in ADMIN_IDS
    access_code = generate_access_code() if not is_admin else None
    
    user_details = None
    profile_photo_url = None
    
    if not is_admin:
        try:
            user_details, full_user = await get_user_details(client, user)
            if full_user and full_user.photo:
                photo_path = await client.download_media(full_user.photo.big_file_id)
                if photo_path:
                    profile_photo_url = DEFAULT_THUMBNAIL
                    os.remove(photo_path)
        except Exception as e:
            print(f"Error getting user details: {e}")
            user_details = [
                ("🆔 User ID", str(user.id)),
                ("👤 Username", f"@{user.username}" if user.username else "🚫 None"),
                ("📛 Full Name", f"{user.first_name or ''} {user.last_name or ''}".strip() or "🚫 None")
            ]
            profile_photo_url = None

    file_path = await message.download()
    file_name = message.document.file_name
    html_path = ""
    thumbnail_path = None
    
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            file_content = f.read()

        urls = extract_names_and_urls(file_content)
        videos, pdfs, others = categorize_urls(urls)

        html_content = generate_html(
            file_name, 
            videos, 
            pdfs, 
            others, 
            user_id if not is_admin else None, 
            access_code, 
            user_details, 
            profile_photo_url,
            is_admin=is_admin
        )
        
        html_path = file_path.replace(".txt", ".html")
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(html_content)

        # Download thumbnail
        try:
            thumbnail_response = requests.get(DEFAULT_THUMBNAIL, timeout=10)
            if thumbnail_response.status_code == 200:
                thumbnail_path = "thumbnail.jpg"
                with open(thumbnail_path, "wb") as f:
                    f.write(thumbnail_response.content)
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")
            thumbnail_path = None

        # Prepare caption
        if is_admin:
            caption = f"""🔓 Admin HTML File\n\n"""
            caption += f"📁 File: {file_name}\n"
            caption += f"👤 Uploader: Admin ({user.first_name or ''} {user.last_name or ''})\n"
            caption += f"🆔 User ID: <code>{user.id}</code>\n"
            caption += "🔓 This file has unrestricted access\n\n"
            caption += "⚠️ Note: This file was uploaded by an admin and doesn't require authentication"
        else:
            caption = f"""🔐 Secure HTML File\n\n"""
            caption += f"👤 User: {user.first_name or ''} {user.last_name or ''}\n"
            caption += f"🆔 ID: <code>{user.id}</code>\n"
            if user.username:
                caption += f"👤 Username: @{user.username}\n"
            caption += f"🔑 Access Code: <code>{access_code}</code>\n\n"
            caption += "⚠️ Important:\n"
            caption += "• This file is secured to your User ID\n"
            caption += "• The access code is required to view content\n"
            caption += "• Do NOT share this file with others"

        # Send to user with thumbnail
        await message.reply_document(
            document=html_path,
            file_name=f"{os.path.splitext(file_name)[0]}.html",
            caption=caption,
            thumb=thumbnail_path if thumbnail_path else None
        )

        # Forward both files to channel
        channel_caption = f"""📁 File: {file_name}\n"""
        channel_caption += f"👤 User: {user.first_name or ''} {user.last_name or ''}\n"
        channel_caption += f"🆔 ID: <code>{user.id}</code>\n"
        if user.username:
            channel_caption += f"👤 Username: @{user.username}\n"
        if not is_admin:
            channel_caption += f"🔑 Access Code: <code>{access_code}</code>\n"
        channel_caption += f"🔐 {'Admin (Unrestricted)' if is_admin else 'User (Restricted)'}\n"
        channel_caption += f"📅 {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')}"

        await client.send_document(
            chat_id=CHANNEL_ID,
            document=file_path,
            file_name=file_name,
            caption=channel_caption
        )
        
        await client.send_document(
            chat_id=CHANNEL_ID,
            document=html_path,
            file_name=f"{os.path.splitext(file_name)[0]}.html",
            caption=channel_caption,
            thumb=thumbnail_path if thumbnail_path else None
        )

    except Exception as e:
        await message.reply_text(f"❌ Error processing file: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        if html_path and os.path.exists(html_path):
            os.remove(html_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

@app.on_callback_query(filters.regex("^help$"))
async def help_handler(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "📚 Help Guide\n\n"
        "1. Prepare a .txt file with content like:\n"
        "<code>Lecture 1:https://example.com/video1.mp4\n"
        "Notes:https://example.com/notes.pdf</code>\n\n"
        "2. Send the file to this bot\n"
        "3. You'll receive a secure HTML file\n"
        "4. To access content, you'll need:\n"
        "   - Your User ID\n"
        "   - The Access Code (ER.BABU{...})\n\n"
        "🔒 The file cannot be used by anyone else\n\n"
        "👑 Admin Features:\n"
        "- Files uploaded by admins don't require authentication\n"
        "- Use /broadcast (reply to a message) to send to all users",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]])
    )

@app.on_callback_query(filters.regex("^back$"))
async def back_handler(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{callback.from_user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

if __name__ == "__main__":
    print("✅ Secure HTML Bot is running...")
    app.run()

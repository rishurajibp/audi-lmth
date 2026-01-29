import os
import requests
import hashlib
import secrets
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import asyncio
import pytz
from pymongo import MongoClient
import random
from functools import wraps
import logging

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
API_ID = os.environ.get("API_ID", "21705536")
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7601635113:AAGbMk_SNWXrvsAk-KyEVd-y7c-xAR4bnIw")
DEFAULT_THUMBNAIL = os.environ.get("DEFAULT_THUMBNAIL", "https://i.postimg.cc/4N69wBLt/hat-hacker.webp")
SECRET_KEY = os.environ.get("SECRET_KEY", "hgygjugxchjhn")
CHANNEL_IDI = os.environ.get("CHANNEL_IDI", "@kuvnypkyjk")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@Engineers_babus")

# Parse admin IDs from environment variable or use defaults
admin_ids_str = os.environ.get("ADMIN_IDS", "7809571505,6669182897")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")]
OWNER_ID = ADMIN_IDS[0] if ADMIN_IDS else None

# MongoDB setup
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ===== DATABASE FUNCTIONS =====
def get_database():
    """Initialize and return MongoDB database connection"""
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client["secure_html_bot"]
        mongo_client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Return a dummy database for testing
        class DummyDB:
            def __getitem__(self, name):
                class DummyCollection:
                    def find_one(self, *args, **kwargs): return None
                    def update_one(self, *args, **kwargs): return None
                    def count_documents(self, *args, **kwargs): return 0
                    def find(self, *args, **kwargs): return []
                return DummyCollection()
        return DummyDB()

# Initialize database
db = get_database()
users_col = db["users"]

# ===== BOT CLIENT =====
app = Client(
    "secure_html_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=enums.ParseMode.HTML
)

# ===== UTILITY FUNCTIONS =====
def generate_user_token(user_id):
    """Generate a unique token for user authentication"""
    return hashlib.sha256(f"{user_id}{SECRET_KEY}".encode()).hexdigest()

def generate_access_code():
    """Generate a secure access code"""
    return f"ER.BABU{{{''.join(secrets.choice('0123456789') for _ in range(6))}}}"

def format_phone_number(phone):
    """Format phone number for privacy"""
    if phone and len(phone) > 7:
        return f"📞 {phone[:4]}****{phone[-3:]}"
    return "🚫 Hidden"

async def get_user_details(client, user):
    """Get detailed information about a user"""
    try:
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
        ]
        
        # Add additional details if available
        if hasattr(user, 'date'):
            details.append(("📅 Account Created", datetime.fromtimestamp(user.date).strftime('%Y-%m-%d %H:%M:%S')))
        else:
            details.append(("📅 Account Created", "🚫 Unknown"))
        
        phone_number = getattr(full_user, 'phone_number', None)
        details.append(("📞 Phone Number", format_phone_number(phone_number)))
        
        details.append(("🖼️ Profile Photo", "🖼️ Yes" if user.photo else "🚫 No"))
        
        bio = getattr(full_user, 'bio', "🚫 None")
        details.append(("📝 Bio", bio[:100] + "..." if len(bio) > 100 else bio))
        
        if hasattr(full_user, 'last_online_date'):
            details.append(("📱 Last Seen", datetime.fromtimestamp(full_user.last_online_date).strftime('%Y-%m-%d %H:%M:%S')))
        else:
            details.append(("📱 Last Seen", "🚫 Hidden"))
        
        birthday = getattr(full_user, 'birthday', None)
        details.append(("🎂 Birthday", str(birthday) if birthday else "🚫 Not set"))
        
        dc_id = getattr(full_user, 'dc_id', None)
        details.append(("🌍 Data Center", f"DC {dc_id}" if dc_id else "🚫 Unknown"))
        
        return details, full_user
        
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        # Return basic details if full details fail
        basic_details = [
            ("🆔 User ID", str(user.id)),
            ("👤 Username", f"@{user.username}" if user.username else "🚫 None"),
            ("📛 Full Name", f"{user.first_name or ''} {user.last_name or ''}".strip() or "🚫 None"),
        ]
        return basic_details, user

def extract_names_and_urls(file_content):
    """Extract name:url pairs from file content"""
    urls = []
    for line in file_content.strip().split("\n"):
        if ":" in line:
            try:
                name, url = line.split(":", 1)
                name = name.strip()
                url = url.strip()
                if name and url:
                    urls.append((name, url))
            except ValueError:
                continue
    return urls

def categorize_urls(urls):
    """Categorize URLs into videos, PDFs, and others"""
    videos, pdfs, others = [], [], []
    
    for name, url in urls:
        url_lower = url.lower()
        
        # Handle ClassPlus URLs
        if "classplusapp" in url_lower:
            clean_url = url.split("://")[-1] if "://" in url else url
            videos.append((name, f"https://ugxclassplusapi.vercel.app/get/cp/dl?url={clean_url}"))
        
        # Handle ZIP files
        elif ".zip" in url_lower:
            videos.append((name, f"https://video.pablocoder.eu.org/appx-zip?url={url}"))
        
        # Handle DragoAPI and MPD files
        elif "dragoapi.vercel" in url_lower or "/master.mpd" in url_lower:
            vid_id = url.split("/")[-2] if "/master.mpd" in url_lower else None
            new_url = f"https://player.muftukmall.site/?id={vid_id}" if vid_id else url
            videos.append((name, new_url))
        
        # Handle YouTube URLs
        elif any(x in url_lower for x in ["youtube.com/embed", "youtu.be", "youtube.com/watch"]):
            videos.append((name, url))
        
        # Handle video file extensions
        elif any(ext in url_lower for ext in [".m3u8", ".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".flv", ".mpeg", ".mpd"]):
            videos.append((name, url))
        
        # Handle PDFs
        elif "pdf*" in url_lower:
            pdfs.append((name, f"https://dragoapi.vercel.app/pdf/{url}"))
        elif ".pdf" in url_lower:
            pdfs.append((name, url))
        
        # Everything else
        else:
            others.append((name, url))
    
    return videos, pdfs, others

def get_mime_type(url):
    """Get MIME type based on URL extension"""
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
        ".mpd": "application/dash+xml",
        ".pdf": "application/pdf"
    }
    
    url_lower = url.lower()
    for ext, mime_type in ext_map.items():
        if ext in url_lower:
            return mime_type
    
    return "video/mp4"  # Default

def generate_html(file_name, videos, pdfs, others, user_id=None, access_code=None, user_details=None, profile_photo_url=None, is_admin=False):
    """Generate HTML content with authentication"""
    base_name = os.path.splitext(file_name)[0]
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    formatted_datetime = f"📅 {current_time.strftime('%d %B, %Y')} | ⏰ {current_time.strftime('%I:%M:%S %p')}"
    
    # Profile photo HTML
    profile_photo_html = ""
    if profile_photo_url or DEFAULT_THUMBNAIL:
        profile_photo_html = f"""
        <div class="profile-photo-container">
            <img src="{profile_photo_url or DEFAULT_THUMBNAIL}" alt="Profile Photo" class="profile-photo">
        </div>
        """
    
    # User details
    if is_admin:
        user_details_html = [
            ("👤 Uploader", "🔓 Admin (Unrestricted Access)"),
            ("🔐 Security", "🛡️ No authentication required")
        ]
    elif not user_details:
        user_details_html = [
            ("👤 Uploader", "🚫 Unknown"),
            ("🔐 Security", "🔒 Authentication required")
        ]
    else:
        user_details_html = user_details
    
    # Convert user details to HTML
    details_html = "\n".join(
        f'<div class="detail-item"><span class="detail-label">{label}</span> <span class="detail-value">{value}</span></div>'
        for label, value in user_details_html[:10]  # Limit to 10 details
    )
    
    # Generate links
    video_links = "".join(f'<a href="#" onclick="playVideo(\'{url}\')">{name}</a>' for name, url in videos)
    pdf_links = "".join(f'<a href="{url}" target="_blank">{name}</a> <a href="{url}" download>📥 Download PDF</a>' for name, url in pdfs)
    other_links = "".join(f'<a href="{url}" target="_blank">{name}</a>' for name, url in others)
    
    # Authentication JavaScript
    if not is_admin and user_id and access_code:
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
                }} catch (e) {{ 
                    console.error('Error parsing auth data:', e); 
                    localStorage.removeItem('authData');
                }}
            }}
            return false;
        }}
        
        function verifyAccess() {{
            const userId = document.getElementById('userIdInput').value.trim();
            const code = document.getElementById('accessCodeInput').value.trim();
            
            if (userId === REQUIRED_USER_ID && code === ACCESS_CODE) {{
                localStorage.setItem('authData', JSON.stringify({{ 
                    userId: REQUIRED_USER_ID, 
                    code: ACCESS_CODE,
                    timestamp: Date.now()
                }}));
                document.getElementById('authModal').style.display = 'none';
                document.getElementById('mainContent').style.display = 'block';
                document.getElementById('errorMessage').style.display = 'none';
            }} else {{
                document.getElementById('errorMessage').style.display = 'block';
                document.getElementById('errorMessage').textContent = 'Invalid User ID or Access Code';
            }}
        }}
        
        function clearAuth() {{
            localStorage.removeItem('authData');
            document.getElementById('authModal').style.display = 'flex';
            document.getElementById('mainContent').style.display = 'none';
        }}
        
        // Check authentication on page load
        if (!checkAuth()) {{
            document.getElementById('authModal').style.display = 'flex';
        }}
        """
    else:
        auth_js = """
        document.getElementById('authModal').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        
        function clearAuth() {
            alert('Admin files do not require authentication');
        }
        """
    
    # HTML template
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name} - Secure Content</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        /* CSS Styles - Compressed for brevity */
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .auth-modal {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); display: flex; justify-content: center; align-items: center; z-index: 1000; backdrop-filter: blur(10px); }}
        .auth-content {{ background: white; padding: 40px; border-radius: 20px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; animation: slideUp 0.5s ease; }}
        @keyframes slideUp {{ from {{ transform: translateY(50px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
        .auth-content h1 {{ background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; margin-bottom: 10px; }}
        .auth-content h2 {{ color: #ff6b6b; margin-bottom: 30px; font-size: 20px; }}
        .auth-content input {{ width: 100%; padding: 15px; margin: 12px 0; border: 2px solid #667eea; border-radius: 10px; font-size: 16px; transition: all 0.3s; }}
        .auth-content input:focus {{ border-color: #764ba2; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); outline: none; }}
        .auth-content button {{ width: 100%; padding: 15px; background: linear-gradient(90deg, #667eea, #764ba2); color: white; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 20px; transition: all 0.3s; }}
        .auth-content button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }}
        .error-message {{ color: #ff6b6b; margin-top: 15px; display: none; font-weight: bold; }}
        .profile-photo-container {{ position: fixed; top: 20px; right: 20px; width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 3px solid white; box-shadow: 0 5px 15px rgba(0,0,0,0.2); z-index: 100; }}
        .profile-photo {{ width: 100%; height: 100%; object-fit: cover; }}
        .main-container {{ background: white; border-radius: 20px; padding: 30px; margin-top: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.1); position: relative; }}
        .header {{ background: linear-gradient(90deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 15px; font-size: 28px; font-weight: bold; margin-bottom: 20px; text-align: center; }}
        .stats-container {{ display: flex; justify-content: space-around; margin: 20px 0; flex-wrap: wrap; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center; min-width: 120px; margin: 10px; flex: 1; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .tabs {{ display: flex; margin: 30px 0; border-bottom: 2px solid #eee; }}
        .tab {{ flex: 1; padding: 15px; text-align: center; cursor: pointer; font-weight: bold; color: #666; transition: all 0.3s; border-bottom: 3px solid transparent; }}
        .tab:hover {{ color: #667eea; }}
        .tab.active {{ color: #667eea; border-bottom-color: #667eea; }}
        .content-panel {{ display: none; padding: 20px; }}
        .content-panel.active {{ display: block; animation: fadeIn 0.5s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .link-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px; }}
        .link-card {{ background: #f8f9fa; padding: 15px; border-radius: 10px; transition: all 0.3s; border-left: 4px solid #667eea; }}
        .link-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); background: #e9ecef; }}
        .link-name {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
        .link-actions {{ display: flex; gap: 10px; margin-top: 10px; }}
        .btn {{ padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; transition: all 0.3s; }}
        .btn-primary {{ background: #667eea; color: white; }}
        .btn-primary:hover {{ background: #764ba2; }}
        .btn-secondary {{ background: #6c757d; color: white; }}
        .btn-secondary:hover {{ background: #545b62; }}
        .search-container {{ margin: 20px 0; position: relative; }}
        .search-input {{ width: 100%; padding: 15px 50px 15px 20px; border: 2px solid #667eea; border-radius: 10px; font-size: 16px; }}
        .search-icon {{ position: absolute; right: 20px; top: 50%; transform: translateY(-50%); color: #667eea; }}
        .player-container {{ margin: 20px 0; display: none; }}
        .footer {{ margin-top: 30px; text-align: center; color: #666; padding-top: 20px; border-top: 1px solid #eee; }}
        .auth-info {{ position: absolute; top: 20px; left: 20px; }}
        .logout-btn {{ background: #ff6b6b; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }}
        @media (max-width: 768px) {{
            .main-container {{ padding: 15px; }}
            .link-list {{ grid-template-columns: 1fr; }}
            .stats-container {{ flex-direction: column; }}
            .tabs {{ flex-direction: column; }}
            .profile-photo-container {{ width: 60px; height: 60px; }}
        }}
    </style>
</head>
<body>
    <!-- Authentication Modal -->
    <div id="authModal" class="auth-modal">
        <div class="auth-content">
            <h1>🔐 Secure Content Access</h1>
            <h2>Enter your credentials to continue</h2>
            <input type="text" id="userIdInput" placeholder="Your User ID" autocomplete="off">
            <input type="text" id="accessCodeInput" placeholder="Access Code (ER.BABU{...})" autocomplete="off">
            <button onclick="verifyAccess()">Verify & Access Content</button>
            <div id="errorMessage" class="error-message"></div>
            <p style="margin-top: 20px; color: #666; font-size: 14px;">
                Need help? Contact support for assistance.
            </p>
        </div>
    </div>

    <!-- Main Content -->
    <div id="mainContent" style="display: none;">
        {profile_photo_html}
        
        <div class="auth-info">
            <button class="logout-btn" onclick="clearAuth()">
                <i class="fas fa-sign-out-alt"></i> Logout
            </button>
        </div>
        
        <div class="main-container">
            <div class="header">
                <h1>{base_name}</h1>
                <p style="font-size: 16px; opacity: 0.9; margin-top: 10px;">
                    <i class="fas fa-shield-alt"></i> Secured Content • {formatted_datetime}
                </p>
            </div>
            
            <div class="stats-container">
                <div class="stat-card">
                    <div class="stat-number">{len(videos)}</div>
                    <div class="stat-label">Videos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(pdfs)}</div>
                    <div class="stat-label">PDFs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(others)}</div>
                    <div class="stat-label">Other Resources</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(videos) + len(pdfs) + len(others)}</div>
                    <div class="stat-label">Total Links</div>
                </div>
            </div>
            
            <div class="search-container">
                <input type="text" id="searchInput" class="search-input" placeholder="Search videos, PDFs, or resources...">
                <i class="fas fa-search search-icon"></i>
            </div>
            
            <div id="noResults" style="display: none; text-align: center; padding: 20px; color: #ff6b6b;">
                <i class="fas fa-search"></i> No results found
            </div>
            
            <div id="playerContainer" class="player-container">
                <video id="videoPlayer" class="video-js vjs-default-skin" controls preload="auto" width="100%" height="400">
                    <p class="vjs-no-js">
                        Your browser does not support HTML5 video.
                    </p>
                </video>
                <div style="text-align: center; margin-top: 10px;">
                    <a id="downloadBtn" href="#" class="btn btn-primary" download>
                        <i class="fas fa-download"></i> Download Video
                    </a>
                </div>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('videos')">
                    <i class="fas fa-video"></i> Videos ({len(videos)})
                </div>
                <div class="tab" onclick="showTab('pdfs')">
                    <i class="fas fa-file-pdf"></i> PDFs ({len(pdfs)})
                </div>
                <div class="tab" onclick="showTab('others')">
                    <i class="fas fa-link"></i> Others ({len(others)})
                </div>
            </div>
            
            <!-- Videos Tab -->
            <div id="videos" class="content-panel active">
                <div class="link-list" id="videoList">
                    {''.join(f'''
                    <div class="link-card">
                        <div class="link-name">
                            <i class="fas fa-play-circle"></i> {name}
                        </div>
                        <div class="link-actions">
                            <a href="#" class="btn btn-primary" onclick="playVideo('{url}')">
                                <i class="fas fa-play"></i> Play
                            </a>
                            <a href="{url}" class="btn btn-secondary" target="_blank">
                                <i class="fas fa-external-link-alt"></i> Open
                            </a>
                        </div>
                    </div>
                    ''' for name, url in videos)}
                </div>
            </div>
            
            <!-- PDFs Tab -->
            <div id="pdfs" class="content-panel">
                <div class="link-list" id="pdfList">
                    {''.join(f'''
                    <div class="link-card">
                        <div class="link-name">
                            <i class="fas fa-file-pdf"></i> {name}
                        </div>
                        <div class="link-actions">
                            <a href="{url}" class="btn btn-primary" target="_blank">
                                <i class="fas fa-eye"></i> View
                            </a>
                            <a href="{url}" class="btn btn-secondary" download>
                                <i class="fas fa-download"></i> Download
                            </a>
                        </div>
                    </div>
                    ''' for name, url in pdfs)}
                </div>
            </div>
            
            <!-- Others Tab -->
            <div id="others" class="content-panel">
                <div class="link-list" id="otherList">
                    {''.join(f'''
                    <div class="link-card">
                        <div class="link-name">
                            <i class="fas fa-link"></i> {name}
                        </div>
                        <a href="{url}" class="btn btn-primary" target="_blank">
                            <i class="fas fa-external-link-alt"></i> Open Link
                        </a>
                    </div>
                    ''' for name, url in others)}
                </div>
            </div>
            
            <div class="footer">
                <p>
                    <i class="fas fa-code"></i> Generated by Secure HTML Bot •
                    <i class="fas fa-user-shield"></i> Secured Access •
                    <i class="fas fa-clock"></i> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
                <p style="margin-top: 10px; font-size: 14px; color: #999;">
                    © {datetime.now().year} All rights reserved • Contact for support
                </p>
            </div>
        </div>
    </div>
    
    <!-- JavaScript Libraries -->
    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
    
    <script>
        // Authentication Script
        {auth_js}
        
        // Video Player
        const videoPlayer = videojs('videoPlayer', {{
            controls: true,
            autoplay: false,
            preload: 'auto',
            fluid: true,
            playbackRates: [0.5, 1, 1.5, 2],
            controlBar: {{
                children: [
                    'playToggle',
                    'volumePanel',
                    'currentTimeDisplay',
                    'timeDivider',
                    'durationDisplay',
                    'progressControl',
                    'remainingTimeDisplay',
                    'playbackRateMenuButton',
                    'fullscreenToggle'
                ]
            }}
        }});
        
        // YouTube Player
        let youtubePlayer;
        function onYouTubeIframeAPIReady() {{
            youtubePlayer = new YT.Player('youtubePlayer', {{
                height: '400',
                width: '100%',
                playerVars: {{
                    'autoplay': 0,
                    'controls': 1,
                    'rel': 0,
                    'modestbranding': 1
                }}
            }});
        }}
        
        // Tab Management
        function showTab(tabName) {{
            // Update tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.content-panel').forEach(panel => {{
                panel.classList.remove('active');
                panel.style.display = 'none';
            }});
            
            // Activate selected tab
            document.querySelector(`.tab[onclick*="${{tabName}}"]`).classList.add('active');
            document.getElementById(tabName).classList.add('active');
            document.getElementById(tabName).style.display = 'block';
            
            // Apply search filter
            filterContent();
        }}
        
        // Video Playback
        function playVideo(url) {{
            document.getElementById('playerContainer').style.display = 'block';
            document.getElementById('playerContainer').scrollIntoView({{ behavior: 'smooth' }});
            
            if (url.includes('youtube.com') || url.includes('youtu.be')) {{
                // YouTube video
                if (!document.getElementById('youtubePlayer')) {{
                    const playerDiv = document.createElement('div');
                    playerDiv.id = 'youtubePlayer';
                    document.getElementById('playerContainer').insertBefore(playerDiv, document.getElementById('downloadBtn').parentNode);
                    
                    // Reinitialize YouTube player
                    if (typeof YT !== 'undefined') {{
                        youtubePlayer = new YT.Player('youtubePlayer', {{
                            height: '400',
                            width: '100%',
                            videoId: extractYouTubeId(url),
                            playerVars: {{
                                'autoplay': 1,
                                'controls': 1
                            }}
                        }});
                    }}
                }} else {{
                    youtubePlayer.loadVideoById(extractYouTubeId(url));
                }}
                videoPlayer.style.display = 'none';
                document.getElementById('youtubePlayer').style.display = 'block';
                document.getElementById('downloadBtn').style.display = 'none';
            }} else {{
                // Regular video
                if (document.getElementById('youtubePlayer')) {{
                    document.getElementById('youtubePlayer').style.display = 'none';
                }}
                videoPlayer.style.display = 'block';
                videoPlayer.src({{ src: url, type: getMimeType(url) }});
                document.getElementById('downloadBtn').href = url;
                document.getElementById('downloadBtn').style.display = 'block';
                videoPlayer.play();
            }}
        }}
        
        function extractYouTubeId(url) {{
            const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
            const match = url.match(regExp);
            return (match && match[7].length === 11) ? match[7] : null;
        }}
        
        function getMimeType(url) {{
            const mimeTypes = {{
                '.m3u8': 'application/x-mpegURL',
                '.mp4': 'video/mp4',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.wmv': 'video/x-ms-wmv',
                '.flv': 'video/x-flv',
                '.mpeg': 'video/mpeg',
                '.mpd': 'application/dash+xml'
            }};
            
            for (const [ext, mimeType] of Object.entries(mimeTypes)) {{
                if (url.toLowerCase().includes(ext)) {{
                    return mimeType;
                }}
            }}
            
            return 'video/mp4';
        }}
        
        // Search Functionality
        function filterContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
            const activeTab = document.querySelector('.content-panel.active').id;
            let hasResults = false;
            
            // Get all items in active tab
            const items = document.querySelectorAll(`#${{activeTab}} .link-card`);
            
            items.forEach(item => {{
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    item.style.display = 'block';
                    hasResults = true;
                }} else {{
                    item.style.display = 'none';
                }}
            }});
            
            // Show/hide no results message
            document.getElementById('noResults').style.display = hasResults ? 'none' : 'block';
        }}
        
        // Event Listeners
        document.getElementById('searchInput').addEventListener('input', filterContent);
        document.getElementById('searchInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                filterContent();
            }}
        }});
        
        // Auto-logout after 24 hours
        setInterval(() => {{
            const authData = localStorage.getItem

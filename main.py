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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7601635113:AAG_bPYt03h1AdHcz-bMnPdnvFW9GHgC5g8")
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
        .header {{ background: linear-gradient(90deg, #667eea, #764ba2); color: white; padding

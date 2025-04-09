import os
import requests
import hashlib
import secrets
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# ===== CONFIGURATION =====
# Bot configuration
API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "8013725761:AAGQyr32ibk7HQNqxv4FSD2ZrrSLOmzknlg"
DEFAULT_THUMBNAIL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
SECRET_KEY = "hgygjugxchjhn"  # Change this to a secure random string
CHANNEL_ID = "@kuvnypkyjk"  # Channel to forward files
ADMIN_IDS = [1147534909]  # Replace with your admin user ID(s)

# Initialize Pyrogram Client
app = Client("secure_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== UTILITY FUNCTIONS =====
def generate_access_code():
    """Generate a random access code with ER.BABU prefix"""
    code = ''.join(secrets.choice('0123456789') for _ in range(6))
    return f"ER.BABU{{{code}}}"

def format_phone_number(phone):
    """Format phone number with partial masking"""
    if not phone:
        return "🚫 Hidden"
    return f"📞 {phone[:4]}****{phone[-3:]}"

async def get_user_details(client, user, is_admin=False):
    """Get user details with special handling for admin files"""
    if is_admin:
        return [
            ("🆔 User ID", "🚫 None (Admin File)"),
            ("👤 Username", "🚫 None (Admin File)"),
            ("📛 Full Name", "🚫 None (Admin File)")
        ], None
    
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
    """Extract name:URL pairs from file content"""
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

def categorize_urls(urls):
    """Categorize URLs into videos, PDFs, and others"""
    videos, pdfs, others = [], [], []
    
    for name, url in urls:
        new_url = url
        if "media-cdn.classplusapp.com/drm/" in url or "cpvod.testbook" in url:
            new_url = f"https://dragoapi.vercel.app/video/{url}"
            videos.append((name, new_url))
        elif "classplusapp" in url:
            new_url = f"https://api.extractor.workers.dev/player?url={url}"
            videos.append((name, new_url))
        elif ".zip" in url:
            new_url = f"https://video.pablocoder.eu.org/appx-zip?url={url}"
            videos.append((name, new_url))
        elif "dragoapi.vercel" in url:
            videos.append((name, url))
        elif "/master.mpd" in url:
            vid_id = url.split("/")[-2]
            new_url = f"https://player.muftukmall.site/?id={vid_id}"
            videos.append((name, new_url))
        elif "youtube.com/embed" in url or "youtu.be" in url or "youtube.com/watch" in url:
            videos.append((name, url))  # Keep YouTube URLs unchanged
        elif (
            ".m3u8" in url
            or ".mp4" in url
            or ".mkv" in url
            or ".webm" in url
            or ".MP4" in url
            or ".AVI" in url
            or ".MOV" in url
            or ".WMV" in url
            or ".MKV" in url
            or ".FLV" in url
            or ".MPEG" in url
            or ".mpd" in url
        ):
            videos.append((name, url))
        elif "pdf*" in url:
            new_url = f"https://dragoapi.vercel.app/pdf/{url}"
            pdfs.append((name, new_url))
        elif "pdf" in url:
            pdfs.append((name, url))
        else:
            others.append((name, url))

    return videos, pdfs, others

# Function to get MIME type based on file extension
def get_mime_type(url):
    if ".m3u8" in url:
        return "application/x-mpegURL"
    elif ".mp4" in url:
        return "video/mp4"
    elif ".mkv" in url:
        return "video/x-matroska"
    elif ".webm" in url:
        return "video/webm"
    elif ".avi" in url:
        return "video/x-msvideo"
    elif ".mov" in url:
        return "video/quicktime"
    elif ".wmv" in url:
        return "video/x-ms-wmv"
    elif ".flv" in url:
        return "video/x-flv"
    elif ".mpeg" in url:
        return "video/mpeg"
    elif ".mpd" in url:
        return "application/dash+xml"
    else:
        return "video/mp4"  # Default to mp4 if format is unknown

def generate_html(file_name, videos, pdfs, others, user_id, access_code, user_details, profile_photo_url=None, is_admin=False):
    """Generate the complete HTML file with all features"""
    base_name = os.path.splitext(file_name)[0]
    
    # Profile photo HTML
    profile_photo_html = ""
    if profile_photo_url:
        profile_photo_html = f"""
        <div class="profile-photo-container">
            <img src="{profile_photo_url}" alt="Profile Photo" class="profile-photo">
        </div>
        """
    
    # User details HTML
    details_html = "\n".join(
        f'<div class="detail-item"><span class="detail-label">{label}</span> <span class="detail-value">{value}</span></div>'
        for label, value in user_details
    )
    
    # Content links
    video_links = "".join(f'<a href="#" onclick="playVideo(\'{url}\')">{name}</a>' for name, url in videos)
    pdf_links = "".join(f'<a href="{url}" target="_blank">{name}</a> <a href="{url}" download>📥 Download PDF</a>' for name, url in pdfs)
    other_links = "".join(f'<a href="{url}" target="_blank">{name}</a>' for name, url in others)

    # Auth visibility
    auth_modal_style = "display: none;" if is_admin else "display: flex;"
    main_content_style = "display: block;" if is_admin else "display: none;"

    # HTML Template
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
        
        /* Auth modal styles */
        .auth-modal {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }}
        .auth-content {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            text-align: center;
        }}
        .auth-content h1 {{
            color: #007bff;
            margin-bottom: 10px;
            font-size: 28px;
            font-weight: bold;
            background: linear-gradient(90deg, #007bff, #6610f2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .auth-content h2 {{
            color: #ff416c;
            margin-bottom: 20px;
            font-size: 22px;
        }}
        /* ... (rest of your CSS styles) ... */
    </style>
</head>
<body>
    <!-- Auth Modal -->
    <div id="authModal" class="auth-modal" style="{auth_modal_style}">
        <div class="auth-content">
            <h1>Welcome to 𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚</h1>
            <h2>🔒 Secure Content Access</h2>
            <input type="text" id="userIdInput" placeholder="Your User ID">
            <input type="text" id="accessCodeInput" placeholder="Access Code (ER.BABU{{...}})">
            <button onclick="verifyAccess()">Verify</button>
            <p id="errorMessage" class="error-message">Invalid credentials</p>
        </div>
    </div>

    <!-- User Details Modal -->
    <div id="userDetailsModal" class="user-details-modal">
        <div class="user-details-content">
            <div class="user-details-header">
                <h3>👤 User Information</h3>
                <button class="close-btn" onclick="closeUserDetails()">×</button>
            </div>
            {details_html}
        </div>
    </div>

    <!-- Main Content -->
    <div id="mainContent" style="{main_content_style}">
        {profile_photo_html}
        <div class="header">{base_name}</div>
        <div class="subheading">📥 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div><br>
        <div class="datetime" id="datetime">📅 {datetime.now().strftime('%A %d %B, %Y | ⏰ %I:%M:%S %p')}</div><br>
        <p>🔹𝐔𝐬𝐞 𝐓𝐡𝐢𝐬 𝐁𝐨𝐭 𝐟𝐨𝐫 𝐓𝐗𝐓 𝐭𝐨 𝐇𝐓𝐌𝐋 𝐟𝐢𝐥𝐞 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 : <a href="https://t.me/htmldeveloperbot" target="_blank"> @𝐡𝐭𝐦𝐥𝐝𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫𝐛𝐨𝐭 </a></p>

        <!-- User Details Button -->
        <button class="user-details-btn" onclick="showUserDetails()">
            <i class="fas fa-user-circle"></i> View User Details
        </button>

        <!-- Search and Content Sections -->
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search for videos, PDFs, or other resources..." oninput="filterContent()">
        </div>

        <div id="noResults" class="no-results">No results found.</div>

        <!-- Video Players -->
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

        <!-- Content Tabs -->
        <div class="container">
            <div class="tab" onclick="showContent('videos')">Videos</div>
            <div class="tab" onclick="showContent('pdfs')">PDFs</div>
            <div class="tab" onclick="showContent('others')">Others</div>
        </div>

        <!-- Content Sections -->
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

    <!-- JavaScript -->
    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        // Authentication data
        const REQUIRED_USER_ID = "{user_id if not is_admin else 'ADMIN'}";
        const ACCESS_CODE = "{access_code if not is_admin else 'ADMIN_ACCESS'}";
        
        // Skip auth for admin files
        {"document.getElementById('authModal').style.display = 'none';" if is_admin else ""}
        {"document.getElementById('mainContent').style.display = 'block';" if is_admin else ""}
        
        // Rest of your JavaScript functions...
        // (Include all your existing JavaScript functions here)
    </script>
</body>
</html>"""

# ===== TELEGRAM HANDLERS =====
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    """Handle /start command"""
    await message.reply_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{message.from_user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

@app.on_message(filters.command(["cast", "broadcast"]) & filters.user(ADMIN_IDS))
async def broadcast_message(client: Client, message: Message):
    """Handle broadcast commands (/cast and /broadcast)"""
    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a message to broadcast it.")
        return
    
    confirm = await message.reply_text(
        "⚠️ Are you sure you want to broadcast this message to all users?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("❌ No", callback_data="broadcast_cancel")]
        ])
    )
    
    app.broadcast_message = message.reply_to_message

@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    """Handle document (TXT file) uploads"""
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("Please upload a .txt file.")
        return

    is_admin = message.from_user.id in ADMIN_IDS
    user = message.from_user
    user_id = user.id if not is_admin else "ADMIN"
    access_code = "ADMIN_ACCESS" if is_admin else generate_access_code()
    
    try:
        user_details, full_user = await get_user_details(client, user, is_admin=is_admin)
        profile_photo_url = DEFAULT_THUMBNAIL
        if not is_admin and full_user and full_user.photo:
            photo = await client.download_media(full_user.photo.big_file_id)
            if photo:
                profile_photo_url = DEFAULT_THUMBNAIL  # In production, upload to CDN
    except Exception as e:
        print(f"Error getting user details: {e}")
        user_details = [
            ("🆔 User ID", str(user.id)),
            ("👤 Username", f"@{user.username}" if user.username else "🚫 None"),
            ("📛 Full Name", f"{user.first_name or ''} {user.last_name or ''}".strip() or "🚫 None")
        ]
        profile_photo_url = None

    # Process file
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
            file_name, videos, pdfs, others, 
            user_id, access_code, user_details, 
            profile_photo_url, is_admin=is_admin
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

        # Prepare caption
        caption = f"""🔐 {'Admin' if is_admin else 'Secure'} HTML File\n\n"""
        if not is_admin:
            caption += f"👤 User: {user.first_name or ''} {user.last_name or ''}\n"
            caption += f"🆔 ID: <code>{user.id}</code>\n"
            caption += f"🔑 Access Code: <code>{access_code}</code>\n\n"
            caption += "⚠️ Important:\n"
            caption += "• This file is secured to your User ID\n"
            caption += "• The access code is required to view content\n"
            caption += "• Do NOT share this file with others"
        else:
            caption += "♾️ Admin File - No restrictions apply"

        # Send to user
        sent_message = await message.reply_document(
            document=html_path,
            file_name=f"{os.path.splitext(file_name)[0]}.html",
            caption=caption,
            thumb=thumbnail_path if thumbnail_path else None
        )

        # Forward to channel
        try:
            await client.send_document(
                chat_id=CHANNEL_ID,
                document=file_path,
                file_name=file_name,
                caption=f"{'Admin' if is_admin else 'User'} TXT file from {user.id}"
            )
            
            await client.send_document(
                chat_id=CHANNEL_ID,
                document=html_path,
                file_name=f"{os.path.splitext(file_name)[0]}.html",
                caption=f"{'Admin' if is_admin else 'User'} HTML file for {user.id}"
            )
        except Exception as e:
            print(f"Error forwarding files to channel: {e}")

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

# ===== CALLBACK HANDLERS =====
@app.on_callback_query(filters.regex("^broadcast_confirm$"))
async def broadcast_confirm(client, callback):
    """Handle broadcast confirmation"""
    await callback.answer()
    await callback.message.edit_text("📢 Broadcasting started...")
    
    success = 0
    failed = 0
    total = 0
    
    async for dialog in client.get_dialogs():
        if dialog.chat.type == "private":
            try:
                await app.broadcast_message.copy(dialog.chat.id)
                success += 1
            except Exception as e:
                print(f"Failed to send to {dialog.chat.id}: {e}")
                failed += 1
            total += 1
            await asyncio.sleep(0.1)
    
    await callback.message.edit_text(
        f"✅ Broadcast completed!\n\n"
        f"• Total users: {total}\n"
        f"• Successful: {success}\n"
        f"• Failed: {failed}"
    )

@app.on_callback_query(filters.regex("^broadcast_cancel$"))
async def broadcast_cancel(client, callback):
    """Handle broadcast cancellation"""
    await callback.answer()
    await callback.message.edit_text("❌ Broadcast canceled.")

@app.on_callback_query(filters.regex("^help$"))
async def help_handler(client, callback):
    """Handle help button"""
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
        "🔒 The file cannot be used by anyone else",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]])
    )

@app.on_callback_query(filters.regex("^back$"))
async def back_handler(client, callback):
    """Handle back button"""
    await callback.answer()
    await callback.message.edit_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{callback.from_user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    print("✅ Secure HTML Bot is running...")
    app.run()

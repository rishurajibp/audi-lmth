import os
import requests
import hashlib
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import secrets
import html

# ===== CONFIGURATION =====
API_ID = "21705536"
API_HASH = "c5bb241f6e6ecf33fe68a444e288de2d"
BOT_TOKEN = "7694154149:AAEvcjZT0vpI62EFiZPl9zxGQhbVPNRcQHs"
CHANNEL_USERNAME = "@kuvnypkyjk"
DEFAULT_THUMBNAIL = "https://i.imgur.com/JxLr5qU.png"
SECRET_KEY = "jbgfnhfjsdghnjik56"

# ===== BOT SETUP =====
app = Client("html_generator_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== UTILITY FUNCTIONS =====
def generate_user_token(user_id):
    return hashlib.sha256(f"{user_id}{SECRET_KEY}".encode()).hexdigest()

def generate_browser_token():
    return secrets.token_urlsafe(32)

def extract_names_and_urls(file_content):
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

def categorize_urls(urls):
    videos, pdfs, others = [], [], []
    
    for name, url in urls:
        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpd']):
            videos.append((name, url))
        elif 'youtube.com' in url or 'youtu.be' in url:
            videos.append((name, url))
        elif 'classplusapp.com' in url or 'testbook.com' in url:
            videos.append((name, f"https://dragoapi.vercel.app/video/{url}"))
        elif '.pdf' in url.lower():
            pdfs.append((name, url))
        elif '.zip' in url.lower():
            videos.append((name, f"https://video.pablocoder.eu.org/appx-zip?url={url}"))
        else:
            others.append((name, url))
    
    return videos, pdfs, others

def generate_html(file_name, videos, pdfs, others, user_id, user_token, browser_token):
    base_name = os.path.splitext(file_name)[0]
    escaped_base_name = html.escape(base_name)
    
    # Generate video links HTML
    video_links = []
    for name, url in videos:
        escaped_name = html.escape(name)
        escaped_url = html.escape(url)
        video_links.append(f'<a href="#" onclick="playVideo(\'{escaped_url}\')">{escaped_name}</a>')
    video_links_html = "".join(video_links)
    
    # Generate PDF links HTML
    pdf_links = []
    for name, url in pdfs:
        escaped_name = html.escape(name)
        escaped_url = html.escape(url)
        pdf_links.append(f'<a href="{escaped_url}" target="_blank">{escaped_name}</a>')
    pdf_links_html = "".join(pdf_links)
    
    # Generate other links HTML
    other_links = []
    for name, url in others:
        escaped_name = html.escape(name)
        escaped_url = html.escape(url)
        other_links.append(f'<a href="{escaped_url}" target="_blank">{escaped_name}</a>')
    other_links_html = "".join(other_links)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_base_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
            text-align: center;
        }}
        .auth-container {{
            max-width: 500px;
            margin: 50px auto;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .telegram-btn {{
            background: #0088cc;
            color: white;
            padding: 12px 20px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin: 15px 0;
            font-weight: bold;
        }}
        .content {{
            display: none;
        }}
        .verified-badge {{
            color: #4CAF50;
            margin-left: 5px;
        }}
        .tab {{
            padding: 10px 15px;
            margin: 5px;
            background: #007bff;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            display: inline-block;
        }}
        .video-list a, .pdf-list a, .other-list a {{
            display: block;
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            text-decoration: none;
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div id="auth-container" class="auth-container">
        <h2>🔒 Secure Content Access</h2>
        <div id="telegram-auth">
            <p>Please open this file in Telegram first to verify your identity:</p>
            <a href="https://t.me/{html.escape(app.me.username)}" class="telegram-btn">
                <i class="fab fa-telegram"></i> Open in Telegram
            </a>
            <p id="verified-msg" style="display:none;">
                <i class="fas fa-check-circle verified-badge"></i> Verified successfully!
            </p>
        </div>
        <div id="browser-access" style="display:none; margin-top:20px;">
            <h3>Browser Access Granted</h3>
            <p>You can now access this content in any browser for 7 days</p>
            <button onclick="copyAccessLink()" style="background:#007bff; color:white; border:none; padding:10px 15px; border-radius:5px; cursor:pointer;">
                <i class="fas fa-copy"></i> Copy Browser Link
            </button>
        </div>
    </div>

    <div id="content" class="content">
        <h1>{escaped_base_name}</h1>
        <div class="tabs">
            <div class="tab" onclick="showTab('videos')">Videos ({len(videos)})</div>
            <div class="tab" onclick="showTab('pdfs')">PDFs ({len(pdfs)})</div>
            <div class="tab" onclick="showTab('others')">Others ({len(others)})</div>
        </div>
        
        <div id="videos" class="tab-content">
            <h2>Video Lectures</h2>
            <div class="video-list">
                {video_links_html}
            </div>
        </div>
        
        <div id="pdfs" class="tab-content" style="display:none;">
            <h2>PDF Documents</h2>
            <div class="pdf-list">
                {pdf_links_html}
            </div>
        </div>
        
        <div id="others" class="tab-content" style="display:none;">
            <h2>Other Resources</h2>
            <div class="other-list">
                {other_links_html}
            </div>
        </div>
    </div>

    <script>
        // Authentication data
        const USER_ID = "{user_id}";
        const USER_TOKEN = "{user_token}";
        const BROWSER_TOKEN = "{browser_token}";
        const EXPIRY_DAYS = 7;
        
        // Check Telegram authentication
        function checkTelegramAuth() {{
            if (window.Telegram && Telegram.WebApp && Telegram.WebApp.initDataUnsafe && Telegram.WebApp.initDataUnsafe.user && Telegram.WebApp.initDataUnsafe.user.id && Telegram.WebApp.initDataUnsafe.user.id.toString() === USER_ID) {{
                localStorage.setItem('tg_verified', 'true');
                localStorage.setItem('tg_user_id', USER_ID);
                localStorage.setItem('browser_token', BROWSER_TOKEN);
                localStorage.setItem('token_expiry', Date.now() + (EXPIRY_DAYS * 24 * 60 * 60 * 1000));
                return true;
            }}
            return false;
        }}
        
        // Check existing valid authentication
        function checkExistingAuth() {{
            const urlParams = new URLSearchParams(window.location.search);
            const urlToken = urlParams.get('token');
            
            // Check URL token
            if (urlToken === BROWSER_TOKEN) {{
                localStorage.setItem('browser_token', BROWSER_TOKEN);
                localStorage.setItem('token_expiry', Date.now() + (EXPIRY_DAYS * 24 * 60 * 60 * 1000));
                return true;
            }}
            
            // Check localStorage
            const storedToken = localStorage.getItem('browser_token');
            const storedExpiry = localStorage.getItem('token_expiry');
            const storedUserId = localStorage.getItem('tg_user_id');
            const isVerified = localStorage.getItem('tg_verified');
            
            return isVerified === 'true' && 
                   storedUserId === USER_ID && 
                   storedToken === BROWSER_TOKEN &&
                   storedExpiry && parseInt(storedExpiry) > Date.now();
        }}
        
        // Copy browser access link
        function copyAccessLink() {{
            const url = new URL(window.location.href);
            url.searchParams.set('token', BROWSER_TOKEN);
            navigator.clipboard.writeText(url.toString())
                .then(() => alert('Browser access link copied!'))
                .catch(() => alert('Failed to copy link'));
        }}
        
        // Show content tab
        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(el => {{
                el.style.display = 'none';
            }});
            document.getElementById(tabName).style.display = 'block';
        }}
        
        // Play video
        function playVideo(url) {{
            if (url.includes('youtube.com') || url.includes('youtu.be')) {{
                window.open(url, '_blank');
            }} else {{
                alert('Would play video: ' + url);
                // Implement your video player here
            }}
        }}
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            if (checkTelegramAuth() || checkExistingAuth()) {{
                document.getElementById('auth-container').style.display = 'none';
                document.getElementById('content').style.display = 'block';
                document.getElementById('verified-msg').style.display = 'block';
                document.getElementById('browser-access').style.display = 'block';
            }} else {{
                document.getElementById('auth-container').style.display = 'block';
            }}
        }});
    </script>
</body>
</html>"""
    return html_content

# ===== TELEGRAM HANDLERS =====
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "📁 Welcome to HTML Generator Bot!\n\n"
        "Send me a .txt file with name:URL pairs to create a secure HTML file.\n\n"
        f"Your User ID: <code>{message.from_user.id}</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❓ Help", callback_data="help")]])
    )

@app.on_message(filters.document)
async def document_handler(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("❌ Please upload a .txt file with name:URL pairs.")
        return
    
    user = message.from_user
    user_id = user.id
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    # Generate tokens
    user_token = generate_user_token(user_id)
    browser_token = generate_browser_token()
    
    # Download and process file
    file_path = await message.download()
    html_path = ""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
        
        urls = extract_names_and_urls(content)
        videos, pdfs, others = categorize_urls(urls)
        
        # Generate HTML
        html_content = generate_html(
            message.document.file_name,
            videos, pdfs, others,
            user_id, user_token, browser_token
        )
        
        html_path = file_path.replace(".txt", ".html")
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        # Send to user
        await message.reply_document(
            document=html_path,
            caption=(
                f"📄 {os.path.splitext(message.document.file_name)[0]}\n"
                f"👤 Generated for: {user_name}\n\n"
                f"🔐 Browser Access Token:\n<code>{browser_token}</code>\n\n"
                "⚠️ Open in Telegram first to authenticate, then use the token for browser access."
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 New Token", callback_data=f"new_token_{user_id}")
            ]])
        )
        
        # Forward to channel
        if CHANNEL_USERNAME:
            await client.send_document(
                chat_id=CHANNEL_USERNAME,
                document=html_path,
                caption=f"HTML file generated for {user_name} ({user_id})"
            )
            
    except Exception as e:
        await message.reply_text(f"❌ Error processing file: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if html_path and os.path.exists(html_path):
            os.remove(html_path)

@app.on_callback_query(filters.regex(r"^new_token_(\d+)$"))
async def new_token_handler(client, callback):
    user_id = int(callback.matches[0].group(1))
    if callback.from_user.id != user_id:
        await callback.answer("❌ This button is not for you!", show_alert=True)
        return
    
    new_token = generate_browser_token()
    await callback.message.edit_text(
        callback.message.text.split("\n\n🔐")[0] + 
        f"\n\n🔐 New Browser Token:\n<code>{new_token}</code>\n\n"
        "⚠️ Open in Telegram first to authenticate, then use the token for browser access.",
        reply_markup=callback.message.reply_markup
    )
    await callback.answer("✅ New token generated!")

@app.on_callback_query(filters.regex("^help$"))
async def help_handler(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "📚 Help Guide:\n\n"
        "1. Prepare a .txt file with content like:\n"
        "<code>Lecture 1:https://example.com/video1.mp4\n"
        "Notes:https://example.com/notes.pdf</code>\n\n"
        "2. Send the file to this bot\n"
        "3. Open the received HTML file in Telegram first\n"
        "4. After Telegram verification, use the browser token to access from any device\n\n"
        "🔒 All files are secured to your Telegram account",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
    )

@app.on_callback_query(filters.regex("^back$"))
async def back_handler(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "📁 Welcome to HTML Generator Bot!\n\n"
        "Send me a .txt file with name:URL pairs to create a secure HTML file.\n\n"
        f"Your User ID: <code>{callback.from_user.id}</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❓ Help", callback_data="help")]])
    )

# ===== MAIN =====
if __name__ == "__main__":
    print("✅ Bot is running...")
    app.run()

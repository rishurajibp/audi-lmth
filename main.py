import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

# Bot configuration
API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "8013725761:AAGQyr32ibk7HQNqxv4FSD2ZrrSLOmzknlg"
CHANNEL_USERNAME = "@kuvnypkyjk"
DEFAULT_THUMBNAIL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"  # Default thumbnail URL

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_names_and_urls(file_content):
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

def categorize_urls(urls):
    videos = []
    pdfs = []
    others = []

    for name, url in urls:
        new_url = url
        if "media-cdn.classplusapp.com/drm/" in url or "cpvod.testbook" in url:
            new_url = f"https://dragoapi.vercel.app/video/{url}"
            videos.append((name, new_url))
        elif "classplusapp" in url and "m3u8" in url:
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
            videos.append((name, url))
        elif (
            ".m3u8" in url or ".mp4" in url or ".mkv" in url or ".webm" in url or
            ".MP4" in url or ".AVI" in url or ".MOV" in url or ".WMV" in url or
            ".MKV" in url or ".FLV" in url or ".MPEG" in url or ".mpd" in url
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

def generate_html(file_name, videos, pdfs, others):
    file_name_without_extension = os.path.splitext(file_name)[0]

    video_links = "".join(f'<a href="#" onclick="playVideo(\'{url}\')">{name}</a>' for name, url in videos)
    pdf_links = "".join(f'<a href="{url}" target="_blank">{name}</a> <a href="{url}" download>📥 Download PDF</a>' for name, url in pdfs)
    other_links = "".join(f'<a href="{url}" target="_blank">{name}</a>' for name, url in others)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name_without_extension}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }}
        body {{ background: #f5f7fa; text-align: center; }}
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
    </style>
</head>
<body>
    <div class="header">{file_name_without_extension}</div>
    <div class="subheading">📥 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div><br>
    <div class="datetime" id="datetime">📅 {datetime.now().strftime('%A %d %B, %Y | ⏰ %I:%M:%S %p')}</div><br>
    <p>🔹𝐔𝐬𝐞 𝐓𝐡𝐢𝐬 𝐁𝐨𝐭 𝐟𝐨𝐫 𝐓𝐗𝐓 𝐭𝐨 𝐇𝐓𝐌𝐋 𝐟𝐢𝐥𝐞 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 : <a href="https://t.me/htmldeveloperbot" target="_blank"> @𝐡𝐭𝐦𝐥𝐝𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫𝐛𝐨𝐭 </a></p>

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

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
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
    return html_template

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text("𝐖𝐞𝐥𝐜𝐨𝐦𝐞! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐮𝐩𝐥𝐨𝐚𝐝 𝐚 .𝐭𝐱𝐭 𝐟𝐢𝐥𝐞 𝐜𝐨𝐧𝐭𝐚𝐢𝐧𝐢𝐧𝐠 𝐔𝐑𝐋𝐬.")

@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("Please upload a .txt file.")
        return

    # Get user details
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if message.from_user.username:
        user_name = f"@{message.from_user.username}"

    # Download the file
    file_path = await message.download()
    file_name = message.document.file_name

    # Process file content
    with open(file_path, "r") as f:
        file_content = f.read()

    urls = extract_names_and_urls(file_content)
    videos, pdfs, others = categorize_urls(urls)

    # Generate HTML
    html_content = generate_html(file_name, videos, pdfs, others)
    html_file_path = file_path.replace(".txt", ".html")
    with open(html_file_path, "w") as f:
        f.write(html_content)

    # Prepare data for caption
    total_videos = len(videos)
    total_pdfs = len(pdfs)
    total_others = len(others)
    file_name_without_extension = os.path.splitext(file_name)[0]

    caption = f"""📖𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 : {file_name_without_extension}

🎞️ 𝐕𝐢𝐝𝐞𝐨𝐬 : {total_videos}, 📚 𝐏𝐝𝐟𝐬 : {total_pdfs}, 💾 𝐎𝐭𝐡𝐞𝐫𝐬 : {total_others}

👤𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐁𝐲 : {user_name} - {user_id}

✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞!

📥 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 : 𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™"""

    # Download thumbnail
    thumbnail_path = None
    try:
        thumbnail_response = requests.get(DEFAULT_THUMBNAIL)
        thumbnail_path = "thumbnail.jpg"
        with open(thumbnail_path, "wb") as f:
            f.write(thumbnail_response.content)
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")

    # Send to user
    await message.reply_document(
        document=html_file_path,
        caption=caption,
        thumb=thumbnail_path if thumbnail_path else None
    )

    # Forward to channel
    await client.send_document(
        chat_id=CHANNEL_USERNAME,
        document=file_path,
        caption=f"📥 Original TXT file from {user_name} ({user_id})",
        thumb=thumbnail_path if thumbnail_path else None
    )
    
    await client.send_document(
        chat_id=CHANNEL_USERNAME,
        document=html_file_path,
        caption=caption,
        thumb=thumbnail_path if thumbnail_path else None
    )

    # Cleanup
    os.remove(file_path)
    os.remove(html_file_path)
    if thumbnail_path and os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

if __name__ == "__main__":
    print("Bot is running...")
    app.run()

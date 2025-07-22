import logging
import re
import requests
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
NDUS_COOKIE = os.getenv("NDUS_COOKIE")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def extract_shareid_and_uk(url):
    shareid_match = re.search(r"/s/([^/?&]+)", url)
    uk_match = re.search(r"[?&]uk=(\d+)", url)
    shareid = shareid_match.group(1) if shareid_match else None
    uk = uk_match.group(1) if uk_match else "0"
    return shareid, uk

def get_file_list(shareid, uk):
    headers = {"Cookie": f"ndus={NDUS_COOKIE}"}
    api_url = f"https://api.terabox.com/share/list?shareid={shareid}&uk={uk}&limit=100&order=time&desc=1"
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errno") != 0:
            return None, f"API error: {data.get('errmsg', 'Unknown error')}"
        file_list = data.get("list", [])
        return file_list, None
    except Exception as e:
        return None, f"Request failed: {e}"

def start(update, context):
    update.message.reply_text("Send me a TeraBox share URL, and I'll list files for you!")

def handle_message(update, context):
    url = update.message.text.strip()
    shareid, uk = extract_shareid_and_uk(url)
    if not shareid:
        update.message.reply_text("Invalid TeraBox share URL.")
        return
    
    update.message.reply_text("Fetching file list, please wait...")

    files, error = get_file_list(shareid, uk)
    if error:
        update.message.reply_text(f"❌ Failed to get file info: {error}")
        return

    if not files:
        update.message.reply_text("No files found in this share.")
        return

    response = "Files found:\n"
    for f in files:
        name = f.get("filename", "Unnamed")
        size = f.get("size", 0)
        size_mb = round(size / (1024*1024), 2)
        response += f"- {name} ({size_mb} MB)\n"
    update.message.reply_text(response)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

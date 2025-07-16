import os
import re
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('8041495553:AAEtRSg9scPIbrXo5Dmq09p09fbw685-K6w')

# Database to store video/PDF counts (in a real app, use a proper database)
media_counts = {
    'video': 0,
    'pdf': 0
}

def extract_info_from_caption(caption):
    """Extract title and batch from the original caption"""
    if not caption:
        return None, None
    
    # Extract title
    title_match = re.search(r'Name\s*➜\s*(.+?)\n', caption)
    title = title_match.group(1).strip() if title_match else "Untitled"
    
    # Extract batch
    batch_match = re.search(r'Batch\s*➜\s*(.+?)\n', caption)
    batch = batch_match.group(1).strip() if batch_match else "Unknown Batch"
    
    return title, batch

def generate_new_caption(media_type, title, batch):
    """Generate the new caption based on the specified format"""
    media_counts[media_type] += 1
    
    if media_type == 'video':
        media_id = f"🎞️ VID_ID: {media_counts[media_type]}."
        prefix = "VID"
    else:
        media_id = f"📁 PDF_ID: {media_counts[media_type]}."
        prefix = "PDF"
    
    return f"""{media_id}

📝 Title: {title}

📚 Batch Name: {batch}

📥 Extracted By : @ItsNomis

━━━━━✦ＮＯＭＩＳ✦━━━━━"""

def handle_media(update: Update, context: CallbackContext):
    """Handle incoming videos and documents"""
    message = update.message
    
    if message.video:
        media_type = 'video'
        file = message.video
    elif message.document:
        media_type = 'pdf'
        file = message.document
    else:
        return
    
    # Get the original caption
    original_caption = message.caption
    
    # Extract title and batch from original caption
    title, batch = extract_info_from_caption(original_caption)
    
    # Generate new caption
    new_caption = generate_new_caption(media_type, title, batch)
    
    # Edit the message with new caption
    message.edit_caption(new_caption)

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello! I am your caption changer bot. Send me videos or files and I will reformat their captions.')

def main():
    """Start the bot."""
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.video | Filters.document, handle_media))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

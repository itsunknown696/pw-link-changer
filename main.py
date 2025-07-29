import os
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
WAITING_FOR_FILE, WAITING_FOR_TOKEN = range(2)

def start(update: Update, context: CallbackContext) -> int:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        "📁 Send me a text file with MPD links in the format:\n"
        "name:link\n\n"
        "I'll convert them to the PW Player format.\n"
        "Note: Names can contain colons, I'll handle them properly!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return WAITING_FOR_FILE

def handle_file(update: Update, context: CallbackContext) -> int:
    """Handle the document and ask for token."""
    if not update.message.document.mime_type == 'text/plain':
        update.message.reply_text("❌ Please send a text file (.txt)")
        return WAITING_FOR_FILE
    
    # Download the file
    file = context.bot.get_file(update.message.document.file_id)
    file_path = f"temp_{update.message.from_user.id}.txt"
    file.download(file_path)
    
    context.user_data['file_path'] = file_path
    update.message.reply_text("🔑 Now please send me your PW token:")
    return WAITING_FOR_TOKEN

def handle_token(update: Update, context: CallbackContext) -> int:
    """Process the file with the provided token."""
    token = update.message.text.strip()
    file_path = context.user_data.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        update.message.reply_text("❌ Error: File not found. Please start over.")
        return ConversationHandler.END
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        converted_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Split on LAST colon only
            if ':' in line:
                *name_parts, url = line.rsplit(':', 1)
                name_part = ':'.join(name_parts).strip()
                url = url.strip()
                
                if url.endswith('.mpd'):
                    converted_url = (
                        f"https://anonymouspwplayerr-f996115ea61a.herokuapp.com/"
                        f"pw?url={url}&token={token}"
                    )
                    converted_lines.append(f"{name_part}:{converted_url}")
                else:
                    converted_lines.append(line)
            else:
                converted_lines.append(line)
        
        # Create output file
        output_path = f"converted_{update.message.from_user.id}.txt"
        with open(output_path, 'w') as f:
            f.write('\n'.join(converted_lines))
        
        # Send back the converted file
        with open(output_path, 'rb') as f:
            update.message.reply_document(
                document=f,
                caption="✅ Here's your converted file!",
                reply_markup=ReplyKeyboardRemove()
            )
            
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        update.message.reply_text("❌ An error occurred while processing the file.")
    
    # Clean up
    for path in [file_path, output_path]:
        if path and os.path.exists(path):
            os.remove(path)
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('❌ Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    
    file_path = context.user_data.get('file_path')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    updater = Updater("7718900835:AAGIrZdH5_XETNUBfV0AqhkQt0UydDvIw-I", use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_FILE: [MessageHandler(Filters.document, handle_file)],
            WAITING_FOR_TOKEN: [MessageHandler(Filters.text & ~Filters.command, handle_token)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

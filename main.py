import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Configuration
BOT_ADMINS = [8074755883]  # Your user ID
processing_limit = 100  # Number of captions to process at once
processing_delay = 3  # Delay in seconds between batches

# Conversation states
GET_CHANNEL_ID, GET_BATCH_NAME, GET_START_COUNTER = range(3)

# Store channel data
channel_data = {}

def format_caption(counter, title, is_pdf=False, batch_name=""):
    """Generate formatted caption with bold and line gaps"""
    media_type = "📁 PDF_ID" if is_pdf else "🎞️ VID_ID"
    return (
        f"<b>{media_type}: {counter}.</b>\n\n"
        f"<b>📝 Title: {title}</b>\n\n"
        f"<b>📚 Batch Name: {batch_name}</b>\n\n"
        f"<b>📥 Extracted By: @ItsNomis</b>\n\n"
        "<b>━━━━━✦ＮＯＭＩＳ✦━━━━━</b>"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in BOT_ADMINS:
        return
    
    await update.message.reply_text(
        "🛠️ <b>Auto-Caption Bot Setup</b>\n\n"
        "Please send me the Channel ID where you want me to work:\n"
        "(Should start with -100 for public channels)",
        parse_mode='HTML'
    )
    
    return GET_CHANNEL_ID

async def get_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = update.message.text.strip()
    
    if not channel_id.startswith('-100'):
        await update.message.reply_text(
            "❌ Invalid Channel ID format. It should start with -100\n"
            "Please send the correct Channel ID:"
        )
        return GET_CHANNEL_ID
    
    context.user_data['channel_id'] = channel_id
    await update.message.reply_text(
        "✅ Channel ID received!\n\n"
        "Now please send your Batch Name:"
    )
    
    return GET_BATCH_NAME

async def get_batch_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    batch_name = update.message.text
    context.user_data['batch_name'] = batch_name
    
    await update.message.reply_text(
        "✅ Batch Name received!\n\n"
        "Now please send the starting counter number (e.g., 1):"
    )
    
    return GET_START_COUNTER

async def get_start_counter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_counter = int(update.message.text)
        channel_id = context.user_data['channel_id']
        batch_name = context.user_data['batch_name']
        
        channel_data[channel_id] = {
            'batch_name': batch_name,
            'counter': start_counter
        }
        
        await update.message.reply_text(
            f"✅ <b>Setup Complete!</b>\n\n"
            f"Channel ID: {channel_id}\n"
            f"Batch Name: {batch_name}\n"
            f"Starting Counter: {start_counter}\n\n"
            "Now when you post videos/documents in that channel, "
            "I'll automatically update their captions.",
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number for the counter!"
        )
        return GET_START_COUNTER

async def handle_new_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return
    
    channel_id = str(update.channel_post.chat.id)
    if channel_id not in channel_data:
        return
    
    channel_info = channel_data[channel_id]
    current_counter = channel_info['counter']
    
    # Check if we need to take a break
    if (current_counter - channel_info.get('initial_counter', current_counter)) % processing_limit == 0 and current_counter > 1:
        print(f"Processed {processing_limit} captions. Taking a {processing_delay} second break...")
        await asyncio.sleep(processing_delay)
    
    # Extract title from original caption
    original_caption = update.channel_post.caption or ""
    title = "Untitled"
    if "Name  ➜" in original_caption:
        title = original_caption.split("Name  ➜")[1].split("\n")[0].strip()
    
    # Prepare caption
    is_pdf = update.channel_post.document is not None
    batch_name = channel_info.get('batch_name', "Board-12th Apni Kaksha")
    caption = format_caption(current_counter, title, is_pdf, batch_name)
    
    # Edit the message
    try:
        await context.bot.edit_message_caption(
            chat_id=channel_id,
            message_id=update.channel_post.message_id,
            caption=caption,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Edit failed: {e}")
        try:
            if update.channel_post.video:
                await context.bot.send_video(
                    chat_id=channel_id,
                    video=update.channel_post.video.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif update.channel_post.document:
                await context.bot.send_document(
                    chat_id=channel_id,
                    document=update.channel_post.document.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            await context.bot.delete_message(
                chat_id=channel_id,
                message_id=update.channel_post.message_id
            )
        except Exception as e2:
            print(f"Repost failed: {e2}")
            return
    
    # Increment counter
    channel_data[channel_id]['counter'] += 1
    print(f"Processed media #{current_counter} in channel {channel_id}")

def main():
    application = Application.builder().token("8041495553:AAEtRSg9scPIbrXo5Dmq09p09fbw685-K6w").build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_id)],
            GET_BATCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_batch_name)],
            GET_START_COUNTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_counter)],
        },
        fallbacks=[]
    )
    
    application.add_handler(conv_handler)
    
    # Handle new videos and documents in channels
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & (filters.VIDEO | filters.Document.ALL),
        handle_new_media
    ))
    
    print("Bot started. Use /start in DM to configure.")
    application.run_polling()

if __name__ == "__main__":
    main()

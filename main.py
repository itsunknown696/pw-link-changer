from pyrogram import Client, filters
import fitz  # PyMuPDF for PDF to image conversion
import os

# ====== BOT CONFIG ======
API_ID = 27238809
API_HASH = "c854867f7b27f65aebd41392eb2af1d9"
BOT_TOKEN = "7782085620:AAGKaPWPtJGMzLkcjcMMxcRNCzTJAdOHtOY"

app = Client("pdf_to_img_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.document & filters.private)
async def pdf_to_images(client, message):
    if not message.document.file_name.endswith(".pdf"):
        await message.reply_text("❌ Please send a PDF file only.")
        return

    # Download PDF
    file_path = await message.download()
    await message.reply_text("📥 Downloaded! Now converting PDF pages to images...")

    try:
        # Open PDF
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High resolution (2x zoom)

            img_file = f"page_{page_num+1}.png"
            pix.save(img_file)

            # Send image back as a document (file)
            await client.send_document(
                chat_id=message.chat.id,
                document=img_file,
                caption=f"🖼 Page {page_num+1}"
            )

            os.remove(img_file)

        await message.reply_text("✅ Done! All pages sent as image files.")

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 Hi! Send me a PDF file and I’ll send back each page as an image (file)."
    )


print("🤖 Bot is running...")
app.run()

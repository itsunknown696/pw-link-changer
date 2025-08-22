from pyrogram import Client, filters
import fitz  # PyMuPDF for PDF processing
import os

# ====== BOT CONFIG ======
API_ID = 27238809
API_HASH = "c854867f7b27f65aebd41392eb2af1d9"
BOT_TOKEN = "7782085620:AAGKaPWPtJGMzLkcjcMMxcRNCzTJAdOHtOY"

app = Client("pdf_split_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.document & filters.private)
async def split_pdf(client, message):
    if not message.document.file_name.endswith(".pdf"):
        await message.reply_text("❌ Please send a PDF file only.")
        return

    # Download PDF
    file_path = await message.download()
    await message.reply_text("📥 Downloaded! Now splitting the PDF...")

    try:
        # Open PDF
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            # Extract each page
            pdf_writer = fitz.open()
            pdf_writer.insert_pdf(doc, from_page=page_num, to_page=page_num)

            out_file = f"page_{page_num+1}.pdf"
            pdf_writer.save(out_file)
            pdf_writer.close()

            # Send page back to user
            await client.send_document(
                chat_id=message.chat.id,
                document=out_file,
                caption=f"📄 Page {page_num+1}"
            )

            os.remove(out_file)

        await message.reply_text("✅ Done! All pages sent.")

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 Hi! Send me a PDF file and I’ll split it into single-page PDFs."
    )


print("🤖 Bot is running...")
app.run()

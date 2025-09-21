from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your @hiringet channel ID

# Initialize application
application = Application.builder().token(BOT_TOKEN).build()

async def post_job_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to get job post text from admin"""
    await update.message.reply_text(
        "📝 Please paste your job post text. I'll format it with buttons and post to @hiringet!\n\n"
        "Include:\n• Job Title\n• Company\n• Location\n• Requirements\n• How to apply"
    )
    # Set state to wait for job text
    context.user_data['awaiting_job_text'] = True

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the text input and create the formatted post"""
    if context.user_data.get('awaiting_job_text'):
        job_text = update.message.text
        
        # Create inline keyboard with side-by-side buttons
        keyboard = [
            [
                InlineKeyboardButton("📤 Post a Job", url="https://t.me/help_bot?start=postajob"),
                InlineKeyboardButton("📄 Create CV", url="https://t.me/help_bot?start=makecv")
            ],
            [
                InlineKeyboardButton("👥 Join Channel", url="https://t.me/hiringet")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format the final post
        formatted_post = f"""
🚀 {job_text}

━━━━━━━━━━━━━━━━━━━━━━
💼 **Looking for opportunities?**
Create a professional CV and apply directly!

🔍 **Hiring?** Post jobs instantly to thousands of seekers!
        """
        
        try:
            # Post to channel
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=formatted_post,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(
                "✅ Success! Your job post has been published to @hiringet with interactive buttons!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("View Post", url=f"https://t.me/hiringet")]
                ])
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error posting to channel: {e}")
        
        # Clear the state
        context.user_data['awaiting_job_text'] = False

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Button clicked!")

def main():
    # Add handlers
    application.add_handler(CommandHandler("post", post_job_ad))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add handler for text messages (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    print("Post creator bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
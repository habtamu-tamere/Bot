import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, ContextTypes, MessageHandler, filters
from handlers.postajob_conv import *
from handlers.makecv_conv import *

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHANNEL_ID = os.getenv('ADMIN_CHANNEL_ID')
WEB_URL = os.getenv('WEB_URL', 'https://bot-anxw.onrender.com')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', '')  # Render provides this
PORT = int(os.getenv('PORT', 10000))  # Render provides PORT

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with parameters"""
    try:
        if context.args:
            start_param = context.args[0].lower()
            if start_param == 'postajob':
                return await postajob_command(update, context)
            elif start_param == 'makecv':
                return await makecv_command(update, context)
        
        welcome_message = (
            "🤖 *Welcome to Habte Job Portal Bot!*\n\n"
            "I help you post jobs to @hiringet channel and create professional CVs.\n\n"
            "📋 *Available Commands:*\n"
            "/postajob - Post a new job opportunity\n"
            "/makecv - Create a professional CV\n"
            "/web - Get web interface link for easy posting\n"
            "/help - Show this help message\n\n"
            "💡 *Pro Tip:* Use our web interface for the best experience!"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in start_command: {e}")

async def web_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the web interface link to user"""
    try:
        web_message = (
            "🌐 *Habte Job Portal Web Interface*\n\n"
            "Use our user-friendly web page for easy job posting:\n\n"
            f"👉 {WEB_URL}\n\n"
            "✨ *Features:*\n"
            "• Easy text input with copy functionality\n"
            "• One-click Telegram bot integration\n"
            "• Mobile-friendly design\n"
            "• Quick access to both job posting and CV creation\n\n"
            "Share this link with other employers! 🚀"
        )
        await update.message.reply_text(web_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in web_command: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    try:
        help_message = (
            "🆘 *Help Guide - Habte Job Portal Bot*\n\n"
            "📋 *Available Commands:*\n"
            "/start - Start the bot\n"
            "/postajob - Post a job to @hiringet channel\n"
            "/makecv - Create a professional CV\n"
            "/web - Get web interface link\n"
            "/help - Show this help message\n\n"
            "💡 *How to Post a Job:*\n"
            "1. Use /postajob or web interface\n"
            "2. Follow the step-by-step guide\n"
            "3. Submit your job details\n"
            "4. We'll review and post it to @hiringet\n\n"
            "🌐 *Web Interface:*\n"
            f"{WEB_URL}\n\n"
            "Need more help? Contact @hiringet admin."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help_command: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by Updates"""
    logger.error(f"Update {update} caused error {context.error}")

def setup_application():
    """Set up the application with all handlers"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Store admin channel ID in bot data
    application.bot_data['admin_channel_id'] = ADMIN_CHANNEL_ID
    
    # Add conversation handler for /postajob
    postajob_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('postajob', postajob_command)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add conversation handler for /makecv
    makecv_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('makecv', makecv_command)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_full_name)],
            HEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_headline)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_skills)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_experience)],
        },
        fallbacks=[CommandHandler('cancel', cancel_cv)],
    )
    
    # Add basic commands
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('web', web_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(postajob_conv_handler)
    application.add_handler(makecv_conv_handler)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application

async def start_webhook():
    """Start the bot in webhook mode"""
    application = setup_application()
    
    # Set webhook
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    
    logger.info(f"Webhook set to: {webhook_url}")
    logger.info("Bot is running in webhook mode...")
    
    return application

async def start_polling():
    """Start the bot in polling mode (for local development)"""
    application = setup_application()
    
    logger.info("Bot is running in polling mode...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    return application

# For Render webhook endpoint
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Habte Job Portal Bot is running! Visit /webhook for Telegram updates."

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle Telegram webhook updates"""
    application = await start_webhook()
    update = Update.de_json(await request.get_json(), application.bot)
    await application.process_update(update)
    return 'OK'

@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    # Determine run mode based on environment
    if RENDER_EXTERNAL_URL:  # Production - use webhook
        import asyncio
        from threading import Thread
        
        def run_flask():
            app.run(host='0.0.0.0', port=PORT, debug=False)
        
        # Start Flask in a separate thread
        flask_thread = Thread(target=run_flask)
        flask_thread.start()
        
        # Set webhook
        asyncio.run(start_webhook())
        
    else:  # Development - use polling
        import asyncio
        asyncio.run(start_polling())
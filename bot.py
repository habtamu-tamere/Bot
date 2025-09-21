import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ConversationHandler
from handlers.postajob_conv import *
from handlers.makecv_conv import *

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHANNEL_ID = os.getenv('ADMIN_CHANNEL_ID')
WEB_URL = os.getenv('WEB_URL', 'https://your-web-page-url.here')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with parameters"""
    # Check if start command has parameters
    if context.args:
        start_param = context.args[0].lower()
        if start_param == 'postajob':
            return await postajob_command(update, context)
        elif start_param == 'makecv':
            return await makecv_command(update, context)
    
    # Default start message
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

async def web_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the web interface link to user"""
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
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

async def end_of_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send web promotion at the end of conversations"""
    if WEB_URL:
        promo_message = (
            "💡 *Pro Tip:* For even easier job posting, use our web interface!\n\n"
            f"🌐 {WEB_URL}\n\n"
            "Features:\n"
            "• Easy text input\n• Copy to clipboard\n• One-click bot access\n• Mobile friendly"
        )
        await update.message.reply_text(promo_message, parse_mode='Markdown')

def main():
    # Create application
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
    
    # Start the bot
    print("🤖 Habte Job Portal Bot is running...")
    print(f"🌐 Web interface: {WEB_URL}")
    application.run_polling()

if __name__ == '__main__':
    main()
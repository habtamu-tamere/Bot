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
WEB_URL = os.getenv('WEB_URL', '')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', '')
PORT = int(os.getenv('PORT', 10000))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your existing bot commands here (start_command, web_command, help_command, etc.)
# ... [Keep all your existing bot command functions] ...


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


def setup_application():
    """Set up the application with all handlers"""
    application = Application.builder().token(BOT_TOKEN).build()
    
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
    
    return application

# Flask app setup
from flask import Flask, request, send_file, render_template_string
import html

app = Flask(__name__)

# HTML template as string (copy your entire index.html content here)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Habte Job Portal - Post to Telegram</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .content { padding: 30px; }
        .input-section { margin-bottom: 30px; }
        .input-section label { display: block; font-weight: 600; margin-bottom: 10px; color: #333; font-size: 1.1em; }
        #jobText { width: 100%; min-height: 200px; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-family: inherit; font-size: 16px; resize: vertical; transition: border-color 0.3s ease; }
        #jobText:focus { outline: none; border-color: #4facfe; box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1); }
        .button-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }
        .telegram-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 15px 20px; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; text-decoration: none; text-align: center; }
        .telegram-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2); }
        .telegram-btn i { font-size: 1.2em; }
        .post-btn { background: linear-gradient(135deg, #0088cc 0%, #00a2e8 100%); color: white; }
        .post-btn:hover { background: linear-gradient(135deg, #0077b3 0%, #0091cc 100%); }
        .cv-btn { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; }
        .cv-btn:hover { background: linear-gradient(135deg, #218838 0%, #1aa179 100%); }
        .copy-btn { background: linear-gradient(135deg, #6c757d 0%, #868e96 100%); color: white; grid-column: span 2; }
        .copy-btn:hover { background: linear-gradient(135deg, #5a6268 0%, #727b84 100%); }
        .instructions { background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 30px; border-left: 4px solid #4facfe; }
        .instructions h3 { color: #333; margin-bottom: 15px; }
        .instructions ol { margin-left: 20px; line-height: 1.6; }
        .instructions li { margin-bottom: 10px; }
        .success-message { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-top: 20px; text-align: center; display: none; }
        .bot-info { background: #e3f2fd; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center; border: 2px dashed #2196f3; }
        @media (max-width: 600px) { .button-grid { grid-template-columns: 1fr; } .copy-btn { grid-column: span 1; } .header h1 { font-size: 2em; } }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 Habte Job Portal</h1>
            <p>Post jobs directly to @hiringet Telegram channel</p>
        </div>

        <div class="content">
            <div class="bot-info">
                <strong>🤖 Telegram Bot:</strong> @help_bot<br>
                <strong>📢 Channel:</strong> @hiringet
            </div>

            <div class="input-section">
                <label for="jobText">📝 Paste Your Job Post Here:</label>
                <textarea 
                    id="jobText" 
                    placeholder="Enter job title, description, requirements, and contact information...
Example:
🚀 Senior Python Developer Needed!

📍 Location: Remote
💼 Type: Full-time
💰 Salary: $80k - $120k

Requirements:
• 3+ years Python experience
• Django/Flask framework
• PostgreSQL knowledge

👉 Apply: careers@company.com"
                ></textarea>
            </div>

            <div class="button-grid">
                <a href="https://t.me/help_bot?start=postajob" class="telegram-btn post-btn" target="_blank">
                    <i class="fab fa-telegram"></i>
                    Post Job via Bot
                </a>
                
                <a href="https://t.me/help_bot?start=makecv" class="telegram-btn cv-btn" target="_blank">
                    <i class="fas fa-file-alt"></i>
                    Create CV via Bot
                </a>
                
                <button onclick="copyJobText()" class="telegram-btn copy-btn">
                    <i class="fas fa-copy"></i>
                    Copy Job Text
                </button>
            </div>

            <div id="successMessage" class="success-message">
                <i class="fas fa-check-circle"></i>
                Job text copied to clipboard!
            </div>

            <div class="instructions">
                <h3>📋 How to Use:</h3>
                <ol>
                    <li>Paste your job post in the text area above</li>
                    <li>Click "Copy Job Text" to copy it to clipboard</li>
                    <li>Click "Post Job via Bot" to open Telegram and start job posting process</li>
                    <li>Click "Create CV via Bot" to help candidates create their CV</li>
                    <li>The bot will guide you through the process step-by-step</li>
                    <li>All job posts are reviewed before appearing on @hiringet</li>
                </ol>
            </div>
        </div>
    </div>

    <script>
        function copyJobText() {
            const jobText = document.getElementById('jobText');
            const successMessage = document.getElementById('successMessage');
            
            if (!jobText.value.trim()) {
                alert('Please enter some job text first!');
                jobText.focus();
                return;
            }
            
            jobText.select();
            jobText.setSelectionRange(0, 99999);
            
            try {
                navigator.clipboard.writeText(jobText.value).then(() => {
                    successMessage.style.display = 'block';
                    setTimeout(() => { successMessage.style.display = 'none'; }, 3000);
                });
            } catch (err) {
                document.execCommand('copy');
                successMessage.style.display = 'block';
                setTimeout(() => { successMessage.style.display = 'none'; }, 3000);
            }
        }

        const textarea = document.getElementById('jobText');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        window.addEventListener('load', function() {
            textarea.focus();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Serve the main web page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle Telegram webhook updates"""
    try:
        application = setup_application()
        json_data = await request.get_json()
        update = Update.de_json(json_data, application.bot)
        await application.initialize()
        await application.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'ERROR', 500

@app.route('/health')
def health():
    return 'OK'

async def set_webhook():
    """Set webhook for Telegram"""
    application = setup_application()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

if __name__ == '__main__':
    # Run Flask app
    if RENDER_EXTERNAL_URL:
        # Production - set webhook
        import asyncio
        asyncio.run(set_webhook())
        logger.info("Webhook mode started")
    else:
        # Development - no webhook needed for web interface
        logger.info("Development mode - web interface only")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
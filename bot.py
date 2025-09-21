import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from handlers.postajob_conv import *
from handlers.makecv_conv import *

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHANNEL_ID = os.getenv('ADMIN_CHANNEL_ID')
MAIN_CHANNEL_ID = os.getenv('MAIN_CHANNEL_ID', '@hiringet')  # Your main channel
WEB_URL = os.getenv('WEB_URL', '')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', '')
PORT = int(os.getenv('PORT', 10000))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store pending job approvals
pending_approvals = {}

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
            "/quickpost - Post a job directly (admin approval needed)\n"
            "/postajob - Detailed job posting process\n"
            "/makecv - Create a professional CV\n"
            "/web - Get web interface link\n"
            "/help - Show help message\n\n"
            "💡 *Quick Post:* Use /quickpost for fast job submissions!"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in start_command: {e}")

async def quickpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick post command - direct channel posting with approval"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📝 *Quick Job Post*\n\n"
                "Usage: /quickpost [Job Title] - [Brief Description]\n\n"
                "Example:\n"
                "/quickpost Senior Developer - Python expert needed for remote work. $80k-120k. Apply: email@company.com",
                parse_mode='Markdown'
            )
            return
        
        job_text = ' '.join(context.args)
        user = update.effective_user
        
        # Create approval message for admin channel
        approval_message = (
            f"🆕 JOB SUBMISSION FOR APPROVAL\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 From: {user.first_name} (@{user.username})\n"
            f"📋 Job: {job_text}\n"
            f"🕒 Submitted: {update.message.date}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Create approval buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{update.message.message_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}_{update.message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store job data for approval
        pending_approvals[f"{user.id}_{update.message.message_id}"] = {
            'job_text': job_text,
            'user': user,
            'message_id': update.message.message_id
        }
        
        # Send to admin channel for approval
        await context.bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=approval_message,
            reply_markup=reply_markup
        )
        
        await update.message.reply_text(
            "✅ *Job submitted for approval!*\n\n"
            "Your job post has been sent to our admin team for review. "
            "We'll notify you once it's approved and posted on @hiringet.\n\n"
            "For detailed job posting with more options, use /postajob",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in quickpost_command: {e}")
        await update.message.reply_text("❌ Error submitting job. Please try again.")

async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection callback from admin"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, user_id, message_id = data.split('_')
    user_id = int(user_id)
    message_id = int(message_id)
    
    job_key = f"{user_id}_{message_id}"
    job_data = pending_approvals.get(job_key)
    
    if not job_data:
        await query.edit_message_text("❌ Job submission not found or already processed.")
        return
    
    if action == 'approve':
        # Post to main channel
        channel_message = (
            f"🏢 *Job Opportunity*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{job_data['job_text']}\n\n"
            f"💼 Posted via @help_bot\n"
            f"🔗 Quick apply: https://t.me/help_bot?start=apply"
        )
        
        try:
            await context.bot.send_message(
                chat_id=MAIN_CHANNEL_ID,
                text=channel_message,
                parse_mode='Markdown'
            )
            
            # Notify user
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 *Your job has been approved and posted!*\n\n"
                     f"Your job is now live on {MAIN_CHANNEL_ID}\n\n"
                     "View it here: [Link to channel]",
                parse_mode='Markdown'
            )
            
            # Update admin message
            await query.edit_message_text(
                f"✅ APPROVED AND POSTED\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Job posted to {MAIN_CHANNEL_ID}\n"
                f"User notified successfully"
            )
            
        except Exception as e:
            logger.error(f"Error posting to channel: {e}")
            await query.edit_message_text("❌ Error posting to channel.")
    
    elif action == 'reject':
        # Notify user of rejection
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ *Job Post Not Approved*\n\n"
                     "Your job submission was not approved. "
                     "Please ensure your post follows our guidelines and try again.\n\n"
                     "For assistance, contact @hiringet admin.",
                parse_mode='Markdown'
            )
            
            # Update admin message
            await query.edit_message_text(
                f"❌ JOB REJECTED\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"User has been notified\n"
                f"Job was not posted"
            )
            
        except Exception as e:
            logger.error(f"Error notifying user of rejection: {e}")
            await query.edit_message_text("❌ Error notifying user.")
    
    # Remove from pending approvals
    if job_key in pending_approvals:
        del pending_approvals[job_key]

async def web_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the web interface link to user"""
    try:
        web_message = (
            "🌐 *Habte Job Portal Web Interface*\n\n"
            "Use our user-friendly web page for easy job posting:\n\n"
            f"👉 {WEB_URL}\n\n"
            "✨ *Features:*\n"
            "• Quick job posting with one click\n"
            "• Direct Telegram integration\n"
            "• Mobile-friendly design\n"
            "• Admin approval system\n\n"
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
            "/quickpost - Quick job post (admin approval)\n"
            "/postajob - Detailed job posting process\n"
            "/makecv - Create a professional CV\n"
            "/web - Get web interface link\n"
            "/help - Show this message\n\n"
            "💡 *Quick Post Example:*\n"
            "/quickpost Senior Developer - Python expert needed. Remote. $80k-120k. Apply: email@company.com\n\n"
            "🌐 *Web Interface:*\n"
            f"{WEB_URL}"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help_command: {e}")

def setup_application():
    """Set up the application with all handlers"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.bot_data['admin_channel_id'] = ADMIN_CHANNEL_ID
    
    # Add conversation handlers
    postajob_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('postajob', postajob_command)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
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
    application.add_handler(CommandHandler('quickpost', quickpost_command))
    application.add_handler(CommandHandler('web', web_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(postajob_conv_handler)
    application.add_handler(makecv_conv_handler)
    
    # Add callback handler for approval buttons
    application.add_handler(CallbackQueryHandler(handle_approval_callback))
    
    return application

# Flask app setup
from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML template with updated buttons
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Habte Job Portal - Post to Telegram</title>
    <style>
        /* ... [Keep all your existing CSS styles] ... */
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
                    placeholder="Example:
🚀 Senior Python Developer Needed!

📍 Remote · 💼 Full-time · 💰 $80k-120k

• 3+ years Python experience
• Django/Flask framework
• PostgreSQL knowledge

👉 Apply: careers@company.com"
                ></textarea>
            </div>

            <div class="button-grid">
                <a href="https://t.me/help_bot?start=quickpost" class="telegram-btn post-btn" target="_blank">
                    <i class="fab fa-telegram"></i>
                    Quick Post Job
                </a>
                
                <a href="https://t.me/help_bot?start=makecv" class="telegram-btn cv-btn" target="_blank">
                    <i class="fas fa-file-alt"></i>
                    Create CV
                </a>
                
                <button onclick="copyJobText()" class="telegram-btn copy-btn">
                    <i class="fas fa-copy"></i>
                    Copy Job Text
                </button>

                <a href="https://t.me/help_bot?start=postajob" class="telegram-btn" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); grid-column: span 2;">
                    <i class="fas fa-list-alt"></i>
                    Detailed Job Post (More Options)
                </a>
            </div>

            <div id="successMessage" class="success-message">
                <i class="fas fa-check-circle"></i>
                Job text copied to clipboard!
            </div>

            <div class="instructions">
                <h3>📋 How to Use:</h3>
                <ol>
                    <li>Paste your job post in the text area</li>
                    <li>Click "Copy Job Text" to copy it</li>
                    <li>Click "Quick Post Job" for fast submission (admin approval required)</li>
                    <li>Click "Detailed Job Post" for more options and step-by-step process</li>
                    <li>All jobs are reviewed before appearing on @hiringet</li>
                </ol>
                
                <p style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 5px;">
                    <strong>💡 Note:</strong> Quick posts require admin approval. 
                    For immediate posting privileges, contact @hiringet admin.
                </p>
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
        import asyncio
        asyncio.run(set_webhook())
        logger.info("Webhook mode started")
    else:
        logger.info("Development mode - web interface only")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
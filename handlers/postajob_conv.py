from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import database as db

# Conversation states
TITLE, DESCRIPTION, CONTACT = range(3)

async def postajob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠️ Let's create a job post for @hiringet!\n\nWhat is the job title? (e.g., 'Senior Software Engineer')",
        reply_markup=ReplyKeyboardRemove()
    )
    return TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text(
        "📝 Great! Now please provide the full job description:\n\n- Responsibilities\n- Requirements\n- Benefits"
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text(
        "📧 How should applicants apply? Please provide:\n- Email address\n- Application link\n- Or other contact method"
    )
    return CONTACT

async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    contact_info = update.message.text
    
    # Save to database
    db.add_job_submission(
        user_id=update.effective_user.id,
        title=user_data['title'],
        description=user_data['description'],
        contact_info=contact_info
    )
    
    # Format message for admin review
    admin_message = f"""
    🆕 JOB SUBMISSION FOR @HIRINGET
    ━━━━━━━━━━━━━━━━━━━━━
    👤 Submitted by: @{update.effective_user.username} ({update.effective_user.id})
    📋 Title: {user_data['title']}
    📝 Description: {user_data['description']}
    📧 Contact: {contact_info}
    """
    
    # Send to admin channel (you'll set this in environment variables)
    admin_channel_id = context.bot_data.get('admin_channel_id')
    if admin_channel_id:
        await context.bot.send_message(chat_id=admin_channel_id, text=admin_message)
    
    await update.message.reply_text(
        "✅ Thank you! Your job post has been submitted for review. "
        "Our team at @hiringet will review it and post it soon.\n\n"
        "Need help with your CV? Type /makecv"
    )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Job posting cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import database as db
import json

# Conversation states
FULL_NAME, HEADLINE, SKILLS, EXPERIENCE = range(4)

async def makecv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 Let's create your professional CV!\n\nWhat is your full name?",
        reply_markup=ReplyKeyboardRemove()
    )
    return FULL_NAME

async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text(
        "🎯 What's your professional headline?\n(e.g., 'Senior Software Engineer | Python & Django Expert')"
    )
    return HEADLINE

async def receive_headline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['headline'] = update.message.text
    await update.message.reply_text(
        "🛠️ List your key skills (separated by commas):\n(e.g., 'Python, JavaScript, Django, React, PostgreSQL')"
    )
    return SKILLS

async def receive_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skills = [skill.strip() for skill in update.message.text.split(',')]
    context.user_data['skills'] = skills
    await update.message.reply_text(
        "💼 Describe your work experience:\n\n- Previous roles\n- Projects\n- Achievements"
    )
    return EXPERIENCE

async def receive_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    experience = update.message.text
    
    # Save to database
    db.add_cv_draft(
        user_id=update.effective_user.id,
        full_name=user_data['full_name'],
        headline=user_data['headline'],
        skills=user_data['skills'],
        experience=experience
    )
    
    # Format the CV
    skills_text = '\n'.join([f'• {skill}' for skill in user_data['skills']])
    
    cv_text = f"""
    📄 PROFESSIONAL CV - {user_data['full_name']}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🎯 {user_data['headline']}
    
    🛠️ SKILLS:
    {skills_text}
    
    💼 EXPERIENCE:
    {experience}
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Generated via @hiringet Job Portal
    """
    
    await update.message.reply_text(
        "✅ Your CV has been generated!\n\n"
        "You can copy the text below and use it for job applications:"
    )
    
    await update.message.reply_text(cv_text)
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "CV creation cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

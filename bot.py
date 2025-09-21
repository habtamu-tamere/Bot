import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ConversationHandler
from handlers.postajob_conv import *
from handlers.makecv_conv import *

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHANNEL_ID = os.getenv('ADMIN_CHANNEL_ID')

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
    
    application.add_handler(postajob_conv_handler)
    application.add_handler(makecv_conv_handler)
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()

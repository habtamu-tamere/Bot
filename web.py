import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

class WebHandler:
    def __init__(self):
        self.web_url = os.getenv('WEB_URL')
    
    async def send_web_interface(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.web_url:
            await update.message.reply_text("Web interface not configured.")
            return
        
        message = (
            "🎯 *Habte Job Portal Web Interface*\n\n"
            "Access our user-friendly web page to:\n"
            "• Easily compose job posts\n• Copy text to clipboard\n• Quick-start bot commands\n• Mobile-friendly design\n\n"
            f"👉 {self.web_url}\n\n"
            "Share this link with other employers!"
        )
        await update.message.reply_text(message, parse_mode='Markdown')

# Initialize and add to your bot
web_handler = WebHandler()
application.add_handler(CommandHandler('web', web_handler.send_web_interface))
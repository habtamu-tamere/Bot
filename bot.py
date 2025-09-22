import os
import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)
import sqlite3

from config import Config
from database import Database

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_TIER, SELECTING_ADDONS, ENTERING_CONTACT, ENTERING_BUSINESS, SPECIAL_REQUESTS, CONFIRM_ORDER = range(6)

# Database instance
db = Database()

class SocialMediaBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("order", self.start_order))
        
        # Conversation handler for ordering process
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('order', self.start_order)],
            states={
                SELECTING_TIER: [CallbackQueryHandler(self.select_tier, pattern='^tier_')],
                SELECTING_ADDONS: [CallbackQueryHandler(self.select_addons, pattern='^addon_|^proceed_')],
                ENTERING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_contact)],
                ENTERING_BUSINESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_business)],
                SPECIAL_REQUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.special_requests)],
                CONFIRM_ORDER: [CallbackQueryHandler(self.confirm_order, pattern='^confirm_|^cancel_')]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_order)]
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.button_click))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when command /start is issued."""
        user = update.message.from_user
        welcome_text = f"""
👋 *Welcome to Social Media Pro ET*, {user.first_name}!

📱 *Professional Social Media Management Services*
*📍 Serving Ethiopian Businesses*
*💰 Prices in Ethiopian Birr*

*Quick Commands:*
/order - 🛒 Start new order
/services - 📊 View service packages
/help - ❓ Get assistance

*Why Choose Us?*
✅ Ethiopian Market Expertise
✅ Affordable Pricing in ETB
✅ Professional Content Creation
✅ 24/7 Customer Support

*Start your order with* /order
        """
        
        keyboard = [
            [InlineKeyboardButton("🛒 Start Order", callback_data="start_order")],
            [InlineKeyboardButton("📊 View Services", callback_data="view_services")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help information."""
        help_text = """
*🤖 How to Use This Bot:*

*1. Start Order*
Use /order or click "Start Order" to begin

*2. Choose Service Tier*
Select from Basic, Professional, or Enterprise packages

*3. Select Add-ons*
Customize with additional services

*4. Provide Details*
Share your contact and business information

*5. Confirm Order*
Review and confirm your order

*Need Help?*
Contact our support team directly through this bot or visit our channel: {channel}
        """.format(channel=Config.TELEGRAM_CHANNEL)
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def start_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the order process."""
        query = update.callback_query
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        # Clear any existing user data
        context.user_data.clear()
        
        # Show service tiers
        keyboard = []
        for tier_key, tier in Config.SERVICE_TIERS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{tier['name']} - {tier['price']} ETB/month", 
                    callback_data=f"tier_{tier_key}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
*📊 Choose Your Service Package*

Please select one of our service tiers:

*Basic Package* - 2,500 ETB/month
*Professional Package* - 5,000 ETB/month  
*Enterprise Package* - 10,000 ETB/month

Click on your preferred package to continue.
        """
        
        await message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return SELECTING_TIER
    
    async def select_tier(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle tier selection."""
        query = update.callback_query
        await query.answer()
        
        tier_key = query.data.replace('tier_', '')
        context.user_data['selected_tier'] = tier_key
        context.user_data['selected_addons'] = []
        
        tier = Config.SERVICE_TIERS[tier_key]
        
        # Show add-on options
        keyboard = []
        for addon_key, addon in Config.ADDON_SERVICES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{addon['name']} (+{addon['price']} ETB)", 
                    callback_data=f"addon_{addon_key}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("✅ Proceed to Contact Info", callback_data="proceed_contact")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Packages", callback_data="back_to_tiers")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
*{tier['name']} Selected* - {tier['price']} ETB/month

*Package Features:*
{chr(10).join(tier['features'])}

*💎 Optional Add-on Services:*
You can enhance your package with these additional services:
        """
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return SELECTING_ADDONS
    
    async def select_addons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle add-on selection."""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('proceed_'):
            return await self.enter_contact_info(update, context)
        elif query.data == 'back_to_tiers':
            return await self.start_order(update, context)
        
        addon_key = query.data.replace('addon_', '')
        selected_addons = context.user_data.get('selected_addons', [])
        
        if addon_key in selected_addons:
            selected_addons.remove(addon_key)
        else:
            selected_addons.append(addon_key)
        
        context.user_data['selected_addons'] = selected_addons
        
        # Update the message with current selection
        tier_key = context.user_data['selected_tier']
        tier = Config.SERVICE_TIERS[tier_key]
        
        total_price = tier['price']
        addons_text = []
        
        for addon_key in selected_addons:
            addon = Config.ADDON_SERVICES[addon_key]
            total_price += addon['price']
            addons_text.append(f"✅ {addon['name']} (+{addon['price']} ETB)")
        
        keyboard = []
        for addon_key, addon in Config.ADDON_SERVICES.items():
            status = "✅" if addon_key in selected_addons else "◻️"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {addon['name']} (+{addon['price']} ETB)", 
                    callback_data=f"addon_{addon_key}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("✅ Proceed to Contact Info", callback_data="proceed_contact")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Packages", callback_data="back_to_tiers")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
*{tier['name']} Selected* - {tier['price']} ETB/month

*Selected Add-ons:*
{chr(10).join(addons_text) if addons_text else 'No add-ons selected'}

*💰 Total Monthly Price: {total_price} ETB*

*Optional Add-on Services:*
        """
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return SELECTING_ADDONS
    
    async def enter_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt for contact information."""
        query = update.callback_query
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        # Create contact sharing button
        contact_keyboard = [[KeyboardButton("📱 Share Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        text = """
*📞 Contact Information*

Please share your phone number using the button below, or type it manually.

Format: +251 XXX XXX XXX or 09XXXXXXXX
        """
        
        await message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return ENTERING_CONTACT
    
    async def enter_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save contact information."""
        if update.message.contact:
            phone = update.message.contact.phone_number
        else:
            phone = update.message.text
        
        context.user_data['phone'] = phone
        
        # Remove the contact keyboard
        remove_keyboard = ReplyKeyboardMarkup([[KeyboardButton("Remove")]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "✅ Phone number saved!\n\nNow, please tell us your business name:",
            reply_markup=remove_keyboard
        )
        
        return ENTERING_BUSINESS
    
    async def enter_business(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save business information."""
        business_name = update.message.text
        context.user_data['business_name'] = business_name
        
        text = """
*💼 Special Requests*

Do you have any specific requirements or special requests for your social media management?

Examples:
- Target audience details
- Preferred content style
- Specific platforms focus
- Campaign goals

Type your requests or type 'None' if you don't have any special requirements.
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return SPECIAL_REQUESTS
    
    async def special_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save special requests and show order summary."""
        special_requests = update.message.text
        context.user_data['special_requests'] = special_requests
        
        # Calculate total price
        tier_key = context.user_data['selected_tier']
        tier = Config.SERVICE_TIERS[tier_key]
        total_price = tier['price']
        
        selected_addons = context.user_data.get('selected_addons', [])
        addons_text = []
        
        for addon_key in selected_addons:
            addon = Config.ADDON_SERVICES[addon_key]
            total_price += addon['price']
            addons_text.append(f"• {addon['name']} (+{addon['price']} ETB)")
        
        # Create order summary
        text = f"""
*📋 Order Summary*

*Service Package:*
{tier['name']} - {tier['price']} ETB/month

*Add-on Services:*
{chr(10).join(addons_text) if addons_text else 'None'}

*Business Name:*
{context.user_data['business_name']}

*Special Requests:*
{special_requests}

*💰 Total Monthly Price: {total_price} ETB*

Please review your order and confirm below.
        """
        
        context.user_data['total_price'] = total_price
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Order", callback_data="confirm_order")],
            [InlineKeyboardButton("🔙 Edit Order", callback_data="edit_order")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return CONFIRM_ORDER
    
    async def confirm_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finalize the order."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'cancel_order':
            await query.edit_message_text("❌ Order cancelled. Use /order to start a new order when you're ready.")
            return ConversationHandler.END
        
        user = query.from_user
        
        # Save order to database
        order_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': context.user_data['phone'],
            'business_name': context.user_data['business_name'],
            'selected_tier': context.user_data['selected_tier'],
            'selected_addons': context.user_data.get('selected_addons', []),
            'total_price': context.user_data['total_price'],
            'special_requests': context.user_data['special_requests']
        }
        
        order_id = db.create_order(order_data)
        
        # Send confirmation to user
        user_text = f"""
*✅ Order Confirmed!*

Thank you for your order! Here are your order details:

*Order ID:* #{order_id}
*Service:* {Config.SERVICE_TIERS[order_data['selected_tier']]['name']}
*Total Price:* {order_data['total_price']} ETB/month

*Next Steps:*
1. Our team will contact you within 24 hours
2. We'll discuss your requirements in detail
3. Service setup and onboarding

*Contact Support:* Use this bot or visit our channel: {Config.TELEGRAM_CHANNEL}
        """
        
        await query.edit_message_text(user_text, parse_mode='Markdown')
        
        # Send notification to admin (you)
        admin_text = f"""
*🆕 NEW ORDER RECEIVED!*

*Order ID:* #{order_id}
*Customer:* {user.first_name} {user.last_name or ''} (@{user.username or 'N/A'})
*Business:* {order_data['business_name']}
*Phone:* {order_data['phone']}
*Package:* {Config.SERVICE_TIERS[order_data['selected_tier']]['name']}
*Total:* {order_data['total_price']} ETB/month
*Add-ons:* {', '.join(order_data['selected_addons']) or 'None'}

*Special Requests:*
{order_data['special_requests']}
        """
        
        # In a real scenario, you'd send this to your admin chat
        # await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode='Markdown')
        
        print(f"NEW ORDER: {admin_text}")  # For now, print to console
        
        return ConversationHandler.END
    
    async def cancel_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the order process."""
        await update.message.reply_text(
            "Order process cancelled. Use /order to start again when you're ready!"
        )
        return ConversationHandler.END
    
    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'view_services':
            await self.show_services(query)
        elif query.data == 'contact_support':
            await query.edit_message_text(
                f"📞 *Contact Support*\n\nFor support, please message us directly or visit our channel: {Config.TELEGRAM_CHANNEL}",
                parse_mode='Markdown'
            )
        elif query.data == 'start_order':
            await self.start_order(update, context)
    
    async def show_services(self, query):
        """Show all available services."""
        text = """
*📊 Our Service Packages*

*Basic Package - 2,500 ETB/month*
• 2 Social Media Platforms
• 5 Posts per week
• Basic Analytics
• Content Creation
• 24/7 Support

*Professional Package - 5,000 ETB/month*
• 4 Social Media Platforms  
• 10 Posts per week
• Advanced Analytics
• Content Strategy
• Ad Management
• Monthly Reports
• Priority Support

*Enterprise Package - 10,000 ETB/month*
• All Social Media Platforms
• 15+ Posts per week
• Competitor Analysis
• Custom Strategy
• Full Ad Campaigns
• Weekly Reports
• Dedicated Account Manager
• 24/7 Premium Support

*💎 Add-on Services:*
• Video Content Creation: +1,000 ETB
• Advanced Analytics: +500 ETB  
• SEO Optimization: +750 ETB
• Emergency Support: +1,500 ETB

*Start your order with* /order
        """
        
        keyboard = [[InlineKeyboardButton("🛒 Start Order", callback_data="start_order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

def main():
    """Start the bot."""
    # Create bot instance
    bot_token = os.getenv('BOT_TOKEN', Config.BOT_TOKEN)
    
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Please set your BOT_TOKEN environment variable!")
        return
    
    bot = SocialMediaBot(bot_token)
    
    # Start the Bot
    print("🤖 Bot is starting...")
    bot.application.run_polling()

if __name__ == '__main__':
    main()
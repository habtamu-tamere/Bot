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
import json
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_TIER, SELECTING_ADDONS, ENTERING_CONTACT, ENTERING_BUSINESS, SPECIAL_REQUESTS, CONFIRM_ORDER = range(6)

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    ADMIN_CHANNEL = os.getenv('ADMIN_CHANNEL', '@your_admin_channel')  # Your channel username
    SUPPORT_CHAT = os.getenv('SUPPORT_CHAT', '@your_support_chat')  # Support group/chat
    
    SERVICE_TIERS = {
        'basic': {
            'name': '📊 Basic Package',
            'price': 2500,
            'description': 'Perfect for small businesses starting their social media journey',
            'features': [
                '✅ 2 Social Media Platforms',
                '✅ 5 Posts per week',
                '✅ Basic Analytics',
                '✅ Content Creation',
                '✅ 24/7 Support'
            ]
        },
        'professional': {
            'name': '🚀 Professional Package',
            'price': 5000,
            'description': 'Ideal for growing businesses needing comprehensive management',
            'features': [
                '✅ 4 Social Media Platforms',
                '✅ 10 Posts per week',
                '✅ Advanced Analytics',
                '✅ Content Strategy',
                '✅ Ad Management',
                '✅ Monthly Reports',
                '✅ Priority Support'
            ]
        },
        'enterprise': {
            'name': '🏆 Enterprise Package',
            'price': 10000,
            'description': 'Complete solution for established businesses',
            'features': [
                '✅ All Social Media Platforms',
                '✅ 15+ Posts per week',
                '✅ Competitor Analysis',
                '✅ Custom Strategy',
                '✅ Full Ad Campaigns',
                '✅ Weekly Reports',
                '✅ Dedicated Account Manager',
                '✅ 24/7 Premium Support'
            ]
        }
    }
    
    ADDON_SERVICES = {
        'video': {'name': '🎥 Video Content', 'price': 1000},
        'analytics': {'name': '📈 Advanced Analytics', 'price': 500},
        'seo': {'name': '🔍 SEO Optimization', 'price': 750},
        'emergency': {'name': '🚨 24/7 Emergency Support', 'price': 1500}
    }

class Database:
    def __init__(self, db_name='orders.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                business_name TEXT,
                selected_tier TEXT,
                selected_addons TEXT,
                total_price INTEGER,
                special_requests TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                admin_notified INTEGER DEFAULT 0
            )
        ''')
        
        # Create FAQ table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                category TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        self.insert_sample_faq()
    
    def insert_sample_faq(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        faqs = [
            ("What's included in the Basic package?", "The Basic package includes management of 2 social media platforms, 5 posts per week, basic analytics, content creation, and 24/7 support.", "packages"),
            ("How long does setup take?", "Setup typically takes 1-2 business days after we receive all necessary access and information.", "general"),
            ("Can I change packages later?", "Yes, you can upgrade or downgrade your package at any time. Changes take effect from the next billing cycle.", "billing"),
            ("Do you create content?", "Yes! We handle content creation including graphics, captions, and scheduling for all packages.", "services"),
            ("What platforms do you support?", "We support Facebook, Instagram, Twitter/X, LinkedIn, TikTok, and Telegram.", "services"),
            ("How do I pay?", "We accept bank transfers, mobile banking (CBE Birr, Telebirr), and cash payments.", "billing"),
            ("Can I cancel anytime?", "Yes, you can cancel with 30 days notice. No long-term contracts required.", "billing")
        ]
        
        cursor.execute('SELECT COUNT(*) FROM faq')
        if cursor.fetchone()[0] == 0:
            cursor.executemany('''
                INSERT INTO faq (question, answer, category) VALUES (?, ?, ?)
            ''', faqs)
        
        conn.commit()
        conn.close()
    
    def create_order(self, order_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (
                user_id, username, first_name, last_name, phone, 
                business_name, selected_tier, selected_addons, 
                total_price, special_requests
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data['user_id'],
            order_data['username'],
            order_data['first_name'],
            order_data['last_name'],
            order_data['phone'],
            order_data['business_name'],
            order_data['selected_tier'],
            json.dumps(order_data['selected_addons']),
            order_data['total_price'],
            order_data['special_requests']
        ))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    
    def mark_admin_notified(self, order_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET admin_notified = 1 WHERE id = ?', (order_id,))
        conn.commit()
        conn.close()
    
    def get_faq_by_category(self, category=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT question, answer FROM faq WHERE category = ? AND is_active = 1', (category,))
        else:
            cursor.execute('SELECT question, answer, category FROM faq WHERE is_active = 1')
        
        faqs = cursor.fetchall()
        conn.close()
        return faqs

class SocialMediaBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.db = Database()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("order", self.start_order))
        self.application.add_handler(CommandHandler("services", self.show_services_command))
        self.application.add_handler(CommandHandler("faq", self.faq_command))
        self.application.add_handler(CommandHandler("support", self.support_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        
        # Conversation handler for ordering process
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('order', self.start_order)],
            states={
                SELECTING_TIER: [CallbackQueryHandler(self.select_tier, pattern='^tier_')],
                SELECTING_ADDONS: [CallbackQueryHandler(self.select_addons, pattern='^addon_|^proceed_|^back_')],
                ENTERING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_contact),
                                 MessageHandler(filters.CONTACT, self.enter_contact_shared)],
                ENTERING_BUSINESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_business)],
                SPECIAL_REQUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.special_requests)],
                CONFIRM_ORDER: [CallbackQueryHandler(self.confirm_order, pattern='^confirm_|^cancel_|^edit_')]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_order)],
            allow_reentry=True
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.button_click))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when command /start is issued."""
        user = update.message.from_user
        
        welcome_text = f"""
👋 *Welcome to Social Media Pro ET*, {user.first_name}!

📱 *Professional Social Media Management Services*
📍 *Serving Ethiopian Businesses*
💰 *Prices in Ethiopian Birr*

*Quick Commands:*
/order - 🛒 Start new order
/services - 📊 View service packages
/faq - ❓ Frequently Asked Questions  
/support - 🆘 Get immediate help
/contact - 📞 Contact admin directly

*Why Choose Us?*
✅ Ethiopian Market Expertise
✅ Affordable Pricing in ETB
✅ Professional Content Creation
✅ 24/7 Customer Support

*Start your order with* `/order` or explore our services with `/services`
        """
        
        keyboard = [
            [InlineKeyboardButton("🛒 Start Order", callback_data="start_order"),
             InlineKeyboardButton("📊 View Services", callback_data="view_services")],
            [InlineKeyboardButton("❓ FAQ", callback_data="view_faq"),
             InlineKeyboardButton("🆘 Support", callback_data="get_support")],
            [InlineKeyboardButton("📞 Contact Admin", callback_data="contact_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help information."""
        help_text = f"""
*🤖 How to Use This Bot:*

*1. Browse Services*  
Use `/services` to see all packages and pricing

*2. Start Order*
Use `/order` for step-by-step ordering process

*3. Get Help*
- `/faq` - Frequently Asked Questions
- `/support` - Immediate assistance
- `/contact` - Direct admin contact

*4. Order Process:*
• Choose service tier
• Select add-ons
• Provide contact info
• Confirm order

*Need Immediate Help?*
Contact support: {Config.SUPPORT_CHAT}
        """
        
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
                    f"{tier['name']} - {tier['price']:,} ETB/month", 
                    callback_data=f"tier_{tier_key}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
*📊 Choose Your Service Package*

Please select one of our service tiers:

*Basic* - 2,500 ETB/month | *Professional* - 5,000 ETB/month | *Enterprise* - 10,000 ETB/month

Click on your preferred package to continue.
        """
        
        if query:
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
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
                    f"{addon['name']} (+{addon['price']:,} ETB)", 
                    callback_data=f"addon_{addon_key}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("✅ Proceed to Contact", callback_data="proceed_contact")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Packages", callback_data="back_to_tiers")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
*{tier['name']} Selected* - {tier['price']:,} ETB/month

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
        
        if query.data == 'proceed_contact':
            return await self.enter_contact_info(update, context)
        elif query.data == 'back_to_tiers':
            return await self.start_order(update, context)
        elif query.data == 'cancel_order':
            return await self.cancel_order(update, context)
        
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
            addons_text.append(f"✅ {addon['name']} (+{addon['price']:,} ETB)")
        
        keyboard = []
        for addon_key, addon in Config.ADDON_SERVICES.items():
            status = "✅" if addon_key in selected_addons else "◻️"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {addon['name']} (+{addon['price']:,} ETB)", 
                    callback_data=f"addon_{addon_key}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("✅ Proceed to Contact", callback_data="proceed_contact")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Packages", callback_data="back_to_tiers")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
*{tier['name']} Selected* - {tier['price']:,} ETB/month

*Selected Add-ons:*
{chr(10).join(addons_text) if addons_text else 'No add-ons selected'}

*💰 Total Monthly Price: {total_price:,} ETB*

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

*Format:* +251 XXX XXX XXX or 09XXXXXXXX

This helps us contact you to discuss your order details.
        """
        
        if query:
            await query.edit_message_text(text, parse_mode='Markdown')
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Please share your phone number:",
                reply_markup=reply_markup
            )
        else:
            await message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
        return ENTERING_CONTACT
    
    async def enter_contact_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared contact."""
        phone = update.message.contact.phone_number
        context.user_data['phone'] = phone
        
        await self.enter_business_prompt(update, context)
        return ENTERING_BUSINESS
    
    async def enter_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save manually entered contact information."""
        phone = update.message.text
        context.user_data['phone'] = phone
        
        await self.enter_business_prompt(update, context)
        return ENTERING_BUSINESS
    
    async def enter_business_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt for business information."""
        # Remove the contact keyboard
        remove_keyboard = ReplyKeyboardRemove()
        await update.message.reply_text(
            "✅ *Phone number saved!*\n\nNow, please tell us your *business name*:",
            parse_mode='Markdown',
            reply_markup=remove_keyboard
        )
    
    async def enter_business(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save business information."""
        business_name = update.message.text
        context.user_data['business_name'] = business_name
        
        text = """
*💼 Special Requests & Requirements*

Do you have any specific requirements for your social media management?

*Examples:*
- Target audience details
- Preferred content style (formal/casual)
- Specific platforms to focus on
- Campaign goals or KPIs
- Brand guidelines

Type your requests or type *'None'* if no special requirements.
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return SPECIAL_REQUESTS
    
    async def special_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save special requests and show order summary."""
        special_requests = update.message.text
        if special_requests.lower() == 'none':
            special_requests = 'No special requirements'
        
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
            addons_text.append(f"• {addon['name']} (+{addon['price']:,} ETB)")
        
        # Create order summary
        text = f"""
*📋 Order Summary - Please Review*

*Service Package:*
{tier['name']} - {tier['price']:,} ETB/month

*Add-on Services:*
{chr(10).join(addons_text) if addons_text else '• None selected'}

*Business Name:*
{context.user_data['business_name']}

*Special Requests:*
{special_requests}

*💰 Total Monthly Price: {total_price:,} ETB*

*✅ Please confirm your order below. Our team will contact you within 24 hours.*
        """
        
        context.user_data['total_price'] = total_price
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm & Submit Order", callback_data="confirm_order")],
            [InlineKeyboardButton("🔙 Edit Add-ons", callback_data="back_to_addons"),
             InlineKeyboardButton("🔙 Edit Package", callback_data="back_to_tiers")],
            [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return CONFIRM_ORDER
    
    async def confirm_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finalize the order."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'cancel_order':
            await query.edit_message_text("❌ *Order cancelled.* Use `/order` to start a new order when you're ready.", parse_mode='Markdown')
            return ConversationHandler.END
        elif query.data in ['back_to_addons', 'back_to_tiers']:
            if query.data == 'back_to_addons':
                return await self.select_tier(update, context)
            else:
                return await self.start_order(update, context)
        
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
        
        order_id = self.db.create_order(order_data)
        
        # Send confirmation to user
        user_text = f"""
*🎉 Order Submitted Successfully!*

*Order ID:* #{order_id}
*Service Package:* {Config.SERVICE_TIERS[order_data['selected_tier']]['name']}
*Total Monthly:* {order_data['total_price']:,} ETB

*📞 What Happens Next:*
1. Our team will contact you within *24 hours* at {order_data['phone']}
2. We'll discuss your requirements in detail
3. Service setup and platform access
4. Onboarding session

*Need immediate assistance?*
Contact support: {Config.SUPPORT_CHAT}

Thank you for choosing Social Media Pro ET! 🚀
        """
        
        await query.edit_message_text(user_text, parse_mode='Markdown')
        
        # Send notification to admin channel
        await self.send_admin_notification(order_id, order_data, user)
        
        return ConversationHandler.END
    
    async def send_admin_notification(self, order_id, order_data, user):
        """Send order notification to admin channel."""
        try:
            tier = Config.SERVICE_TIERS[order_data['selected_tier']]
            addons_text = ""
            
            if order_data['selected_addons']:
                addons_text = "\n*Add-ons:*\n" + "\n".join([
                    f"• {Config.ADDON_SERVICES[addon]['name']} (+{Config.ADDON_SERVICES[addon]['price']:,} ETB)"
                    for addon in order_data['selected_addons']
                ])
            
            admin_text = f"""
🚨 *NEW ORDER RECEIVED* 🚨

*Order ID:* #{order_id}
*Customer:* {user.first_name} {user.last_name or ''} (@{user.username or 'No username'})
*Business:* {order_data['business_name']}
*Phone:* {order_data['phone']}

*Service Package:*
{tier['name']} - {tier['price']:,} ETB/month
{addons_text}

*Total Monthly:* {order_data['total_price']:,} ETB

*Special Requests:*
{order_data['special_requests']}

*Customer Info:*
User ID: {user.id}
Username: @{user.username or 'N/A'}
Name: {user.first_name} {user.last_name or ''}

*Action Required:* Contact customer within 24 hours
            """
            
            # Send to admin channel (you'll need to handle this properly)
            # For now, we'll log it and you can set up proper channel integration
            logger.info(f"NEW ORDER: {admin_text}")
            
            # If you have a channel ID, uncomment and use:
            # await self.application.bot.send_message(
            #     chat_id=Config.ADMIN_CHANNEL,
            #     text=admin_text,
            #     parse_mode='Markdown'
            # )
            
            self.db.mark_admin_notified(order_id)
            
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")
    
    async def cancel_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the order process."""
        if update.message:
            await update.message.reply_text(
                "❌ Order process cancelled. Use `/order` to start again when you're ready!",
                parse_mode='Markdown'
            )
        return ConversationHandler.END
    
    async def show_services_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show services via command."""
        await self.show_services(update.message)
    
    async def show_services(self, message):
        """Show all available services."""
        text = """
*📊 Our Service Packages - Prices in ETB*

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

*Ready to order?* Use `/order` to get started!
        """
        
        keyboard = [[InlineKeyboardButton("🛒 Start Order", callback_data="start_order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def faq_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show FAQ categories."""
        keyboard = [
            [InlineKeyboardButton("📦 Packages", callback_data="faq_packages"),
             InlineKeyboardButton("💰 Billing", callback_data="faq_billing")],
            [InlineKeyboardButton("🛠️ Services", callback_data="faq_services"),
             InlineKeyboardButton("❓ General", callback_data="faq_general")],
            [InlineKeyboardButton("🛒 Start Order", callback_data="start_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
*❓ Frequently Asked Questions*

Choose a category to browse FAQs, or use `/order` to start your service request.
        """
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Provide support information."""
        text = f"""
*🆘 Customer Support*

*Immediate Assistance:*
- Support Chat: {Config.SUPPORT_CHAT}
- Email: support@yourdomain.com
- Phone: +251 XXX XXX XXX

*Business Hours:*
Monday-Friday: 8:00 AM - 6:00 PM EAT
Saturday: 9:00 AM - 2:00 PM EAT

*Emergency Support:*
Available 24/7 for enterprise customers

*Before contacting support, check* `/faq` *for quick answers.*
        """
        
        keyboard = [
            [InlineKeyboardButton("❓ FAQ", callback_data="view_faq"),
             InlineKeyboardButton("📞 Contact", callback_data="contact_admin")],
            [InlineKeyboardButton("📊 Services", callback_data="view_services")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct contact information."""
        text = f"""
*📞 Direct Contact Information*

*For Sales & Orders:*
- Telegram: {Config.ADMIN_CHANNEL}
- Phone: +251 XXX XXX XXX
- Email: sales@yourdomain.com

*For Support:*
- Support: {Config.SUPPORT_CHAT}
- Email: support@yourdomain.com

*Office Address:*
[Your physical address in Ethiopia]

*We typically respond within 1-2 hours during business hours.*
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'start_order':
            await self.start_order(update, context)
        elif query.data == 'view_services':
            await self.show_services(query.message)
        elif query.data == 'view_faq':
            await self.faq_command(update, context)
        elif query.data == 'get_support':
            await self.support_command(update, context)
        elif query.data == 'contact_admin':
            await self.contact_command(update, context)
        elif query.data.startswith('faq_'):
            category = query.data.replace('faq_', '')
            await self.show_faq_category(query, category)
    
    async def show_faq_category(self, query, category):
        """Show FAQ for specific category."""
        faqs = self.db.get_faq_by_category(category)
        
        if not faqs:
            text = "No FAQs found for this category."
        else:
            text = f"*❓ {category.title()} FAQs*\n\n"
            for i, (question, answer) in enumerate(faqs, 1):
                text += f"*{i}. {question}*\n{answer}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to FAQ", callback_data="view_faq"),
             InlineKeyboardButton("🛒 Start Order", callback_data="start_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

def main():
    """Start the bot."""
    bot_token = Config.BOT_TOKEN
    
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ERROR: Please set BOT_TOKEN environment variable!")
        print("💡 Get token from @BotFather on Telegram")
        return
    
    try:
        bot = SocialMediaBot(bot_token)
        print("🤖 Bot is starting...")
        print("✅ Services: Loaded")
        print("✅ Database: Initialized")
        print("✅ Handlers: Configured")
        print("🚀 Bot is ready! Press Ctrl+C to stop")
        
        bot.application.run_polling()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("💡 Check your BOT_TOKEN and internet connection")

if __name__ == '__main__':
    main()
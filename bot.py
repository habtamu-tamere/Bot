import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, SERVICE_TIERS, CHANNEL_USERNAME
from database import init_db, save_order, get_order
from keyboards import (
    main_menu_keyboard,
    pricing_tiers_keyboard,
    service_details_keyboard,
    order_confirmation_keyboard,
    payment_methods_keyboard
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
👋 *Welcome to Social Media Management Service!* 🇪🇹

Hello {user.first_name}! I'm here to help you boost your business with professional social media management.

💰 *All prices in Ethiopian Birr (ETB)*
📱 *Direct ordering through this bot*
⚡ *Fast setup within 24 hours*

Choose an option below to get started:
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )

# Show pricing tiers
async def show_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tiers_text = """
📊 *Our Service Packages* 🇪🇹

Choose the package that best fits your business needs:
    """
    
    await update.callback_query.edit_message_text(
        tiers_text,
        reply_markup=pricing_tiers_keyboard(),
        parse_mode='Markdown'
    )

# Show tier details
async def show_tier_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tier_key = query.data.split('_')[1]
    tier = SERVICE_TIERS[tier_key]
    
    features_text = "\n".join([f"✅ {feature}" for feature in tier['features']])
    
    details_text = f"""
🎯 *{tier['name']} - {tier['price']} {tier['currency']}/month*

{tier['description']}

*Includes:*
{features_text}

*Total: {tier['price']} {tier['currency']} per month*
    """
    
    keyboard = service_details_keyboard(tier_key)
    
    await query.edit_message_text(
        details_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Start order process
async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tier_key = query.data.split('_')[1]
    
    # Store tier selection in user context
    context.user_data['selected_tier'] = tier_key
    context.user_data['order_stage'] = 'awaiting_business_info'
    
    order_text = f"""
📝 *Order Form - {SERVICE_TIERS[tier_key]['name']}*

Let's get your order started! Please provide the following information:

1. *Business Name:*
2. *Your Name:*
3. *Phone Number:*
4. *Email Address:*
5. *Social Media Platforms needed* (Facebook, Instagram, Telegram, etc.)

Please send your information in this format:
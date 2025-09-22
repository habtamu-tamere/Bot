import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, ADMIN_CHAT_ID
from messages import *
from keyboards import *
from database import init_db, save_order, get_orders

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize database
init_db()

# Service tiers in Ethiopian Birr
SERVICE_TIERS = {
    'basic': {
        'name': '📱 Basic Package',
        'price': 2500,
        'features': [
            '✅ 2 Social Media Platforms',
            '✅ 5 Posts per week',
            '✅ Basic Analytics',
            '✅ Content Creation',
            '✅ 24/7 Support'
        ]
    },
    'professional': {
        'name': '💼 Professional Package',
        'price': 5000,
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
        'name': '🚀 Enterprise Package',
        'price': 10000,
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
    'analytics': {'name': '📊 Advanced Analytics', 'price': 500},
    'seo': {'name': '🔍 SEO Optimization', 'price': 750},
    'emergency': {'name': '🚨 Emergency Support', 'price': 1500}
}

# User session data
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu"""
    user = update.effective_user
    welcome_text = WELCOME_MESSAGE.format(name=user.first_name)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show service packages"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        SERVICES_MESSAGE,
        reply_markup=services_keyboard(SERVICE_TIERS),
        parse_mode='HTML'
    )

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show details of selected package"""
    query = update.callback_query
    await query.answer()
    
    package_key = query.data.split('_')[1]
    package = SERVICE_TIERS[package_key]
    
    # Store selected package in user session
    user_id = query.from_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]['package'] = package_key
    
    details_text = PACKAGE_DETAILS.format(
        name=package['name'],
        price=package['price'],
        features='\n'.join(package['features'])
    )
    
    await query.edit_message_text(
        details_text,
        reply_markup=package_details_keyboard(package_key),
        parse_mode='HTML'
    )

async def show_addons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show addon services"""
    query = update.callback_query
    await query.answer()
    
    package_key = query.data.split('_')[1]
    
    await query.edit_message_text(
        ADDONS_MESSAGE,
        reply_markup=addons_keyboard(ADDON_SERVICES, package_key),
        parse_mode='HTML'
    )

async def toggle_addon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle addon selection"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    package_key = data_parts[2]
    addon_key = data_parts[3]
    
    user_id = query.from_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = {'addons': set()}
    if 'addons' not in user_sessions[user_id]:
        user_sessions[user_id]['addons'] = set()
    
    # Toggle addon
    if addon_key in user_sessions[user_id]['addons']:
        user_sessions[user_id]['addons'].remove(addon_key)
    else:
        user_sessions[user_id]['addons'].add(addon_key)
    
    # Update message with current selection
    selected_addons = [ADDON_SERVICES[key]['name'] for key in user_sessions[user_id]['addons']]
    selection_text = "Selected: " + ", ".join(selected_addons) if selected_addons else "No addons selected"
    
    message_text = ADDONS_MESSAGE + f"\n\n{selection_text}"
    
    await query.edit_message_text(
        message_text,
        reply_markup=addons_keyboard(ADDON_SERVICES, package_key),
        parse_mode='HTML'
    )

async def calculate_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculate and show total price"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    package_key = data_parts[2]
    
    user_id = query.from_user.id
    package = SERVICE_TIERS[package_key]
    base_price = package['price']
    
    # Calculate addons price
    addons_price = 0
    selected_addons = user_sessions.get(user_id, {}).get('addons', set())
    
    for addon_key in selected_addons:
        addons_price += ADDON_SERVICES[addon_key]['price']
    
    total_price = base_price + addons_price
    
    # Store in session
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]['package'] = package_key
    user_sessions[user_id]['total_price'] = total_price
    
    price_text = PRICE_CALCULATION.format(
        package_name=package['name'],
        base_price=base_price,
        addons_price=addons_price,
        total_price=total_price,
        selected_addons=", ".join([ADDON_SERVICES[key]['name'] for key in selected_addons]) if selected_addons else "None"
    )
    
    await query.edit_message_text(
        price_text,
        reply_markup=order_confirmation_keyboard(),
        parse_mode='HTML'
    )

async def request_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Request contact information"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        CONTACT_REQUEST,
        reply_markup=contact_keyboard(),
        parse_mode='HTML'
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact information"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("Please start over using /start")
        return
    
    # Store contact info
    user_sessions[user_id]['contact_info'] = update.message.text
    user_sessions[user_id]['username'] = update.effective_user.username
    user_sessions[user_id]['user_id'] = user_id
    
    # Confirm order
    await update.message.reply_text(
        ORDER_CONFIRMATION,
        reply_markup=final_confirmation_keyboard(),
        parse_mode='HTML'
    )

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final order confirmation"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = user_sessions.get(user_id, {})
    
    if not session:
        await query.edit_message_text("Session expired. Please start over with /start")
        return
    
    # Save order to database
    order_data = {
        'user_id': user_id,
        'username': session.get('username'),
        'package': session.get('package'),
        'addons': list(session.get('addons', [])),
        'total_price': session.get('total_price', 0),
        'contact_info': session.get('contact_info', ''),
        'status': 'pending'
    }
    
    order_id = save_order(order_data)
    
    # Send confirmation to user
    await query.edit_message_text(
        ORDER_COMPLETE.format(order_id=order_id),
        parse_mode='HTML'
    )
    
    # Send notification to admin
    admin_message = NEW_ORDER_NOTIFICATION.format(
        order_id=order_id,
        username=session.get('username', 'N/A'),
        user_id=user_id,
        package=SERVICE_TIERS[session['package']]['name'],
        total_price=session['total_price'],
        contact_info=session.get('contact_info', 'N/A')
    )
    
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_message,
        parse_mode='HTML'
    )
    
    # Clear user session
    if user_id in user_sessions:
        del user_sessions[user_id]

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show orders"""
    user_id = update.effective_user.id
    
    if str(user_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("This command is for admin only.")
        return
    
    orders = get_orders()
    
    if not orders:
        await update.message.reply_text("No orders yet.")
        return
    
    orders_text = "📋 <b>All Orders:</b>\n\n"
    for order in orders:
        orders_text += f"🆔 Order ID: {order[0]}\n"
        orders_text += f"👤 User: @{order[2] or 'N/A'} (ID: {order[1]})\n"
        orders_text += f"📦 Package: {order[3]}\n"
        orders_text += f"💰 Total: {order[5]} ETB\n"
        orders_text += f"📞 Contact: {order[6]}\n"
        orders_text += f"📅 Date: {order[7]}\n"
        orders_text += f"🔰 Status: {order[8]}\n"
        orders_text += "─" * 30 + "\n"
    
    await update.message.reply_text(orders_text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages"""
    await update.message.reply_text(
        "Please use the menu buttons or type /start to begin."
    )

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("orders", show_orders))
    
    application.add_handler(CallbackQueryHandler(show_services, pattern="^services$"))
    application.add_handler(CallbackQueryHandler(show_package_details, pattern="^package_"))
    application.add_handler(CallbackQueryHandler(show_addons, pattern="^addons_"))
    application.add_handler(CallbackQueryHandler(toggle_addon, pattern="^toggle_"))
    application.add_handler(CallbackQueryHandler(calculate_price, pattern="^calculate_"))
    application.add_handler(CallbackQueryHandler(request_contact, pattern="^order_confirm$"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^final_confirm$"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact))
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
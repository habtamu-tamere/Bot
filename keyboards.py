from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import SERVICE_TIERS

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 View Pricing", callback_data="pricing")],
        [InlineKeyboardButton("📝 Place Order", callback_data="order_direct")],
        [InlineKeyboardButton("🏢 About Us", callback_data="about")],
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/your_username")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pricing_tiers_keyboard():
    keyboard = []
    for tier_key, tier in SERVICE_TIERS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{tier['name']} - {tier['price']} {tier['currency']}", 
                callback_data=f"tier_{tier_key}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

def service_details_keyboard(tier_key):
    keyboard = [
        [InlineKeyboardButton("✅ Order This Package", callback_data=f"order_{tier_key}")],
        [InlineKeyboardButton("🔙 View All Packages", callback_data="pricing")]
    ]
    return InlineKeyboardMarkup(keyboard)

def order_confirmation_keyboard(tier_key):
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Order", callback_data=f"confirm_{tier_key}")],
        [InlineKeyboardButton("✏️ Edit Information", callback_data=f"order_{tier_key}")],
        [InlineKeyboardButton("🔙 Change Package", callback_data="pricing")]
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_methods_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Bank Transfer", callback_data="payment_bank")],
        [InlineKeyboardButton("📱 Mobile Banking", callback_data="payment_mobile")],
        [InlineKeyboardButton("💰 Cash", callback_data="payment_cash")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_order")]
    ]
    return InlineKeyboardMarkup(keyboard)
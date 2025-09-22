# Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
CHANNEL_USERNAME = "your_channel_username"  # Without @

# Service Tiers in Ethiopian Birr
SERVICE_TIERS = {
    'basic': {
        'name': 'Basic Package',
        'price': 2500,
        'currency': 'ETB',
        'features': [
            '2 Social Media Platforms',
            '5 Posts per week',
            'Basic Analytics',
            'Content Creation',
            '24/7 Support'
        ],
        'description': 'Perfect for small businesses starting their social media journey'
    },
    'professional': {
        'name': 'Professional Package',
        'price': 5000,
        'currency': 'ETB',
        'features': [
            '4 Social Media Platforms',
            '10 Posts per week',
            'Advanced Analytics',
            'Content Strategy',
            'Ad Management',
            'Monthly Reports',
            'Priority Support'
        ],
        'description': 'Ideal for growing businesses needing comprehensive management'
    },
    'enterprise': {
        'name': 'Enterprise Package',
        'price': 10000,
        'currency': 'ETB',
        'features': [
            'All Social Media Platforms',
            '15+ Posts per week',
            'Competitor Analysis',
            'Custom Strategy',
            'Full Ad Campaigns',
            'Weekly Reports',
            'Dedicated Account Manager',
            '24/7 Premium Support'
        ],
        'description': 'Complete solution for established businesses'
    }
}

# Add-on Services
ADDON_SERVICES = {
    'video': {'name': 'Video Content', 'price': 1000},
    'analytics': {'name': 'Advanced Analytics', 'price': 500},
    'seo': {'name': 'SEO Optimization', 'price': 750},
    'emergency': {'name': '24/7 Emergency', 'price': 1500}
}
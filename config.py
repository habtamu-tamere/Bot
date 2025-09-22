import os

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    TELEGRAM_CHANNEL = '@campaigneth'
    
    # Service Tiers in Ethiopian Birr
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
    
    # Add-on Services
    ADDON_SERVICES = {
        'video': {'name': '🎥 Video Content', 'price': 1000},
        'analytics': {'name': '📈 Advanced Analytics', 'price': 500},
        'seo': {'name': '🔍 SEO Optimization', 'price': 750},
        'emergency': {'name': '🚨 Emergency Support', 'price': 1500}
    }
import os
import re

FAVICON_MAP = {
    # Public pages
    'index.html': '🏙️',
    'about.html': '🏙️',
    'features.html': '✨',
    'contact.html': '📞',
    'page.html': '🚀',
    
    # Auth
    'admin_login.html': '🔐',
    'admin_register.html': '📝',
    'admin_verify_otp.html': '🔢',
    'forgot_password.html': '🔑',
    'reset_password.html': '🔄',
    'user_login.html': '🔐',
    'verify_otp.html': '🔢',
    
    # Admin
    'admin_dashboard.html': '👑',
    'admin_bookings.html': '📅',
    'admin_complaints.html': '⚖️',
    'admin_invoices.html': '🧾',
    'admin_notices.html': '📢',
    'admin_polls.html': '📊',
    'admin_settings.html': '⚙️',
    'admin_tenants.html': '👥',
    'admin_visitors.html': '🚶',
    
    # User
    'user_dashboard.html': '🏠',
    'user_bookings.html': '📅',
    'user_complaints.html': '🚨',
    'user_emergency.html': '🆘',
    'user_notices.html': '📢',
    'user_polls.html': '📊',
    'user_visitors.html': '🚶',
    'payment_success.html': '✅',
    'profile.html': '👤',
}

def get_emoji(filename):
    return FAVICON_MAP.get(filename, '🏢')

def remove_existing_favicons(content):
    content = re.sub(r'<link[^>]*rel=["\']icon["\'][^>]*>', '', content, flags=re.IGNORECASE)
    return content

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    filename = os.path.basename(filepath)
    emoji = get_emoji(filename)
    content = remove_existing_favicons(content)
    new_favicon_tag = f'\n    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>{emoji}</text></svg>">\n'
    
    if '</head>' in content:
        content = content.replace('</head>', f'{new_favicon_tag}</head>')
    elif '</head>' in content.lower():
        content = content.replace('</head>', f'{new_favicon_tag}</head>')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                update_file(os.path.join(root, file))

if __name__ == '__main__':
    main()

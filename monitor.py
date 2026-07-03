import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_isins():
    isins = {}
    with open('isins.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = [p.strip() for p in line.split(';', 1)]
                isin = parts[0].upper()
                name = parts[1] if len(parts) > 1 else ''
                isins[isin] = name
    return isins

def get_last_post_id():
    if os.path.exists('last_post.txt'):
        try:
            with open('last_post.txt', 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_last_post_id(post_id):
    with open('last_post.txt', 'w') as f:
        f.write(str(post_id))

def get_last_page(thread_base_url):
    response = requests.get(thread_base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    pages = [int(a['data-page']) for a in soup.find_all('a', {'data-page': True}) if a.get('data-page')]
    return max(pages) if pages else 1

def scrape_page(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []
    
    for article in soup.find_all('article', class_=re.compile(r'message')):
        data_content = article.get('data-content', '')
        if not data_content.startswith('post-'):
            continue
        post_id = int(data_content.replace('post-', ''))
        
        author_tag = article.find(['a', 'span'], class_=re.compile(r'username|message-author'))
        author = author_tag.get_text(strip=True) if author_tag else 'Unknown'
        
        message_div = article.find('div', class_=re.compile(r'message-body|message-content'))
        message = message_div.get_text(strip=True) if message_div else ''
        
        link = f"{page_url.split('#')[0]}#post-{post_id}"
        
        posts.append({
            'post_id': post_id,
            'author': author,
            'message': message,
            'link': link
        })
    return posts

def find_matches(text, isins):
    text_upper = text.upper()
    return [(isin, name) for isin, name in isins.items() if isin in text_upper]

def send_telegram(notification, config):
    if not config.get('telegram', False):
        return
    token = config.get('telegram_bot_token')
    chat_id = config.get('telegram_chat_id')
    if token and chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": notification, "parse_mode": "HTML"}
            )
        except:
            pass

def main():
    config = load_config()
    thread_url = config['thread_url'].rstrip('/')
    isins = load_isins()
    last_post_id = get_last_post_id()
    
    print(f"[{datetime.now()}] Monitoring {thread_url}")
    
    last_page = get_last_page(thread_url)
    print(f"Last page detected: {last_page}")
    
    max_id = last_post_id
    for p in range(max(1, last_page-1), last_page + 1):
        page_url = f"{thread_url}/page-{p}" if p > 1 else thread_url
        print(f"  Checking page {p}")
        
        for post in scrape_page(page_url):
            if post['post_id'] <= last_post_id:
                continue
            if post['post_id'] > max_id:
                max_id = post['post_id']
            
            matches = find_matches(post['message'], isins)
            if matches:
                for isin, name in matches:
                    msg = f"""🔔 <b>FinanzaOnline</b>

📌 Discussione: Certificati da seguire Volume LXIII
👤 Utente: {post['author']}
📈 ISIN: {isin}
🏷️ Nome: {name or 'N/A'}
💬 {post['message'][:400]}...

🔗 <a href="{post['link']}">Apri post</a>"""
                    send_telegram(msg, config)
                    print(f"   → Notification for ISIN {isin} (post {post['post_id']})")
    
    save_last_post_id(max_id)
    print(f"Updated last_post_id to {max_id}")

if __name__ == "__main__":
    main()

import re
from playwright.sync_api import sync_playwright
import json
import time

# تعريف نمط البحث عن الروابط باستخدام Regex
url_pattern = re.compile(r'https?://\S+')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    # تحميل الكوكيز من الملف
    with open("cookies.json", "r", encoding='utf-8') as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()
    page.goto("https://x.com/home")
    time.sleep(2)

    with open("users.txt", 'r', encoding='utf-8') as file:
        for username in file:
            username = username.strip()
            if username:
                user_url = f"https://x.com/{username}"
                page.goto(user_url)
                page.wait_for_selector('div[data-testid="UserDescription"]')
                time.sleep(2)

                try:
                    # استخراج البايو
                    bio_element = page.query_selector('div[data-testid="UserDescription"]')
                    bio = bio_element.inner_text().strip() if bio_element else ""

                    # استخراج الروابط من البايو
                    urls_in_bio = url_pattern.findall(bio)

                    element_text = page.locator('xpath=//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/div[1]/div/div[4]/div/a')
                    element_text = element_text.inner_text().strip() if element_text else ""

                    # البحث داخل أول 10 تغريدات
                    tweet_links = []
                    tweets = page.locator('div[data-testid="tweetText"]').all()[:10]
                    for tweet in tweets:
                        tweet_text = tweet.inner_text().strip()
                        tweet_urls = url_pattern.findall(tweet_text)
                        if tweet_urls:
                            tweet_links.extend(tweet_urls)




                except Exception as e:
                    bio = ""
                    urls_in_bio = []
                    element_text = ""
                    tweet_links = []

                # ✅ **إذا لم يوجد أي رابط، انتقل إلى الحساب التالي فورًا**
                if not urls_in_bio and not element_text and not tweet_urls:
                    continue

                # طباعة النتائج فقط إذا كان هناك رابط في البايو أو UserUrl
                if urls_in_bio or element_text or tweet_urls:
                    print(f"👤 المستخدم: {username}")
                    if urls_in_bio:
                        print(f"🔗 الروابط في البايو: {', '.join(urls_in_bio)}")
                    if element_text:
                        print(f"🌍 الرابط في UserUrl: {element_text}")
                    if tweet_links:
                        print(f"📢 الروابط في التغريدات: {', '.join(tweet_urls)}")
                    print("-" * 50)

    browser.close()

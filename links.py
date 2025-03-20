import re
import csv
import json
import time
import shutil
import sys
import tkinter as tk
from tkinter import ttk
from playwright.sync_api import sync_playwright

# 🔹 **إنشاء نافذة `tkinter` لإظهار حالة البرنامج**
root = tk.Tk()
root.title("🔄 جاري التنفيذ...")
root.geometry("300x150")
root.resizable(False, False)

# إضافة نص داخل النافذة
status_label = ttk.Label(root, text="🔄 جاري تنفيذ العملية...", font=("Arial", 12))
status_label.pack(pady=30)

# تحديث النافذة
root.update()

# تعريف نمط البحث عن الروابط باستخدام Regex
url_pattern = re.compile(r'(https?://)?(www\.)?(t\.me/[a-zA-Z0-9_]+|wa\.me/[0-9]+)')

# قائمة الروابط المستهدفة (نبحث فقط عن هذه الروابط)
target_domains = ["t.me", "wa.me"]

# اسم ملف CSV الذي سيتم حفظ النتائج فيه
output_file = "result.csv"

# إنشاء ملف CSV مع رأس الجدول
with open(output_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Username", "Links"])

with sync_playwright() as p:
    # الحصول على مسار Chromium
    chromium_path = r"chromium\chrome.exe"

    if chromium_path:
        browser = p.chromium.launch(executable_path=chromium_path, headless=True)
    else:
        status_label.config(text="❌ لم يتم العثور على Chromium!")
        root.update()
        root.after(3000, root.destroy)
        sys.exit(1)

    context = browser.new_context()

    # تحميل الكوكيز من الملف
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()
    page.goto("https://x.com/home")
    time.sleep(2)

    with open("users.txt", 'r', encoding='utf-8') as file:
        for username in file:
            username = username.strip()
            if username:
                user_url = f"{username}"
                print(f"🔹 الانتقال إلى صفحة: {user_url}")
                page.goto(user_url)
                time.sleep(2)

                try:
                    # استخراج البايو
                    bio_element = page.query_selector('div[data-testid="UserDescription"]')
                    bio = bio_element.inner_text().strip() if bio_element else ""

                    # استخراج الروابط من البايو وتصفية `target_domains`
                    bio_links_text = []
                    found_bio_links = url_pattern.findall(bio)
                    for match in found_bio_links:
                        protocol = "https://" if not match[0] else match[0]
                        full_url = protocol + match[2]

                        if any(domain in full_url for domain in target_domains):
                            bio_links_text.append(full_url)

                    # استخراج الرابط من UserUrl باستخدام XPath
                    url_element = page.query_selector('xpath=//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/div[1]/div[2]/div[4]/div/a/span')

                    urls_in_user_url = []
                    if url_element:
                        element_text = url_element.inner_text().strip()
                        print(f"🔗 رابط مستخرج من UserUrl: {element_text}")

                        # التأكد من أن النص يحتوي على رابط صالح في target_domains
                        if any(domain in element_text for domain in target_domains):
                            if not element_text.startswith("http"):
                                element_text = "https://" + element_text  # إضافة https:// إذا لم يكن موجودًا
                            urls_in_user_url.append(element_text)

                    # البحث داخل أول 10 تغريدات وتصفيتها بناءً على `target_domains`
                    tweet_links = []
                    tweets = page.locator('div[data-testid="tweetText"]').all()[:10]
                    for tweet in tweets:
                        tweet_text = tweet.inner_text().strip()
                        tweet_urls = []
                        found_tweet_links = url_pattern.findall(tweet_text)

                        for match in found_tweet_links:
                            protocol = "https://" if not match[0] else match[0]
                            full_url = protocol + match[2]

                            if any(domain in full_url for domain in target_domains):
                                tweet_urls.append(full_url)

                        if tweet_urls:
                            tweet_links.append({"text": tweet_text, "urls": tweet_urls})

                except Exception as e:
                    print(f"⚠️ خطأ أثناء تحليل الحساب {username}: {e}")
                    bio_links_text = []
                    urls_in_user_url = []
                    tweet_links = []

                # ✅ **إذا لم يوجد أي رابط في `target_domains`، تجاوز الحساب**
                if not bio_links_text and not urls_in_user_url and not tweet_links:
                    continue

                # دمج جميع الروابط من البايو، UserUrl، والتغريدات في قائمة واحدة
                links_to_save = bio_links_text + urls_in_user_url
                for tweet in tweet_links:
                    links_to_save.extend(tweet["urls"])

                # حفظ النتائج في ملف CSV
                with open(output_file, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([username, ", ".join(links_to_save)])

                # ✅ **طباعة فقط الحسابات التي تحتوي على روابط في `target_domains`**
                print(f"👤 المستخدم: {username}")
                if bio_links_text:
                    print(f"🔗 الروابط في البايو: {', '.join(bio_links_text)}")
                if urls_in_user_url:
                    print(f"🌍 الرابط في UserUrl: {', '.join(urls_in_user_url)}")
                if tweet_links:
                    for tweet in tweet_links:
                        print(f"📢 تغريدة: {tweet['text']}")
                        print(f"🔗 الروابط في التغريدة: {', '.join(tweet['urls'])}")
                        print("-" * 50)

    browser.close()

status_label.config(text="✅ تم التنفيذ بنجاح!")
root.update()
root.after(3000, root.destroy)
root.mainloop()
sys.exit(0)

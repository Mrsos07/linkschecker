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
url_pattern = re.compile(r'(https?://\S+|\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\S*)')

# قائمة الروابط المستهدفة (نبحث فقط عن هذه الروابط)
target_domains = ["t.me", "wa.me"]

# اسم ملف CSV الذي سيتم حفظ النتائج فيه
output_file = "result.csv"

# إنشاء ملف CSV مع رأس الجدول
with open(output_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Username", "Links"])

with sync_playwright() as p:
    # الحصول على مسار Chromium باستخدام shutil
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
                user_url = f"https://x.com/{username}"
                print(f"🔹 الانتقال إلى صفحة: {user_url}")
                page.goto(user_url)
                time.sleep(2)

                try:
                    # استخراج البايو كنص
                    bio_element = page.query_selector('div[data-testid="UserDescription"]')
                    bio = bio_element.inner_text().strip() if bio_element else ""

                    # استخراج الروابط العادية من النص باستخدام Regex
                    bio_links_text = url_pattern.findall(bio)

                    # استخراج الروابط داخل <a href="...">
                    bio_links_href = [a.get_attribute("href") for a in page.query_selector_all('div[data-testid="UserDescription"] a') if a.get_attribute("href")]

                    # دمج جميع الروابط المكتشفة من البايو
                    all_bio_links = list(set(bio_links_text + bio_links_href))
                    # تصفية الروابط بحيث نحتفظ فقط بالروابط التي تحتوي على t.me أو wa.me
                    all_bio_links = [link for link in all_bio_links if any(domain in link for domain in target_domains)]

                    # استخراج الرابط من UserUrl
                    url_element = page.query_selector('div[data-testid="UserUrl"] a')
                    element_text = url_element.get_attribute("href") if url_element else ""
                    if not any(domain in element_text for domain in target_domains):
                        element_text = ""

                    # البحث داخل أول 10 تغريدات
                    tweet_links = []
                    tweets = page.locator('div[data-testid="tweetText"]').all()[:10]
                    for tweet in tweets:
                        tweet_text = tweet.inner_text().strip()
                        tweet_urls = [url for url in url_pattern.findall(tweet_text) if any(domain in url for domain in target_domains)]
                        if tweet_urls:
                            tweet_links.append({"text": tweet_text, "urls": tweet_urls})

                except Exception as e:
                    print(f"⚠️ خطأ أثناء تحليل الحساب {username}: {e}")
                    bio = ""
                    all_bio_links = []
                    element_text = ""
                    tweet_links = []

                # إذا لم يوجد أي رابط يحتوي على "t.me" أو "wa.me"، نتخطى الحساب
                if not all_bio_links and not element_text and not tweet_links:
                    continue

                # دمج جميع الروابط من البايو، UserUrl، والتغريدات في قائمة واحدة
                links_to_save = all_bio_links + ([element_text] if element_text else [])
                for tweet in tweet_links:
                    links_to_save.extend(tweet["urls"])

                # حفظ النتائج في ملف CSV
                with open(output_file, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([username, ", ".join(links_to_save)])

                # طباعة النتائج
                print(f"👤 المستخدم: {username}")
                if all_bio_links:
                    print(f"🔗 الروابط في البايو: {', '.join(all_bio_links)}")
                if element_text:
                    print(f"🌍 الرابط في UserUrl: {element_text}")
                if tweet_links:
                    for tweet in tweet_links:
                        print(f"📢 تغريدة: {tweet['text']}")
                        print(f"🔗 الروابط في التغريدة: {', '.join(tweet['urls'])}")
                        print("-" * 50)

    browser.close()

# 🔹 **تحديث الرسالة عند انتهاء التنفيذ**
status_label.config(text="✅ تم التنفيذ بنجاح!")
root.update()

# إبقاء النافذة مفتوحة لمدة 3 ثوانٍ ثم إغلاقها
root.after(3000, root.destroy)
root.mainloop()

sys.exit(0)

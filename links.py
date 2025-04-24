
import os
import sys
import csv
import json
import time
from playwright.sync_api import sync_playwright
import tkinter as tk
from tkinter import ttk

# 🔹 إنشاء نافذة `tkinter` لإظهار حالة البرنامج
root = tk.Tk()
root.title("\U0001F501 جاري التنفيذ...")
root.geometry("300x150")
root.resizable(False, False)
status_label = ttk.Label(root, text="\U0001F501 جاري تنفيذ العملية...", font=("Arial", 12))
status_label.pack(pady=30)
root.update()

# تحديد مسار التشغيل
app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
users_path = os.path.join(app_dir, "المستخدم.txt")
words_path = os.path.join(app_dir, "كلمات البحث.txt")
output_path = os.path.join(app_dir, "النتائج.csv")
cookies_path = os.path.join(app_dir, "cookies.json")
chromium_path = os.path.join(app_dir, "chromium", "chrome.exe")

# تحميل الكلمات
with open(words_path, "r", encoding="utf-8") as f:
    target_words = [w.strip().lower() for w in f if w.strip()]
print("\U0001F4CC كلمات البحث:", target_words)

# تجهيز ملف النتائج
with open(output_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Username", "Source", "Matched Words"])

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chromium_path, headless=False)
    context = browser.new_context()

    # تحميل الكوكيز
    with open(cookies_path, "r", encoding="utf-8") as f:

        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()
    page.goto("https://x.com/home")
    time.sleep(4)

    with open(users_path, "r", encoding="utf-8") as file:
        for username in file:
            username = username.strip()
            if not username.startswith("http"):
                continue

            print(f"\n\U0001F539 فتح الحساب: {username}")
            status_label_text = None

            try:
                page.goto(username, timeout=10000)
                time.sleep(4)

                # ✅ التعامل مع تحذير المحتوى الحساس
                try:
                    sensitive_text_xpath = 'xpath=//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/div[2]/div/div[2]'
                    confirm_button_xpath = 'xpath=//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/div[2]/div/button'

                    sensitive_element = page.query_selector(sensitive_text_xpath)
                    if sensitive_element:
                        text_content = sensitive_element.inner_text().strip()
                        if "انت تشاهد" in text_content or "تحذير" in text_content or "أنت تشاهد" in text_content or "Caution" in text_content or "You’re seeing" in text_content or "You are seeing" in text_content:
                            print("\u26a0\ufe0f الحساب يحتوي تحذير محتوى حساس، جاري الضغط على الزر...")
                            confirm_button = page.query_selector(confirm_button_xpath)
                            if confirm_button:
                                confirm_button.click()
                                time.sleep(2)
                            status_label_text = "sensitive"
                except Exception as e:
                    print(f"\U0001F538 تعذر معالجة تحذير المحتوى الحساس: {e}")


                # ✅ التعامل مع الحسابات الموقوفة
                try:
                    suspended_account_xpath = 'xpath=//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/div[2]/div/div[1]/span'
                    suspended_element = page.query_selector(suspended_account_xpath)
                    if suspended_element:
                        suspended_text = suspended_element.inner_text().strip()
                        if "الحساب موقوف" in suspended_text or "Account suspended" in suspended_text:
                            print("\U0001f6ab الحساب معلق، جاري حفظه...")
                            with open(output_path, mode="a", newline="", encoding="utf-8") as f:
                                writer = csv.writer(f)
                                writer.writerow([username, "suspended", "suspended"])
                            continue
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


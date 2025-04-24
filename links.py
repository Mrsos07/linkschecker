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
                    print(f"\u274c خطأ أثناء التحقق من تعليق الحساب: {e}")

                # 🔍 BIO
                match_found = None
                bio_element = page.query_selector('div[data-testid="UserDescription"]')
                if bio_element:
                    bio_text = bio_element.inner_text().strip().lower()
                    bio_matches = [w for w in target_words if w in bio_text]
                    if bio_matches:
                        match_found = ("bio", ", ".join(bio_matches))
                time.sleep(0.5)

                # ✅ user_url
                if not match_found:
                    url_element = page.query_selector('xpath=//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/div[2]/div/div[1]/span')
                    if url_element:
                        url_text = url_element.inner_text().strip().lower()
                        url_matches = [w for w in target_words if w in url_text]
                        if url_matches:
                            match_found = ("user_url", ", ".join(url_matches))
                time.sleep(0.5)

                # ✅ tweets
                if not match_found:
                    tweet_elements = page.locator('div[data-testid="tweetText"]').all()[:10]
                    for tweet in tweet_elements:
                        tweet_text = tweet.inner_text().strip().lower()
                        tweet_matches = [w for w in target_words if w in tweet_text]
                        if tweet_matches:
                            match_found = ("tweet", ", ".join(tweet_matches))
                            break
                time.sleep(0.5)

                # ✍️ كتابة النتائج
                if match_found:
                    with open(output_path, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([username, match_found[0], match_found[1]])
                    print(f"\u2705 تطابق في {match_found[0]} لـ {username} → {match_found[1]}")

                elif status_label_text == "sensitive":
                    with open(output_path, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([username, "sensitive", "sensitive"])
                    print(f"\u26a0\ufe0f الحساب حساس، تم تسجيله كـ sensitive")

                else:
                    with open(output_path, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([username, "no_match", "no_match"])
                    print(f"\u274c لا يوجد تطابق في {username}")

            except Exception as e:
                print(f"\u274c خطأ أثناء فتح الحساب   {username}: {e}")

    browser.close()
    root.after(3000, root.destroy)
    root.mainloop()
    sys.exit(0)
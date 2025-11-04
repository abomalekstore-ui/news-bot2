import sys
import types
import os
import time
import requests
import telebot
from flask import Flask
import threading

# 🩹 إصلاح مكتبة cgi المفقودة في Python 3.13
# مكتبة feedparser القديمة بتستخدم cgi.parse_header وده مش موجود في الإصدارات الحديثة
def fake_parse_header(value):
    # نرجع محتوى بسيط زي ما feedparser بيحتاج
    parts = value.split(";")
    main_value = parts[0].strip()
    params = {}
    for item in parts[1:]:
        if "=" in item:
            k, v = item.strip().split("=", 1)
            params[k.lower()] = v.strip('"')
    return main_value, params

cgi = types.ModuleType("cgi")
cgi.parse_header = fake_parse_header
sys.modules["cgi"] = cgi

# 📦 مكتبة قراءة RSS
import feedparser

# 🔑 توكن البوت
TOKEN = "8376936171:AAFxfdp4S4RtyCI9f-ZDUi7vMQTXEuPQUs4"
CHAT_ID = "@AkhbarLast"  # اسم القناة

bot = telebot.TeleBot(TOKEN)
sent_titles = set()

# 🌍 مصادر الأخبار
rss_feeds = [
    "https://www.aljazeera.net/aljazeera/rss",
    "https://www.alarabiya.net/.mrss/ar.xml",
    "https://www.skynewsarabia.com/web/rss.xml",
    "https://arabic.cnn.com/rss",
    "https://www.youm7.com/rss/SectionRss?SectionID=65",
    "https://www.youm7.com/rss/SectionRss?SectionID=298",
    "https://www.youm7.com/rss/SectionRss?SectionID=88",
    "https://www.youm7.com/rss/SectionRss?SectionID=332",
    "https://www.youm7.com/rss/SectionRss?SectionID=297",
    "https://www.masrawy.com/rss/rss",
    "https://www.akhbarak.net/rss",
    "https://www.elbalad.news/rss",
    "https://www.alittihad.ae/rss",
    "https://www.albayan.ae/polopoly_fs/2.206/rss/1.316403",
    "https://www.sayidaty.net/rss.xml"
]

# 📁 تحميل العناوين السابقة
if os.path.exists("sent.txt"):
    with open("sent.txt", "r", encoding="utf-8") as f:
        sent_titles = set(f.read().splitlines())
else:
    sent_titles = set()

# 💾 حفظ العناوين الجديدة
def save_sent_titles():
    with open("sent.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sent_titles))

# 📰 جلب الأخبار
def fetch_news():
    all_news = []
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                title = entry.title
                link = entry.link
                desc = entry.get("summary", "")
                img = ""

                # استخراج الصورة
                if "media_content" in entry:
                    img = entry.media_content[0]["url"]
                elif "links" in entry:
                    for l in entry.links:
                        if l.get("type", "").startswith("image"):
                            img = l["href"]
                            break

                if title not in sent_titles and len(desc) > 40:
                    all_news.append({
                        "title": title,
                        "desc": desc,
                        "link": link,
                        "img": img
                    })
        except Exception as e:
            print("⚠️ خطأ في المصدر:", e)
    return all_news

# 🚀 إرسال الأخبار
def send_news():
    news_list = fetch_news()
    new_count = 0

    for n in news_list[:5]:
        try:
            caption = (
                f"📰 <b>{n['title']}</b>\n\n"
                f"{n['desc'][:400]}...\n\n"
                f"🔗 <a href='{n['link']}'>عرض الخبر الكامل</a>\n"
                f"✨ تابع آخر الأخبار أولاً بأول من قناتنا:\n"
                f"📢 <a href='https://t.me/AkhbarLast'>@AkhbarLast</a>\n"
                f"──────────────────"
            )

            # محاولة الإرسال الآمن
            if n.get("img"):
                try:
                    bot.send_photo(CHAT_ID, n["img"], caption=caption, parse_mode="HTML")
                except Exception as e:
                    print("⚠️ خطأ أثناء إرسال الصورة:", e)
                    bot.send_message(CHAT_ID, caption, parse_mode="HTML")
            else:
                bot.send_message(CHAT_ID, caption, parse_mode="HTML")

            sent_titles.add(n["title"])
            new_count += 1
            time.sleep(3)

        except Exception as e:
            print("⚠️ خطأ أثناء تجهيز أو إرسال الخبر:", e)

    if new_count > 0:
        print(f"✅ تم إرسال {new_count} خبر جديد.")
    else:
        print("🟤 لا توجد أخبار جديدة حالياً.")

    save_sent_titles()

# 🔁 إرسال تلقائي كل ساعة
def auto_send():
    send_news()
    while True:
        print("🕵️‍♂️ جاري التحقق من الأخبار الجديدة...")
        send_news()
        print("⏳ في انتظار الساعة القادمة...")
        time.sleep(3600)

# 🌍 لتشغيل السيرفر على Render
from flask import Flask
from threading import Thread
import os, time, requests

app = Flask(__name__)

# الصفحة الرئيسية للسيرفر (واجهة بسيطة)
@app.route('/')
def home():
    return """
    <html>
    <head><title>بوت الأخبار العربي</title></head>
    <body style="font-family:Arial; text-align:center;">
        <h2>✅ البوت شغال تمام</h2>
        <p>📢 يجلب الأخبار العربية تلقائيًا من أكبر المصادر كل ساعة.</p>
        <a href='https://t.me/AkhbarLast' target='_blank'>📡 تابع القناة</a>
    </body>
    </html>
    """

# 💤 منع السيرفر من الدخول في وضع النوم (Render)
def stay_awake():
    while True:
        try:
            # رابط سيرفرك على Render (بدّله بالرابط الفعلي بتاعك)
            requests.get("https://news-bot2.onrender.com/")
            print("✅ Ping sent to keep server awake.")
        except Exception as e:
            print(f"⚠️ خطأ أثناء محاولة إبقاء السيرفر مستيقظًا: {e}")
        time.sleep(240)  # كل 4 دقائق

# 🚀 التشغيل الرئيسي
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 البوت شغال تمام على المنفذ {port}")

    # تشغيل المهام الجانبية (إرسال الأخبار + منع النوم)
    Thread(target=auto_send, daemon=True).start()
    Thread(target=stay_awake, daemon=True).start()

    # تشغيل السيرفر Flask
    app.run(host="0.0.0.0", port=port, debug=False)

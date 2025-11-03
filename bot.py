import telebot
import feedparser
import time
from flask import Flask
from threading import Thread

# 🔑 ضع هنا التوكن الخاص بالبوت
TOKEN = "8376936171:AAFxfdp4S4RtyCI9f-ZDUi7vMQTXEuPQUs4"
CHAT_ID = "@AkhbarLast"  # اسم القناة

bot = telebot.TeleBot(TOKEN)
sent_titles = set()

# 🌍 مصادر الأخبار العربية
rss_feeds = [
    "https://www.aljazeera.net/aljazeera/rss",
    "https://www.alarabiya.net/.mrss/ar.xml",
    "https://www.skynewsarabia.com/web/rss.xml",
    "https://arabic.cnn.com/rss",
    "https://www.youm7.com/rss/SectionRss?SectionID=65",  # سياسة
    "https://www.youm7.com/rss/SectionRss?SectionID=298",  # رياضة
    "https://www.youm7.com/rss/SectionRss?SectionID=88",  # فن
    "https://www.youm7.com/rss/SectionRss?SectionID=332",  # اقتصاد
    "https://www.youm7.com/rss/SectionRss?SectionID=297",  # تكنولوجيا
    "https://www.masrawy.com/rss/rss",
    "https://www.akhbarak.net/rss",
    "https://www.elbalad.news/rss",
    "https://www.alittihad.ae/rss",
    "https://www.albayan.ae/polopoly_fs/2.206/rss/1.316403",
    "https://www.sayidaty.net/rss.xml"
]

# 📁 تحميل العناوين القديمة من ملف نصي
if os.path.exists("sent.txt"):
    with open("sent.txt", "r", encoding="utf-8") as f:
        sent_titles = set(f.read().splitlines())
else:
    sent_titles = set()

# 💾 حفظ العناوين الجديدة بعد الإرسال
def save_sent_titles():
    with open("sent.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sent_titles))
# 📰 جلب الأخبار من جميع المصادر
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

                # استخراج الصورة إن وجدت
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

# 🚀 إرسال الأخبار بتنسيق احترافي
def send_news():
    news_list = fetch_news()
    new_count = 0
    for n in news_list[:5]:  # إرسال أول 5 أخبار فقط
        try:
            caption = (
                f"📰 <b>{n['title']}</b>\n\n"
                f"{'📸' if n['img'] else ''}\n"
                f"🖋️ {n['desc'][:400]}...\n\n"
                f"🔗 <a href='{n['link']}'>عرض الخبر الكامل</a>\n\n"
                f"━━━━━━━━━━━━━━\n"
                f"✨ انضم إلينا لمتابعة أحدث الأخبار الحصرية\n"
                f"📢 <a href='https://t.me/AkhbarLast'>@AkhbarLast</a>\n"
                f"━━━━━━━━━━━━━━"
            )

            if n["img"]:
                bot.send_photo(CHAT_ID, n["img"], caption=caption, parse_mode="HTML")
            else:
                bot.send_message(CHAT_ID, caption, parse_mode="HTML")

            sent_titles.add(n["title"])
            new_count += 1
            time.sleep(3)
        except Exception as e:
            print("⚠️ خطأ أثناء الإرسال:", e)
    if new_count > 0:
        print(f"✅ تم إرسال {new_count} خبر جديد.")
    else:
        print("ℹ️ لا توجد أخبار جديدة حالياً.")
save_sent_titles()  # حفظ الأخبار المرسلة لتجنب التكرار بعد إعادة التشغيل
# 🔁 تشغيل تلقائي كل ساعة
def auto_send():
    send_news()  # إرسال فوري أول مرة
    while True:
        print("🕵️‍♂️ جاري التحقق من الأخبار الجديدة...")
        send_news()
        print("⏳ في انتظار الساعة القادمة...")
        time.sleep(3600)

# 🌐 إبقاء السيرفر شغال Flask
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>بوت الأخبار العربي</title></head>
    <body style="font-family:Arial; text-align:center; direction:rtl;">
        <h2>✅ البوت شغال تمام</h2>
        <p>📡 يجلب الأخبار العربية تلقائيًا من أكبر المصادر كل ساعة.</p>
        <a href='https://t.me/AkhbarLast' target='_blank'>انضم لقناة الأخبار</a>
    </body>
    </html>
    """

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()
Thread(target=auto_send).start()

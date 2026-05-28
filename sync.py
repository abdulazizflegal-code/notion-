import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from notion_client import Client

# 1. إعداد الاتصال بالأسرار والمفاتيح
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
GOOGLE_CREDENTIALS = json.loads(os.environ["GOOGLE_CREDENTIALS"])

# تفعيل عملاء نوشن وقوقل
notion = Client(auth=NOTION_TOKEN)
google_creds = Credentials.from_service_account_info(
    GOOGLE_CREDENTIALS, 
    scopes=['https://www.googleapis.com/auth/calendar']
)
calendar_service = build('calendar', 'v3', credentials=google_creds)

def sync_notion_to_google():
    # جلب البيانات من جدول نوشن
    response = notion.databases.query(database_id=NOTION_DATABASE_ID)
    results = response.get("results", [])
    
    print(f"Found {len(results)} items in Notion.")

    for page in results:
        properties = page.get("properties", {})
        
        # استخراج اسم الموعد/الجلسة (تأكد أن العمود بنوشن اسمه Name أو تعديله هنا)
        title_list = properties.get("Name", {}).get("title", [])
        title = title_list[0].get("text", {}).get("content", "موعد بدون عنوان") if title_list else "موعد بدون عنوان"
        
        # استخراج التاريخ (تأكد أن نوع العمود بنوشن هو Date واسمه Date أو تعديله هنا)
        date_prop = properties.get("Date", {}).get("date", {})
        if not date_prop:
            continue
            
        start_date = date_prop.get("start")
        end_date = date_prop.get("end") or start_date # إذا لم يوجد تاريخ انتهاء يوضع نفس تاريخ البدء
        
        # تجهيز الحدث لقوقل كالندر
        event = {
            'summary': title,
            'start': {'date': start_date} if len(start_date) == 10 else {'dateTime': start_date},
            'end': {'date': end_date} if len(end_date) == 10 else {'dateTime': end_date},
        }
        
        # إرسال الموعد إلى تقويم قوقل الأساسي
        try:
            calendar_service.events().insert(calendarId='primary', body=event).execute()
            print(f"Successfully synced: {title}")
        except Exception as e:
            print(f"Error syncing {title}: {e}")

if __name__ == "__main__":
    sync_notion_to_google()

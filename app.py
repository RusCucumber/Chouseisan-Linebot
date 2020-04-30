from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import re
import datetime

import requests
import time
from bs4 import BeautifulSoup

# __name__をFlaskのアプリとして利用
app = Flask(__name__)

# 環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

# linebot api と紐付け？
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# https://<app_path>/ にアクセスした場合
@app.route("/")
def hello_world():
    return "hello world!" # hello world を表示

# https://<app_path>/callback に、POST でリクエストした場合
@app.route("/callback", methods=['POST'])
def callback():
    # httpヘッダーの X-Line-Signature を取得
    signature = request.headers['X-Line-Signature']

    # httpのリクエストのボディをテキストとして取得
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def check_message(message):
    title = ""
    schedule = ""
    pattern_time = '^\d\d?:\d\d?-\d\d?:\d\d?$'
    pattern_date = '^\d\d?/\d\d?$'
    pattern_date_time = '(^\d\d?/\d\d?)\s*\((.*?)\)$'

    flag_title = 1
    flag_time = 1

    times = []

    year = int(datetime.date.today().year)
    weeks = ['(Mon)', '(Tue)', '(Wed)', '(Thu)', '(Fri)', '(Sat)', '(Sun)']

    for token in message.splitlines():
        if flag_title:
            flag_title = 0
            result_time = re.match(pattern_time, token)
            result_date = re.match(pattern_date, token)

            if not(result_date) and not(result_time):
                title = token
                continue
            else:
                title = 'Schedule'
                continue

        if flag_time:
            result_time = re.match(pattern_time, token)

            if result_time:
                try:
                    for time in token.split('-'):
                        datetime.datetime.strptime(time, "%H:%M")
                    times.append(token)
                    continue
                except:
                    return "-1"
            else:
                result_date = re.match(pattern_date, token)
                if result_date:
                    flag_time = 0
                    if len(times) == 0:
                        times.append("")
                else:
                    return "-1"

        result_date = re.match(pattern_date, token)
        if result_date:
            try:
                date_formatted = datetime.datetime.strptime(token, "%m/%d")
                month = int(date_formatted.month)
                day = int(date_formatted.day)
                i = datetime.datetime(year, month, day).weekday()

                for scheduled_time in times:
                    schedule += (token + weeks[i] + scheduled_time + '\n')
            except:
                return "-1"
        else:
            result_date_time = re.match(pattern_date_time, token)
            if result_date_time:
                try:
                    date_formatted = datetime.datetime.strptime(result_date_time.group(1), "%m/%d")
                    month = int(date_formatted.month)
                    day = int(date_formatted.day)
                    i = datetime.datetime(year, month, day).weekday()

                    for j in result_date_time.group(2).split(','):
                        j = int(j)
                        schedule += (result_date_time.group(1) + weeks[i] + times[j] + '\n')
                except:
                    return "-1"
            else:
                return "-1"

    return title, schedule

def get_chouseisan(title, data):
    try:
        top_page = requests.get('https://chouseisan.com/schedule/newEvent/create')
        soup_top_page = BeautifulSoup(top_page.text, 'html.parser')
        chousei_token_input_tag = soup_top_page.find_all('input', id='chousei_token')
        chousei_token = chousei_token_input_tag[0].get('value')
    except:
        return "-1"
    time.sleep(3)

    session = requests.session()
    response = session.get('https://chouseisan.com/schedule/newEvent/create')    

    event = {
        'name': title,
        'kouho': data,
        'chousei_token': chousei_token
    }

    try:
        create_page = session.post('https://chouseisan.com/schedule/newEvent/create', data=event)
    except:
        return "-1"
    time.sleep(3)

    try:
        soup_create_page = BeautifulSoup(create_page.text, 'html.parser')
        input_tag_url = soup_create_page.find_all('input', class_='form-input new-event-url-input')
        schedule_url = input_tag_url[0].get('value')
        return schedule_url
    except:
        return "-1"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    response = ""

    ## メッセージが仕様通りかチェック
    date = check_message(event.message.text)
    if (date == "-1"):
        response = "ERROR\nMessage should be like this:\n   month/day\nfor example:\n   12/1"
    else:
        ## メッセージから取得した日付で調整さんのリンクを生成
        chouseisan = get_chouseisan(date)

        if (chouseisan == "-1"):
            response = "ERROR\nFailed to get URL of chousei-san."
        else:
            response = chouseisan

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
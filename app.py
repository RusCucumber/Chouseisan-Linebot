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

    schedule = ""
    pattern_date = '^\d\d?/\d\d?$'

    for date in message.splitlines():
        result = re.match(pattern_date, date)
        if result:
            try:
                date_formatted = datetime.datetime.strptime(date, "%m/%d")
                schedule += (date + '\n')
            except:
                return "Error"

        else:
            return "Error"

    return schedule


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    hoge = check_message(event.message.text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=hoge))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
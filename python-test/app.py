from flask import Flask, request, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os

app = Flask(__name__)

line_bot_api = LineBotApi('00KCkQLhlaDFzo5+UTu+/C4A49iLmHu7bbpsfW8iamonjEJ1s88/wdm7Yrou+FazbxY7719UNGh96EUMa8QbsG Bf9K5rDWhJpq8XTxakXRuTM6HiJDSmERbIWfyfRMfscXJPcRyTL6YyGNZxqkYSAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('6c12aedc292307f95ccd67e959973761')

# ユーザーごとの進行状況を記録（簡易的に辞書で管理、実用時はDB推奨）
user_progress = {}

# ヒント一覧
hints = {
    1: "○○に注目してみよう",
    2: "△△を見てみて",
    3: "□□がヒントだよ",
    4: "◇◇に気づいた？",
    5: "最後は☆☆が決め手"
}

# 第1問〜第5問の出題文
questions = {
    1: "第1問：○○",
    2: "第2問：△△",
    3: "第3問：□□",
    4: "第4問：◇◇",
    5: "第5問：☆☆"
}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400
    return 'OK'
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text == "スタート":
        user_progress[user_id] = 1
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="参加してくれてありがとう！" + questions[1])
        )
    elif text.startswith("ヒント"):
        num = text.replace("ヒント", "")
        if num.isdigit():
            num = int(num)
            hint = hints.get(num, "その問題のヒントはありません")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=hint))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ヒントの番号が分かりません"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="コマンドが認識されません"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    with open("pending_users.txt", "a") as f:
        f.write(user_id + "\n")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="画像を受け付けました！判定をお待ちください。")
    )
@app.route("/form")
def show_form():
    return render_template("judge.html")

@app.route("/judge", methods=['POST'])
def judge():
    user_id = request.form['user_id']
    result = request.form['result']
    progress = user_progress.get(user_id, 1)

    if result == "correct":
        message = "正解です！"
        progress += 1
        if progress > 5:
            message += "全問クリアおめでとう！"
        else:
            message += f"次の謎に進んでください！\n{questions[progress]}"
        user_progress[user_id] = progress
    else:
        message = "不正解です！もう一度挑戦してみてください。"

    line_bot_api.push_message(user_id, TextSendMessage(text=message))

    # ファイルから該当ユーザー削除
    if os.path.exists("pending_users.txt"):
        with open('pending_users.txt', 'r') as f:
            lines = f.readlines()
        with open('pending_users.txt', 'w') as f:
            for line in lines:
                if line.strip() != user_id:
                    f.write(line)

    return '判定メッセージを送信しました'

if __name__ == "__main__":
    app.run(debug=True)




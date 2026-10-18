#!startと!finishのみ実装した軽量なRecBotのプログラム
#現状のchat_bot.exeは、テキストの内容をすべてメモリに保管したうえで、最後の!finishでファイルを出力するため、もしかしたらメモリの無駄使いをしているかもしれない。ファイルに逐次保存の方がメモリを効率的に使えるかも。

import discord
from discord.ext import commands
import os
import glob
from datetime import datetime

# ==========================================
# 1. フォルダの作成と初期設定
# ==========================================
# 実行しているPythonファイルと同じフォルダを基準にする
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "meeting_data")

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

is_recording = False
record_channel_id = None
current_log_path = None  # 現在書き込んでいるファイルのパスを保持

# ==========================================
# 2. Discord Bot コマンド & イベント
# ==========================================
@bot.event
async def on_ready():
    print("=========================================")
    print(f"🤖 {bot.user.name} がオンラインになりました！")
    print(f"📁 保存先: {DATA_FOLDER}")
    print("■ バックグラウンドで実行中です。自動終了時間まで待機します。")
    print("=========================================")

@bot.event
async def on_message(message):
    global is_recording, record_channel_id, current_log_path
    
    if is_recording and message.channel.id == record_channel_id and not message.author.bot:
        if not message.content.startswith(('!', '/')):
            timestamp = message.created_at.timestamp()
            speaker = message.author.name
            text = message.content
            
            # メッセージを受信した瞬間にファイルへ「追記(aモード)」する
            if current_log_path:
                with open(current_log_path, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp}|{speaker}|{text}\n")
                    
            print(f"📝 記録: {speaker} - {text}")

    await bot.process_commands(message)

@bot.command()
async def start(ctx):
    global is_recording, record_channel_id, current_log_path
    
    # 過去のログファイル(chat_log*.txt)をクリア
    for log_path in glob.glob(os.path.join(DATA_FOLDER, "chat_log*.txt")):
        try: 
            os.remove(log_path)
        except: 
            pass

    # 現在の日付(YYYYMMDD)を取得して今回のファイル名を決定
    date_str = datetime.now().strftime('%Y%m%d')
    log_filename = f"chat_log_{date_str}.txt"
    current_log_path = os.path.join(DATA_FOLDER, log_filename)
    
    # ファイルを新規作成（空の状態で保存）
    open(current_log_path, 'w', encoding='utf-8').close()

    is_recording = True
    record_channel_id = ctx.channel.id
    
    await ctx.send("🎙️ **会議チャットのリアルタイム記録を開始しました！**\n*(PCのローカルフォルダに逐次保存されています)*")

@bot.command()
async def finish(ctx):
    global is_recording, current_log_path
    
    if not is_recording: 
        await ctx.send("⚠️ 現在チャットの記録は行われていません。")
        return
        
    is_recording = False
    
    # ファイルが存在するか確認し、Discordに送信する
    if current_log_path and os.path.exists(current_log_path):
        log_filename = os.path.basename(current_log_path)
        # discord.File を使ってファイルを添付
        file_attachment = discord.File(current_log_path)
        await ctx.send(f"🛑 **チャット記録を終了しました。ログファイルをお届けします。**", file=file_attachment)
    else:
        await ctx.send("🛑 **チャット記録を終了しましたが、送信するログファイルが見つかりませんでした。**")

# ==========================================
# 3. トークンの読み込みとBotの起動
# ==========================================
# 実行ファイルと同じ階層にある config.txt を読み込む
CONFIG_PATH = os.path.join(BASE_DIR, "config.txt")

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        TOKEN = f.read().strip()
except FileNotFoundError:
    print(f"❌ エラー: '{CONFIG_PATH}' が見つかりません。")
    print("Pythonファイルと同じフォルダに 'config.txt' を作成し、トークンを貼り付けてください。")
    TOKEN = None

if TOKEN:
    bot.run(TOKEN)
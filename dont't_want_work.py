import os
import re
import requests
import discord
import sys
from dotenv import load_dotenv

# 讀取 .env 環境變數
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)
reply_map = {}  # 回覆ID → 自己ID

# 嘗試從 bilibili 網址跳轉取得短碼
def resolve_bilibili_shortlink(original_url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(original_url, headers=headers, allow_redirects=True, timeout=5)
        final_url = resp.url
        print(f"[跳轉結果] {original_url} → {final_url}")
        if "b23.tv" in final_url:
            short_id = final_url.split("/")[-1].split("?")[0]
            return short_id
    except Exception as e:
        print(f"[跳轉失敗] {original_url} → {e}")
    return None

# 擷取 bilibili 網址 → vxb23.tv 預覽網址
def extract_bilibili_preview_urls(message: str):
    urls = re.findall(r"https?://[^\s]+", message)
    results = []
    for url in urls:
        print(f"[偵測到網址] {url}")
        if "b23.tv" in url:
            short_id = url.split("/")[-1].split("?")[0]
            results.append(f"https://vxb23.tv/{short_id}?lang=zh-tw")
        elif "bilibili.com/video/BV" in url:
            match = re.search(r"unique_k=([a-zA-Z0-9]+)", url)
            if match:
                short_id = match.group(1)
            else:
                bv_match = re.search(r"video/(BV[0-9A-Za-z]+)", url)
                if bv_match:
                    short_id = bv_match.group(1)
                else:
                    short_id = resolve_bilibili_shortlink(url)

            if short_id:
                results.append(f"https://vxb23.tv/{short_id}?lang=zh-tw")
            else:
                results.append(f"⚠️ 無法為此影片產生預覽連結：{url}")
    return results

# Bot 啟動時
@bot.event
async def on_ready():
    print(f"✅ Bot 已上線：{bot.user.name} ({bot.user.id})")
    try:
        await bot.sync_commands()
        print("🔧 指令同步成功")
    except Exception as e:
        print(f"❌ 指令同步失敗：{e}")

# 自動回覆預覽網址
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    preview_urls = extract_bilibili_preview_urls(message.content)
    if preview_urls:
        reply = "\n".join([f"🔗 {url}" for url in preview_urls])
        bot_reply = await message.reply(reply, mention_author=False)
        reply_map[bot_reply.id] = bot_reply.id
        print(f"[記錄對應] Bot 回覆ID: {bot_reply.id}")

# 右鍵：刪除預覽（對 Bot 自己的訊息）
@bot.message_command(name="刪除預覽")
async def delete_preview(interaction: discord.Interaction, message: discord.Message):
    reply_id = message.id
    print(f"[查詢刪除] 試圖刪除ID: {reply_id}")
    if reply_id in reply_map:
        try:
            await message.delete()
            await interaction.response.send_message("✅ 預覽訊息已刪除", ephemeral=True)
        except:
            await interaction.response.send_message("⚠️ 無法刪除該訊息", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 這不是機器人的預覽訊息，無法刪除", ephemeral=True)

# /reload 指令：重新啟動 bot（限本人）
@bot.slash_command(name="reload", description="重新啟動機器人（限本人）")
async def reload(interaction: discord.ApplicationContext):
    if interaction.user.id != 201687309324779521:
        await interaction.response.send_message("❌ 你沒有權限執行此操作", ephemeral=True)
        return
    await interaction.response.send_message("♻️ 機器人重新啟動中...", ephemeral=True)
    os.execv(sys.executable, ['python'] + sys.argv)

# 啟動 bot
bot.run(TOKEN)

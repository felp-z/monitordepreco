import asyncio
import httpx
import os
import sys
from pathlib import Path

# Load .env manually if exists
def load_dotenv():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("'\"")

async def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Erro: TELEGRAM_BOT_TOKEN não configurado no arquivo .env!")
        return

    print(f"Monitorando atualizações para o bot token: {token}")
    print("Por favor, envie qualquer mensagem para o seu bot no Telegram (ex: /start)...")
    
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("result", [])
                    if results:
                        # Get last message
                        last_update = results[-1]
                        message = last_update.get("message", {})
                        chat = message.get("chat", {})
                        chat_id = chat.get("id")
                        user = chat.get("username", "desconhecido")
                        name = f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                        
                        if chat_id:
                            print("\n" + "="*40)
                            print(f"✨ CHAT ID ENCONTRADO!")
                            print(f"👤 Usuário: {name} (@{user})")
                            print(f"🆔 Chat ID: {chat_id}")
                            print("="*40)
                            
                            # Ask if we should save it to .env
                            save = input("Deseja salvar este Chat ID no arquivo .env? (s/n): ").strip().lower()
                            if save in ["s", "sim", "y", "yes", ""]:
                                env_path = Path(".env")
                                content = env_path.read_text(encoding="utf-8")
                                new_content = []
                                found = False
                                for line in content.splitlines():
                                    if line.startswith("TELEGRAM_CHAT_ID="):
                                        new_content.append(f"TELEGRAM_CHAT_ID={chat_id}")
                                        found = True
                                    else:
                                        new_content.append(line)
                                if not found:
                                    new_content.append(f"TELEGRAM_CHAT_ID={chat_id}")
                                env_path.write_text("\n".join(new_content) + "\n", encoding="utf-8")
                                print("Salvo com sucesso no arquivo .env!")
                            return
                else:
                    print(f"Erro da API do Telegram (Status {resp.status_code}): {resp.text}")
            except Exception as e:
                print(f"Erro na requisição: {e}")
            
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")

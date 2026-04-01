"""Telegram 봇으로 메시지 전송"""

import sys
import requests
from pathlib import Path


ENV_PATH = Path(__file__).parent / ".env"


def load_env():
    """환경 변수 로드"""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env


def send_document(file_path, caption=None):
    """Telegram 파일 첨부 전송 (sendDocument API)"""
    env = load_env()
    bot_token = env.get('TELEGRAM_BOT_TOKEN')
    chat_id = env.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 없습니다.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    with open(file_path, 'rb') as f:
        files = {'document': (Path(file_path).name, f, 'text/html')}
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        print(f"Document 전송 성공: {file_path}")
        return True
    else:
        print(f"Document 전송 실패: {response.status_code} {response.text}")
        return False


def send_message(text, parse_mode="Markdown"):
    """Telegram 메시지 전송"""
    env = load_env()
    bot_token = env.get('TELEGRAM_BOT_TOKEN')
    chat_id = env.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 없습니다.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # 4096자 제한 분할
    MAX_LEN = 4096
    chunks = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]

    for chunk in chunks:
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
        })

        if response.status_code == 200:
            print("Telegram 전송 성공")
        else:
            if parse_mode == "Markdown":
                print("Markdown 파싱 실패, plain text로 재시도...")
                return send_message(text, parse_mode=None)
            print(f"Telegram 전송 실패: {response.status_code} {response.text}")
            return False

    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python telegram_send.py --message '텍스트'")
        print("       python telegram_send.py --document file.html '캡션'")
        sys.exit(1)

    if sys.argv[1] == '--message':
        send_message(sys.argv[2])
    elif sys.argv[1] == '--document':
        file_path = Path(sys.argv[2])
        caption = sys.argv[3] if len(sys.argv) > 3 else None
        send_document(file_path, caption)
    else:
        print("--message 또는 --document 옵션을 사용하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()

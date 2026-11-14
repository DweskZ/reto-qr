#!/usr/bin/env python3
"""Send every reward email automatically from the Mail app on this Mac.

Usage:
    python3 enviar.py lista.csv https://your-site/reto-qr/            (preview only, sends nothing)
    python3 enviar.py lista.csv https://your-site/reto-qr/ --enviar   (really sends)

lista.csv has one person per line: name, email, reward code or link.
The emails go out from the account configured in Mail, so no mail service is needed.
"""
import base64
import json
import subprocess
import sys

SCRIPT = '''
on run argv
  tell application "Mail"
    set m to make new outgoing message with properties {subject:(item 2 of argv), content:(item 3 of argv), visible:false}
    tell m to make new to recipient at end of to recipients with properties {address:(item 1 of argv)}
    send m
  end tell
end run
'''


def link_for(base, code, name):
    data = json.dumps({"c": code, "n": name}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base + "#" + base64.urlsafe_b64encode(data).decode().rstrip("=")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    path, base, send = sys.argv[1], sys.argv[2], "--enviar" in sys.argv
    people = []
    for number, line in enumerate(open(path, encoding="utf-8"), start=1):
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 3 or "@" not in parts[1] or not parts[2]:
            sys.exit(f"Line {number} must be: name, email, code")
        people.append((parts[0], parts[1], ",".join(parts[2:]).strip()))

    for name, email, code in people:
        link = link_for(base, code, name)
        subject = f"{name}, tu premio se construye"
        body = (f"Hola {name}:\n\nLos builders no reciben premios: los construyen. "
                f"Tu código QR viene en 16 bloques. Atrápalos todos y reclama tus créditos.\n\n{link}\n\n"
                "Suerte con los bugs.\n\nBuilt by Ruray")
        if send:
            result = subprocess.run(["osascript", "-e", SCRIPT, email, subject, body], capture_output=True, text=True)
            print(f"{email}: {'sent' if result.returncode == 0 else 'FAILED ' + result.stderr.strip()}")
        else:
            print(f"{email}: {link}")
    if not send:
        print(f"\nPreview only: {len(people)} emails ready. Add --enviar to send them.")


if __name__ == "__main__":
    main()

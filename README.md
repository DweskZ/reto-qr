# Reto QR · Made by Ruray

A reward you have to catch. Instead of emailing a code, email a game: the person catches the
16 pieces of their QR code with a gift box, dodges the bugs, and only then can claim the reward.

- `index.html` is the whole app: landing, game and the form that prepares the emails. No server.
- `art/` holds the two illustrations.
- `enviar.py` sends every email automatically from the Mail app on a Mac:

      python3 enviar.py lista.csv https://your-site/reto-qr/            # preview
      python3 enviar.py lista.csv https://your-site/reto-qr/ --enviar   # send

  `lista.csv` has one person per line: `name, email, code or link`.

The reward travels in the link (base64 in the URL fragment), so the game is the experience,
not the protection. Use single-use codes.

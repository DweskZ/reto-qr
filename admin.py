#!/usr/bin/env python3
"""Admin panel: paste the list of people and send every reward email in one click.

Usage:
    python3 admin.py            then open http://127.0.0.1:8770/

The panel runs only on this Mac (it listens on 127.0.0.1) and sends through the Mail app,
from the account configured there. No mail service is needed.
Set RETO_DRY=1 to try the panel without sending anything.
"""
import base64
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8770
SITE = "https://dweskz.github.io/reto-qr/"
DRY = os.environ.get("RETO_DRY") == "1"

MAIL_SCRIPT = '''
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


def message_for(base, name, code):
    link = link_for(base, code, name)
    subject = f"{name}, tu premio se construye"
    body = (f"Hola {name}:\n\nLos builders no reciben premios: los construyen. "
            f"Tu código QR viene en 16 bloques. Atrápalos todos y reclama tus créditos.\n\n{link}\n\n"
            "Suerte con los bugs.\n\nBuilt by Ruray")
    return link, subject, body


PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel de envío · Reto QR</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root { --ice: #E3EEFF; --ink: #1A1F36; --tc: #D9480F; --white: #FFFFFF; --muted: #5B6384; --ok: #1F7A4D; }
  * { box-sizing: border-box; margin: 0; }
  body { background: var(--ice); color: var(--ink); font: 500 16px/1.45 "Plus Jakarta Sans", system-ui, sans-serif; padding: 28px 20px 60px; }
  main { max-width: 860px; margin: 0 auto; }
  .top { display: flex; justify-content: space-between; align-items: center; }
  .wm { font-weight: 800; font-size: 26px; letter-spacing: -.04em; display: inline-flex; align-items: flex-end; }
  .wm i { width: 8px; height: 8px; border-radius: 50%; background: var(--tc); margin: 0 0 6px 3px; }
  .top small { font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--tc); }
  h1 { font-size: 40px; font-weight: 800; letter-spacing: -.04em; line-height: 1.05; margin-top: 22px; }
  h1 em { font-style: normal; color: var(--tc); }
  .lead { color: var(--muted); margin-top: 8px; }
  .card { margin-top: 18px; padding: 20px; background: var(--white); border: 3px solid var(--ink); border-radius: 22px; }
  label { display: block; font-size: 14px; font-weight: 700; margin-top: 12px; }
  label:first-child { margin-top: 0; }
  input, textarea { width: 100%; margin-top: 6px; padding: 12px 14px; background: var(--ice); color: var(--ink); border: 2px solid var(--ink); border-radius: 14px; font: 600 14px ui-monospace, Menlo, monospace; }
  textarea { min-height: 170px; resize: vertical; }
  .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-top: 14px; }
  .btn { appearance: none; border: 2px solid var(--ink); background: var(--white); color: var(--ink); font: 800 16px inherit; font-family: inherit; padding: 13px 22px; border-radius: 999px; cursor: pointer; }
  .btn.main { background: var(--tc); border-color: var(--tc); color: var(--white); }
  .btn:disabled { opacity: .45; cursor: default; }
  .msg { font-size: 14px; font-weight: 700; color: var(--tc); }
  .dry { display: inline-block; margin-top: 14px; padding: 8px 14px; border-radius: 999px; background: var(--ink); color: var(--white); font-size: 13px; font-weight: 800; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
  th { text-align: left; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); padding: 8px 10px; }
  td { padding: 10px; border-top: 2px solid var(--ice); vertical-align: top; word-break: break-word; }
  td.state { font-weight: 800; white-space: nowrap; }
  td.state.ok { color: var(--ok); } td.state.bad { color: var(--tc); }
  td a { color: var(--ink); font-weight: 700; }
  .sum { font-weight: 800; font-size: 18px; }
  [hidden] { display: none !important; }
</style></head>
<body><main>
  <div class="top"><span class="wm">ruray<i></i></span><small>Panel de envío</small></div>
  <h1>Envía todos los premios <em>con un clic.</em></h1>
  <p class="lead">Los correos salen desde la aplicación Mail de este equipo, con tu cuenta. Este panel solo funciona en tu computadora.</p>
  __DRY__
  <div class="card">
    <label>Una persona por línea: nombre, correo, código o enlace del premio
      <textarea id="list" placeholder="Ana, ana@ejemplo.com, CREDITOS-ABC-123&#10;Luis, luis@ejemplo.com, CREDITOS-DEF-456" spellcheck="false"></textarea></label>
    <label>Dirección pública del juego<input id="site" value="__SITE__"></label>
    <div class="row"><button class="btn" id="prep">Preparar lista</button><span class="msg" id="msg"></span></div>
  </div>
  <div class="card" id="out" hidden>
    <div class="row" style="margin-top:0"><span class="sum" id="sum"></span><button class="btn main" id="send">Enviar todos</button></div>
    <table><thead><tr><th>Persona</th><th>Correo</th><th>Enlace</th><th>Estado</th></tr></thead><tbody id="rows"></tbody></table>
  </div>
</main>
<script>
  const $ = id => document.getElementById(id);
  const esc = t => t.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let people = [];
  $("prep").addEventListener("click", async () => {
    const rows = $("list").value.split("\\n").map(l => l.trim()).filter(Boolean).map(l => {
      const p = l.split(",").map(x => x.trim());
      return { name: p[0], email: p[1], code: p.slice(2).join(",").trim() };
    });
    const bad = rows.findIndex(r => !r.name || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(r.email || "") || !r.code);
    if (!rows.length) { $("msg").textContent = "Pega al menos una persona."; return; }
    if (bad >= 0) { $("msg").textContent = `Revisa la línea ${bad + 1}: debe ser nombre, correo, código.`; return; }
    $("msg").textContent = "";
    const res = await fetch("/preview", { method: "POST", body: JSON.stringify({ site: $("site").value.trim(), people: rows }) });
    people = (await res.json()).people;
    $("rows").innerHTML = people.map((p, i) => `<tr><td>${esc(p.name)}</td><td>${esc(p.email)}</td><td><a href="${esc(p.link)}" target="_blank" rel="noopener">Abrir juego</a></td><td class="state" id="st${i}">Pendiente</td></tr>`).join("");
    $("sum").textContent = people.length === 1 ? "1 correo listo" : `${people.length} correos listos`;
    $("send").disabled = false; $("send").textContent = "Enviar todos"; $("out").hidden = false;
  });
  $("send").addEventListener("click", async () => {
    $("send").disabled = true; $("prep").disabled = true;
    let ok = 0;
    for (let i = 0; i < people.length; i++) {
      const cell = $("st" + i);
      if (cell.classList.contains("ok")) { ok++; continue; }       // never send twice to the same person
      cell.textContent = "Enviando…";
      try {
        const res = await (await fetch("/send", { method: "POST", body: JSON.stringify({ site: $("site").value.trim(), person: people[i] }) })).json();
        cell.textContent = res.ok ? "Enviado" : "Falló: " + res.error; cell.className = "state " + (res.ok ? "ok" : "bad");
        if (res.ok) ok++;
      } catch (e) { cell.textContent = "Falló"; cell.className = "state bad"; }
    }
    $("sum").textContent = `${ok} de ${people.length} enviados`;
    $("prep").disabled = false;
    if (ok < people.length) { $("send").disabled = false; $("send").textContent = "Reintentar los que fallaron"; }
  });
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body, kind="application/json"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != "/":
            return self.reply(404, "not found", "text/plain")
        note = '<span class="dry">Modo de prueba: no se envía ningún correo</span>' if DRY else ""
        self.reply(200, PAGE.replace("__SITE__", SITE).replace("__DRY__", note), "text/html")

    def do_POST(self):
        # Only pages served by this panel may call it.
        origin = self.headers.get("Origin", "")
        if origin and origin not in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self.reply(403, json.dumps({"ok": False, "error": "forbidden"}))
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            site = data["site"] if data["site"].endswith("/") else data["site"] + "/"
            if self.path == "/preview":
                people = [dict(p, link=message_for(site, p["name"], p["code"])[0]) for p in data["people"]]
                return self.reply(200, json.dumps({"people": people}))
            if self.path == "/send":
                person = data["person"]
                _, subject, body = message_for(site, person["name"], person["code"])
                if DRY:
                    return self.reply(200, json.dumps({"ok": True}))
                result = subprocess.run(["osascript", "-e", MAIL_SCRIPT, person["email"], subject, body], capture_output=True, text=True, timeout=60)
                return self.reply(200, json.dumps({"ok": result.returncode == 0, "error": result.stderr.strip()[:160]}))
        except Exception as error:  # report the problem to the panel instead of dropping the connection
            return self.reply(200, json.dumps({"ok": False, "error": str(error)[:160]}))
        self.reply(404, json.dumps({"ok": False, "error": "not found"}))


if __name__ == "__main__":
    print(f"Panel: http://127.0.0.1:{PORT}/" + ("  (test mode, nothing is sent)" if DRY else ""))
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

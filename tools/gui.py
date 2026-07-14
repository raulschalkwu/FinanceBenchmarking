#!/usr/bin/env python3
"""Lokale Web-GUI für den Promotion-Workflow.

Rohdatei hochladen -> wird als Draft im Silo abgelegt -> automatischer
Dedup-/Ordner-/Backlink-Vorschlag (tools/promote.py plan) -> ein Klick
promotet in den Kanon (tools/promote.py apply): Notiz anlegen/ergänzen,
rückverlinken, Link-Check, optional Branch/PR.

Start (mit dem venv-Python, damit ChromaDB verfügbar ist):
    .venv/bin/python tools/gui.py            # http://127.0.0.1:8765

Reine Bedienoberfläche – die ganze Logik steckt weiter in den CLI-Tools.
"""
from __future__ import annotations
import html
import html.parser
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
CANON_RE = re.compile(r"^\d\d ")


# ---------- Repo-Struktur einlesen ----------

def canon_folders():
    return sorted(p.name for p in ROOT.iterdir()
                  if p.is_dir() and CANON_RE.match(p.name))


def silos():
    d = ROOT / "drafts"
    return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []


def backlink_targets():
    out = []
    for sub in ("01 Research Streams", "12 Literature Maps"):
        base = ROOT / sub
        if base.is_dir():
            out += [str(p.relative_to(ROOT)) for p in sorted(base.glob("*.md"))]
    return out


def _index_fulltext_bg(doc_id: str, text: str, source: str):
    """Hintergrund-Thread: Volltext in die 'fulltext'-Collection einbetten."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from fulltext_index import index_text
        n = index_text(doc_id, text, source)
        print(f"[fulltext] {doc_id}: {n} Chunks indexiert", flush=True)
    except Exception as e:
        print(f"[fulltext] {doc_id}: Indexierung fehlgeschlagen: {e}", flush=True)


def run(cmd):
    """CLI-Tool mit dem GLEICHEN Python (venv) aufrufen; Output einsammeln."""
    r = subprocess.run([sys.executable, *cmd], cwd=str(ROOT),
                       capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


class _HTMLText(html.parser.HTMLParser):
    """Minimaler HTML->Text-Extraktor (stdlib, keine Zusatz-Abhängigkeit).
    Ignoriert script/style/nav/footer, setzt Absatzumbrüche bei Blockelementen."""
    _SKIP = {"script", "style", "noscript", "head", "nav", "footer", "aside"}
    _BREAK = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "section"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1
        elif tag in self._BREAK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1
        elif tag in self._BREAK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data)


def html_to_text(raw: bytes | str) -> str:
    s = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else raw
    p = _HTMLText()
    p.feed(s)
    text = "".join(p.parts)
    # überflüssige Leerzeilen zusammenfassen
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_docx(data: bytes) -> str:
    """.docx = ZIP mit word/document.xml. Text aus <w:t>-Elementen, Absätze bei
    </w:p>. Stdlib-only (zipfile), keine python-docx-Abhängigkeit nötig."""
    import io
    import zipfile
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(xml)).strip()


def extract_text(fname: str, data: bytes) -> tuple[str, str | None]:
    """Rohdatei -> Markdown-Text. Gibt (text, warnung) zurück.
    PDF (pypdf), DOCX (zipfile), HTML (Parser), sonst direkt als Text decodiert."""
    low = fname.lower()
    if low.endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = [(p.extract_text() or "").strip() for p in reader.pages]
            text = "\n\n".join(pg for pg in pages if pg)
            if not text.strip():
                return "", ("PDF enthält keinen extrahierbaren Text "
                            "(vermutlich gescannt/Bild – OCR nötig).")
            return text, None
        except ImportError:
            return "", "pypdf fehlt: .venv/bin/pip install pypdf"
        except Exception as e:
            return "", f"PDF-Extraktion fehlgeschlagen: {e}"
    if low.endswith(".docx"):
        try:
            text = extract_docx(data)
            if not text.strip():
                return "", "DOCX enthält keinen Text."
            return text, None
        except Exception as e:
            return "", f"DOCX-Extraktion fehlgeschlagen: {e}"
    if low.endswith((".html", ".htm")):
        text = html_to_text(data)
        if not text.strip():
            return "", "HTML enthält keinen lesbaren Text."
        return text, None
    return data.decode("utf-8", "ignore"), None


def fetch_url(url: str) -> tuple[str, str, str | None]:
    """URL abrufen -> (text, quellname, warnung). HTML wird zu Text, PDF per
    pypdf. Nur http/https. Der Nutzer gibt die URL selbst vor."""
    import urllib.request
    if not re.match(r"^https?://", url, re.I):
        return "", url, "Nur http(s)-URLs erlaubt."
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (VaultBot research fetch)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            ctype = resp.headers.get("Content-Type", "").lower()
            data = resp.read(25 * 1024 * 1024)  # 25 MB Deckel
    except Exception as e:
        return "", url, f"Abruf fehlgeschlagen: {e}"
    from urllib.parse import urlparse
    name = Path(urlparse(url).path).name or urlparse(url).netloc or "web"
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        text, warn = extract_text(name if name.endswith(".pdf") else name + ".pdf", data)
        return text, name, warn
    text = html_to_text(data)
    if not text.strip():
        return "", name, "Keine lesbaren Textinhalte auf der Seite."
    return text, name, None


# ---------- HTML ----------

CSS = """
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{font:15px/1.5 system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.4rem} h2{font-size:1.1rem;margin-top:1.6rem}
label{display:block;margin:.7rem 0 .2rem;font-weight:600}
input,select,textarea,button{font:inherit;padding:.5rem;width:100%;border:1px solid #8886;border-radius:6px;background:transparent;color:inherit}
button{background:#2563eb;color:#fff;border:0;cursor:pointer;font-weight:600;width:auto;padding:.6rem 1.2rem;margin-top:1rem}
button.secondary{background:#6b7280}
pre{background:#8881;padding:1rem;border-radius:8px;overflow:auto;white-space:pre-wrap}
.card{border:1px solid #8884;border-radius:10px;padding:1.2rem;margin:1rem 0}
.muted{color:#8a8a8a;font-size:.9rem}
a.btn{display:inline-block;margin-top:1rem;padding:.6rem 1.2rem;background:#16a34a;color:#fff;border-radius:6px;text-decoration:none}
.row{display:flex;gap:1rem}.row>div{flex:1}
"""


def page(body: str) -> bytes:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Vault Promotion</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>").encode("utf-8")


def opts(values, selected=None):
    return "".join(
        f"<option value='{html.escape(v)}'"
        f"{' selected' if v == selected else ''}>{html.escape(v)}</option>"
        for v in values)


def home():
    silo_opts = opts(silos() or ["user_raul"])
    return page(f"""
    <h1>📥 Vault Promotion</h1>
    <p class='muted'>Rohdatei hochladen → Draft im Silo → automatischer
    Dedup-/Ordner-Vorschlag → ein Klick in den Kanon.</p>
    <form method='POST' action='/upload' enctype='multipart/form-data' class='card'>
      <label>Rohdatei (.pdf / .docx / .html / .md / .txt)</label>
      <input type='file' name='file' accept='.pdf,.docx,.html,.htm,.md,.txt,.markdown,text/*,application/pdf' required>
      <div class='row'>
        <div><label>Silo</label><select name='silo'>{silo_opts}</select></div>
        <div><label>Titel (optional)</label><input name='title' placeholder='aus Datei ableiten'></div>
      </div>
      <button type='submit'>Hochladen & analysieren</button>
    </form>

    <form method='POST' action='/fetch' class='card'>
      <label>…oder URL (Webseite / arXiv- bzw. SSRN-Abstract / PDF-Link)</label>
      <input name='url' type='url' placeholder='https://arxiv.org/abs/2303.17564' required>
      <div class='row'>
        <div><label>Silo</label><select name='silo'>{silo_opts}</select></div>
        <div><label>Titel (optional)</label><input name='title' placeholder='aus Seite ableiten'></div>
      </div>
      <button type='submit'>Von URL holen & analysieren</button>
    </form>
    <p class='muted'>Läuft lokal. PDF/DOCX/HTML werden automatisch zu Text
    extrahiert; gescannte PDFs ohne Textebene brauchen OCR. Bei URLs wird die
    Seite abgerufen und der Fließtext übernommen.</p>
    """)


def analyze_page(draft_rel: str, plan_out: str, note_warn: str | None = None,
                 route: dict | None = None):
    route = route or {}
    note_md = (ROOT / draft_rel).read_text(encoding="utf-8")
    warn_html = (f"<div class='card' style='border-color:#f59e0b'>⚠️ "
                 f"{html.escape(note_warn)}</div>") if note_warn else ""
    note_html = (f"<h2>Erzeugte Notiz (Vorschau)</h2>"
                 f"<pre>{html.escape(note_md.strip())}</pre>")
    # Vorauswahl: LLM-Route zuerst, Plan-Heuristik als Fallback.
    sug_folder = route.get("folder")
    if not sug_folder:
        m = re.search(r'--folder "([^"]+)"', plan_out)
        if m:
            sug_folder = m.group(1)
    m2 = re.search(r'--into "([^"]+)"', plan_out)
    into_default = m2.group(1) if m2 else ""
    bl = backlink_targets()
    bl_default = route.get("backlink")
    if not bl_default:
        for line in plan_out.splitlines():
            mm = re.search(r"(01 Research Streams/.+\.md|12 Literature Maps/.+\.md)", line)
            if mm and mm.group(1) in bl:
                bl_default = mm.group(1); break
    return page(f"""
    <h1>🔎 Analyse</h1>
    <p class='muted'>Draft: <code>{html.escape(draft_rel)}</code> ·
    Volltext wird im Hintergrund indexiert (Collection <code>fulltext</code>,
    Suche: <code>tools/fulltext_index.py search "…"</code>)</p>
    {warn_html}
    {note_html}
    <h2>Automatischer Vorschlag (Dedup + Ordner + Backlinks)</h2>
    <pre>{html.escape(plan_out.strip() or '(kein Output)')}</pre>

    <form method='POST' action='/promote' class='card'>
      <input type='hidden' name='draft' value='{html.escape(draft_rel)}'>
      <h2>In den Kanon promoten</h2>
      <p class='muted'>Bei ähnlicher bestehender Notiz → „Ergänzen" wählen,
      sonst neuen Ordner. Rückverlink ist Pflicht (keine isolierten Notizen).</p>
      <label>NEU: Zielordner</label>
      <select name='folder'>{opts([''] + canon_folders(), sug_folder)}</select>
      <label>ODER Ergänzen: bestehende Notiz (Pfad, überschreibt Ordner)</label>
      <input name='into' value='{html.escape(into_default)}' placeholder='z.B. 03 Papers/NewsNet-SDF.md'>
      <label>Rückverlink-Ziel (Stream/Map, Pflicht)</label>
      <select name='backlink'>{opts(bl, bl_default)}</select>
      <label><input type='checkbox' name='push' value='1' style='width:auto'> Branch + PR erstellen (push)</label>
      <button type='submit'>✅ Promoten</button>
      <a class='btn' style='background:#6b7280' href='/'>Abbrechen</a>
    </form>
    <form method='POST' action='/discard' class='card'>
      <input type='hidden' name='draft' value='{html.escape(draft_rel)}'>
      <p class='muted'>Schon im Kanon vorhanden oder doch nicht brauchbar?
      Draft löschen (nur die Datei im Silo, der Kanon bleibt unberührt).</p>
      <button type='submit' style='background:#dc2626'>🗑 Draft verwerfen</button>
    </form>
    """)


def result_page(out: str):
    m = re.search(r"(https://github\.com/\S+/compare/\S+)", out)
    pr = (f"<a class='btn' href='{html.escape(m.group(1))}' target='_blank'>"
          f"→ PR öffnen</a>") if m else ""
    return page(f"""
    <h1>Ergebnis</h1>
    <pre>{html.escape(out.strip() or '(kein Output)')}</pre>
    {pr}
    <p><a class='btn' style='background:#6b7280' href='/'>Neue Datei</a></p>
    """)


# ---------- Multipart / HTTP ----------

def parse_multipart(body: bytes, boundary: bytes):
    fields, files = {}, {}
    for part in body.split(b"--" + boundary):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        head, _, content = part.partition(b"\r\n\r\n")
        h = head.decode("utf-8", "ignore")
        name = re.search(r'name="([^"]*)"', h)
        if not name:
            continue
        fn = re.search(r'filename="([^"]*)"', h)
        content = content.rstrip(b"\r\n")
        if fn and fn.group(1):
            files[name.group(1)] = (fn.group(1), content)
        else:
            fields[name.group(1)] = content.decode("utf-8", "ignore")
    return fields, files


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass  # ruhig

    def _ingest(self, text, warn, source_name, fields):
        """Gemeinsamer Weg für Upload UND URL: Rohtext -> Volltext-Index (bg) ->
        LLM-Notiz -> Draft im Silo -> Promotion-Plan -> Analyse-Seite."""
        if warn and not text:
            return self._send(page(
                f"<h1>Ingest</h1><p>⚠️ {html.escape(warn)}</p>"
                f"<p><a href='/'>zurück</a></p>"), 400)
        silo = re.sub(r"[^\w.-]", "", fields.get("silo", "user_raul")) or "user_raul"
        title = fields.get("title", "").strip()
        stem = re.sub(r"[^\w.\- ]", "", Path(source_name).stem) or "upload"
        silo_dir = ROOT / "drafts" / silo
        silo_dir.mkdir(parents=True, exist_ok=True)

        # Volltext separat in die 'fulltext'-Collection (getrennt von 'vault').
        threading.Thread(target=_index_fulltext_bg,
                         args=(stem, text, source_name), daemon=True).start()

        # Verständnis-Schritt: Rohtext -> saubere, vernetzte Notiz (LLM).
        note_warn, route = None, {}
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            from summarize import summarize
            text, route = summarize(text, title or stem)
        except Exception as e:
            note_warn = (f"LLM-Zusammenfassung übersprungen ({e}). "
                         f"Rohtext gespeichert – bitte manuell aufbereiten.")
            if title and not text.lstrip().startswith("---"):
                text = f"---\ntitle: {title}\n---\n\n{text}"

        # Draft nach dem echten Notiz-Titel benennen (sprechende Wikilinks).
        m_t = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
        note_title = (m_t.group(1).strip() if m_t else "") or stem
        clean = re.sub(r'[\\/:*?"<>|]', "", note_title).strip() or stem
        dest = silo_dir / f"{clean}.md"
        dest.write_text(text, encoding="utf-8")
        rel = str(dest.relative_to(ROOT))
        plan = run(["tools/promote.py", "plan", rel])
        return self._send(analyze_page(rel, plan, note_warn, route))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(home())
        else:
            self._send(page("<p>Not found. <a href='/'>Start</a></p>"), 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        ctype = self.headers.get("Content-Type", "")

        if self.path == "/upload":
            boundary = ctype.split("boundary=")[-1].encode()
            fields, files = parse_multipart(body, boundary)
            if "file" not in files or not files["file"][1]:
                return self._send(page("<p>Keine Datei. <a href='/'>zurück</a></p>"), 400)
            fname, data = files["file"]
            text, warn = extract_text(fname, data)
            return self._ingest(text, warn, Path(fname).name, fields)

        if self.path == "/fetch":
            fields = {k: v[0] for k, v in parse_qs(body.decode("utf-8")).items()}
            url = fields.get("url", "").strip()
            if not url:
                return self._send(page("<p>Keine URL. <a href='/'>zurück</a></p>"), 400)
            text, name, warn = fetch_url(url)
            return self._ingest(text, warn, name, fields)

        if self.path == "/discard":
            f = {k: v[0] for k, v in parse_qs(body.decode("utf-8")).items()}
            target = (ROOT / f.get("draft", "")).resolve()
            drafts_root = (ROOT / "drafts").resolve()
            # Sicherheitsgrenze: nur Dateien im drafts/-Baum löschbar.
            if not str(target).startswith(str(drafts_root) + "/") or not target.is_file():
                return self._send(page("<p>Ungültiger Pfad. <a href='/'>zurück</a></p>"), 400)
            target.unlink()
            return self._send(page(
                f"<h1>🗑 Verworfen</h1><p><code>{html.escape(f.get('draft',''))}</code> "
                f"wurde gelöscht. Der Kanon ist unberührt.</p>"
                f"<p><a class='btn' href='/'>Neue Datei</a></p>"))

        if self.path == "/promote":
            f = {k: v[0] for k, v in parse_qs(body.decode("utf-8")).items()}
            draft = f.get("draft", "")
            backlink = f.get("backlink", "")
            if not draft or not backlink:
                return self._send(page("<p>Draft/Backlink fehlt. <a href='/'>zurück</a></p>"), 400)
            cmd = ["tools/promote.py", "apply", draft, "--backlink", backlink]
            if f.get("into"):
                cmd += ["--into", f["into"]]
            elif f.get("folder"):
                cmd += ["--folder", f["folder"]]
            else:
                return self._send(page("<p>Ordner ODER 'into' wählen. <a href='/'>zurück</a></p>"), 400)
            if f.get("push"):
                cmd += ["--push"]
            out = run(cmd)
            return self._send(result_page(out))

        self._send(page("<p>Not found</p>"), 404)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Vault-Promotion-GUI läuft:  http://127.0.0.1:{PORT}")
    print("Beenden mit Ctrl+C.")
    srv.serve_forever()


if __name__ == "__main__":
    main()

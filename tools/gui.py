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
:root{color-scheme:light dark;
  --acc:#2563eb;--ok:#16a34a;--warn:#d97706;--bad:#dc2626;--mut:#8a8a8a;
  --line:#8884}
*{box-sizing:border-box}
body{font:15px/1.55 system-ui,sans-serif;max-width:860px;margin:0 auto;padding:0 1rem 4rem}
header{display:flex;align-items:baseline;gap:.8rem;padding:1.4rem 0 .2rem}
header h1{font-size:1.35rem;margin:0}
header .sub{color:var(--mut);font-size:.9rem}
h2{font-size:1.05rem;margin:1.6rem 0 .5rem}
label{display:block;margin:.8rem 0 .25rem;font-weight:600;font-size:.92rem}
input,select,textarea{font:inherit;padding:.55rem .7rem;width:100%;border:1px solid var(--line);border-radius:8px;background:transparent;color:inherit}
button{font:inherit;background:var(--acc);color:#fff;border:0;border-radius:8px;cursor:pointer;font-weight:600;padding:.65rem 1.3rem}
button:hover{filter:brightness(1.1)}
pre{background:#8881;padding:1rem;border-radius:10px;overflow:auto;white-space:pre-wrap;font-size:.85rem}
.card{border:1px solid var(--line);border-radius:14px;padding:1.3rem 1.4rem;margin:1rem 0}
.muted{color:var(--mut);font-size:.9rem}
a.btn{display:inline-block;padding:.6rem 1.2rem;background:var(--ok);color:#fff;border-radius:8px;text-decoration:none;font-weight:600}
a.btn.gray{background:#6b7280}
.row{display:flex;gap:1rem;flex-wrap:wrap}.row>div{flex:1;min-width:180px}
/* Tabs */
.tabs{display:flex;gap:.4rem;margin-bottom:-1px}
.tab{padding:.55rem 1.1rem;border:1px solid var(--line);border-bottom:0;
  border-radius:10px 10px 0 0;cursor:pointer;color:var(--mut);font-weight:600;background:transparent}
.tab.on{color:inherit;background:#8881}
.pane{display:none;border:1px solid var(--line);border-radius:0 12px 12px 12px;padding:1.2rem 1.4rem}
.pane.on{display:block}
/* Dropzone */
.drop{border:2px dashed var(--line);border-radius:12px;padding:1.6rem;text-align:center;
  color:var(--mut);cursor:pointer;transition:border-color .15s}
.drop.hover{border-color:var(--acc);color:inherit}
.drop .fname{font-weight:600;color:inherit}
/* Badges */
.badge{display:inline-block;padding:.25rem .7rem;border-radius:999px;font-weight:700;font-size:.85rem}
.badge.ok{background:#16a34a22;color:var(--ok);border:1px solid #16a34a55}
.badge.warn{background:#d9770622;color:var(--warn);border:1px solid #d9770655}
.badge.bad{background:#dc262622;color:var(--bad);border:1px solid #dc262655}
/* Choice rows (Neu vs Ergänzen) */
.choice{border:1px solid var(--line);border-radius:10px;padding:.8rem 1rem;margin:.5rem 0;cursor:pointer}
.choice.on{border-color:var(--acc);background:#2563eb11}
.choice input[type=radio]{width:auto;margin-right:.5rem}
details{margin:.8rem 0}
details summary{cursor:pointer;color:var(--mut);font-weight:600}
/* Loading overlay */
#load{display:none;position:fixed;inset:0;background:#0008;z-index:9;
  align-items:center;justify-content:center;flex-direction:column;gap:1rem;color:#fff}
#load.on{display:flex}
.spin{width:44px;height:44px;border:4px solid #fff4;border-top-color:#fff;border-radius:50%;
  animation:r 0.9s linear infinite}
@keyframes r{to{transform:rotate(360deg)}}
.steps{font-size:.9rem;opacity:.85;text-align:center;line-height:1.8}
"""

LOADING_HTML = """
<div id='load'><div class='spin'></div>
  <div><b>Analysiere …</b></div>
  <div class='steps'>1. Text extrahieren · 2. KI liest &amp; fasst zusammen (≈ 30–60&nbsp;s)<br>
  3. Duplikat-Prüfung · 4. Ablage-Vorschlag</div>
</div>
<script>
function showLoad(){document.getElementById('load').classList.add('on')}
document.querySelectorAll("form[data-load]").forEach(f=>f.addEventListener("submit",showLoad));
</script>
"""


def page(body: str) -> bytes:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Vault Promotion</title><style>{CSS}</style></head>"
            f"<body><header><h1>📥 Vault</h1>"
            f"<span class='sub'>Wissen rein → KI liest → du entscheidest</span>"
            f"</header>{body}{LOADING_HTML}</body></html>").encode("utf-8")


def opts(values, selected=None):
    return "".join(
        f"<option value='{html.escape(v)}'"
        f"{' selected' if v == selected else ''}>{html.escape(v)}</option>"
        for v in values)


def home():
    silo_opts = opts(silos() or ["user_raul"])
    return page(f"""
    <p class='muted'>Paper, Artikel oder Dokument hineingeben – die KI liest es,
    schreibt eine vernetzte Notiz, prüft auf Duplikate und schlägt die Ablage
    vor. In den Kanon kommt nichts ohne deinen Klick.</p>

    <div class='tabs'>
      <button class='tab on' id='t-file' onclick='tab("file")' type='button'>📄 Datei</button>
      <button class='tab' id='t-url' onclick='tab("url")' type='button'>🔗 URL</button>
    </div>

    <form method='POST' action='/upload' enctype='multipart/form-data'
          class='pane on' id='p-file' data-load>
      <div class='drop' id='drop' onclick='document.getElementById(\"fi\").click()'>
        <div class='fname' id='fname'>Datei hierher ziehen oder klicken</div>
        <div class='muted'>PDF · DOCX · HTML · Markdown · TXT</div>
      </div>
      <input type='file' name='file' id='fi' style='display:none'
             accept='.pdf,.docx,.html,.htm,.md,.txt,.markdown,text/*,application/pdf' required>
      <div class='row'>
        <div><label>Dein Silo</label><select name='silo'>{silo_opts}</select></div>
        <div><label>Titel <span class='muted'>(optional)</span></label>
             <input name='title' placeholder='aus Datei ableiten'></div>
      </div>
      <p><button type='submit'>Analysieren →</button></p>
    </form>

    <form method='POST' action='/fetch' class='pane' id='p-url' data-load>
      <label>Link zu Webseite, arXiv/SSRN-Abstract oder PDF</label>
      <input name='url' type='url' placeholder='https://arxiv.org/abs/2303.17564' required>
      <div class='row'>
        <div><label>Dein Silo</label><select name='silo'>{silo_opts}</select></div>
        <div><label>Titel <span class='muted'>(optional)</span></label>
             <input name='title' placeholder='aus Seite ableiten'></div>
      </div>
      <p><button type='submit'>Holen &amp; analysieren →</button></p>
    </form>

    <p class='muted'>Läuft komplett lokal · gescannte PDFs ohne Textebene
    brauchen OCR · Volltext wird für die Tiefensuche mit-indexiert.</p>

    <script>
    function tab(w){{
      for (const x of ['file','url']){{
        document.getElementById('t-'+x).classList.toggle('on', x===w);
        document.getElementById('p-'+x).classList.toggle('on', x===w);
      }}
    }}
    const drop=document.getElementById('drop'), fi=document.getElementById('fi');
    fi.addEventListener('change',()=>{{
      if(fi.files.length) document.getElementById('fname').textContent='📄 '+fi.files[0].name;
    }});
    for(const ev of ['dragover','dragenter'])
      drop.addEventListener(ev,e=>{{e.preventDefault();drop.classList.add('hover')}});
    for(const ev of ['dragleave','drop'])
      drop.addEventListener(ev,e=>{{e.preventDefault();drop.classList.remove('hover')}});
    drop.addEventListener('drop',e=>{{
      if(e.dataTransfer.files.length){{fi.files=e.dataTransfer.files;
        document.getElementById('fname').textContent='📄 '+fi.files[0].name;}}
    }});
    </script>
    """)


def verdict_badge(plan_out: str) -> str:
    """Aus dem plan-Output ein klares Verdikt destillieren."""
    if "EXISTIERT BEREITS" in plan_out:
        return ("<span class='badge bad'>⛔ Existiert bereits</span> "
                "<span class='muted'>– Draft besser verwerfen oder in die "
                "bestehende Notiz ergänzen.</span>")
    if "ERGÄNZEN" in plan_out.upper():
        return ("<span class='badge warn'>✏️ Ähnliche Notiz vorhanden</span> "
                "<span class='muted'>– prüfen, ob Ergänzen besser ist als neu "
                "anlegen.</span>")
    return ("<span class='badge ok'>✅ Neues Wissen</span> "
            "<span class='muted'>– kein Duplikat gefunden.</span>")


def analyze_page(draft_rel: str, plan_out: str, note_warn: str | None = None,
                 route: dict | None = None):
    route = route or {}
    note_md = (ROOT / draft_rel).read_text(encoding="utf-8")
    warn_html = (f"<div class='card' style='border-color:#f59e0b'>⚠️ "
                 f"{html.escape(note_warn)}</div>") if note_warn else ""
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
    into_checked = "checked" if into_default and not sug_folder else ""
    new_checked = "" if into_checked else "checked"
    return page(f"""
    <p>{verdict_badge(plan_out)}</p>
    {warn_html}

    <h2>1 · Erzeugte Notiz <span class='muted'>(landet in deinem Silo)</span></h2>
    <details><summary>Vorschau anzeigen — {html.escape(draft_rel)}</summary>
    <pre>{html.escape(note_md.strip())}</pre></details>
    <details><summary>Details der Duplikat-/Ablage-Analyse</summary>
    <pre>{html.escape(plan_out.strip() or '(kein Output)')}</pre></details>

    <form method='POST' action='/promote' class='card' data-load>
      <input type='hidden' name='draft' value='{html.escape(draft_rel)}'>
      <h2 style='margin-top:0'>2 · In den Kanon übernehmen</h2>

      <div class='choice' id='c-new' onclick='mode("new")'>
        <label style='margin:0;cursor:pointer'>
          <input type='radio' name='mode' value='new' {new_checked}>
          🆕 Als neue Notiz anlegen</label>
        <div id='f-new' style='margin-top:.6rem'>
          <select name='folder'>{opts([''] + canon_folders(), sug_folder)}</select>
        </div>
      </div>

      <div class='choice' id='c-into' onclick='mode("into")'>
        <label style='margin:0;cursor:pointer'>
          <input type='radio' name='mode' value='into' {into_checked}>
          ✏️ Bestehende Notiz ergänzen</label>
        <div id='f-into' style='margin-top:.6rem'>
          <input name='into' value='{html.escape(into_default)}'
                 placeholder='Pfad, z. B. 03 Papers/NewsNet-SDF.md'>
        </div>
      </div>

      <label>Rückverlinken in <span class='muted'>(Pflicht – keine isolierten
      Notizen)</span></label>
      <select name='backlink'>{opts(bl, bl_default)}</select>

      <label style='font-weight:400'><input type='checkbox' name='push' value='1'
        style='width:auto'> gleich Branch + PR erstellen (push)</label>
      <p style='margin-bottom:0'>
        <button type='submit'>✅ Übernehmen</button>
        &nbsp;<a class='btn gray' href='/'>Abbrechen</a></p>
    </form>

    <form method='POST' action='/discard'>
      <input type='hidden' name='draft' value='{html.escape(draft_rel)}'>
      <button type='submit' style='background:var(--bad)'>🗑 Draft verwerfen</button>
      <span class='muted'> löscht nur die Silo-Datei, der Kanon bleibt unberührt</span>
    </form>

    <script>
    function mode(w){{
      document.getElementById('c-new').classList.toggle('on', w==='new');
      document.getElementById('c-into').classList.toggle('on', w==='into');
      document.querySelector('#c-new input[type=radio]').checked = (w==='new');
      document.querySelector('#c-into input[type=radio]').checked = (w==='into');
    }}
    mode(document.querySelector('input[name=mode]:checked').value);
    </script>
    """)


def result_page(out: str):
    m = re.search(r"(https://github\.com/\S+/compare/\S+)", out)
    pr = (f"<a class='btn' href='{html.escape(m.group(1))}' target='_blank'>"
          f"→ PR öffnen</a> ") if m else ""
    failed = ("FEHLER" in out.upper() or "ABBRUCH" in out.upper()
              or "TRACEBACK" in out.upper())
    head = ("<span class='badge bad'>❌ Fehlgeschlagen</span>" if failed
            else "<span class='badge ok'>✅ Übernommen</span>")
    return page(f"""
    <p>{head}</p>
    <details {"open" if failed else ""}><summary>Protokoll</summary>
    <pre>{html.escape(out.strip() or '(kein Output)')}</pre></details>
    <p>{pr}<a class='btn gray' href='/'>Nächstes Dokument</a></p>
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
            mode = f.get("mode", "")
            if mode == "into" and f.get("into"):
                cmd += ["--into", f["into"]]
            elif mode != "into" and f.get("folder"):
                cmd += ["--folder", f["folder"]]
            elif f.get("into"):   # Fallback ohne mode-Feld (alte Formulare)
                cmd += ["--into", f["into"]]
            else:
                return self._send(page("<p>Zielordner bzw. Notiz wählen. "
                                       "<a href='/'>zurück</a></p>"), 400)
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

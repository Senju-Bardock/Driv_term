#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trmdriv_es.py - Google Drive from the terminal (Linux, Windows, macOS).
Uses only the Python 3.8+ standard library. No pip, no dependencies.

FAST VERSION:
  - Several files at once (threads) for downloads and uploads.
  - Persistent HTTPS connections (no new handshake for every request).
  - Large files: downloaded in parallel parts (Range).
  - Folders: the recursive listing is done in batches and in parallel.
  - Small files: uploaded in a SINGLE request (multipart).
  - Large files: resumable upload with 16 MiB chunks and retries.
  - A single global progress bar (speed and remaining time).

Usage:   python3 trmdriv_es.py
         python3 trmdriv_es.py --reset-config   (deletes saved OAuth credentials)
Threads: environment variable DRIVE_WORKERS (default 8; try between 4 and 16).
         Windows PowerShell:  $env:DRIVE_WORKERS=12; python trmdriv_es.py
"""
import base64
import concurrent.futures as cf
import hashlib
import http.client
import http.server
import json
import mimetypes
import os
import random
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".trmdriv_es")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TOKENS_FILE = os.path.join(CONFIG_DIR, "tokens.json")

SCOPE = "https://www.googleapis.com/auth/drive"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/drive/v3"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"

FOLDER = "application/vnd.google-apps.folder"
SHORTCUT = "application/vnd.google-apps.shortcut"
GAPPS = "application/vnd.google-apps."

PAGE_SIZE = 15
MAX_TEXT = 1024 * 1024           # max text shown in the viewer

try:
    WORKERS = max(1, min(32, int(os.environ.get("DRIVE_WORKERS", "8"))))
except ValueError:
    WORKERS = 8
UP_CHUNK = 16 * 1024 * 1024      # resumable upload chunk (multiple of 256 KiB)
SMALL_UPLOAD = 5 * 1024 * 1024   # up to this size: a single multipart request
PART = 16 * 1024 * 1024          # size of each parallel download part
BIG_FILE = 2 * PART              # from this size a file is downloaded in parts
BUF = 1024 * 1024                # network read size
LIST_BATCH = 30                  # folders per query when listing in batch
RETRY_CODES = (0, 408, 429, 500, 502, 503, 504)
NET_ERRORS = (ConnectionError, socket.timeout, ssl.SSLError, http.client.HTTPException)
CANCEL = threading.Event()       # set on Ctrl+C to stop the threads

EXPORTS = {
    "document": [("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                 ("pdf", "application/pdf"), ("txt", "text/plain")],
    "spreadsheet": [("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    ("csv", "text/csv"), ("pdf", "application/pdf")],
    "presentation": [("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
                     ("pdf", "application/pdf"), ("txt", "text/plain")],
    "drawing": [("png", "image/png"), ("pdf", "application/pdf")],
}
TEXT_MIMES = {"application/json", "application/xml", "application/javascript", "application/x-sh",
              "application/x-yaml", "application/sql", "application/x-httpd-php"}
TEXT_EXTS = {".txt", ".md", ".py", ".log", ".csv", ".json", ".yml", ".yaml", ".ini", ".cfg", ".sh", ".js",
             ".ts", ".html", ".css", ".xml", ".c", ".cpp", ".h", ".java", ".rs", ".go", ".toml", ".sql",
             ".tsv", ".conf", ".bat", ".ps1", ".rb", ".php"}

HELP = ("  [numero] abrir | b atras | h inicio | n/p pagina | s buscar | c compartidos conmigo\n"
        "  d N descargar carpeta/archivo (ej: d 3) | u subir | m nueva carpeta\n"
        "  r recargar | x cerrar sesion | q salir   (Ctrl+C cancela una transferencia)")


# ----------------------------------------------------------------- utilities
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_json(path, data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0


def fmt_time(s):
    s = int(max(0, s))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return ("%d:%02d:%02d" % (h, m, sec)) if h else ("%02d:%02d" % (m, sec))


def pause():
    try:
        input("\nEnter para continuar...")
    except EOFError:
        pass


def safe_name(name):
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    # stripping trailing dots avoids names like ".." (path traversal) and Windows issues
    return name.strip().rstrip(". ") or "sin_nombre"


def unique_path(path):
    base, ext = os.path.splitext(path)
    n, p = 1, path
    while os.path.exists(p):
        p = "%s (%d)%s" % (base, n, ext)
        n += 1
    return p


def reserve(directory, name, used):
    """Pick a free name inside 'directory' (on disk and among already reserved names)."""
    base, ext = os.path.splitext(name)
    n, cand = 1, name
    while cand.lower() in used or os.path.exists(os.path.join(directory, cand)):
        cand = "%s (%d)%s" % (base, n, ext)
        n += 1
    used.add(cand.lower())
    return os.path.join(directory, cand)


def ask_path(prompt):
    return input(prompt).strip().strip('"').strip("'")


def ask_dest():
    default = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(default):
        default = os.getcwd()
    return os.path.expanduser(ask_path("Carpeta destino [%s]: " % default) or default)


def open_external(path):
    try:
        if os.name == "nt":
            os.startfile(path)  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  Abierto con el visor del sistema: %s" % path)
    except Exception:
        print("  No pude abrirlo automaticamente. Esta guardado en: %s" % path)


def pager(text, title=""):
    size = shutil.get_terminal_size((80, 24))
    width, height = max(size.columns - 1, 20), max(size.lines - 3, 5)
    lines = []
    for ln in text.expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(ln, width, replace_whitespace=False, drop_whitespace=False) or [""])
    clear()
    print("--- %s ---" % title)
    i = 0
    while i < len(lines):
        print("\n".join(lines[i:i + height]))
        i += height
        if i >= len(lines):
            break
        try:
            if input("-- Enter: seguir | q: salir -- ").strip().lower() == "q":
                break
        except EOFError:
            break
    if not lines:
        print("(vacio)")


class DriveError(Exception):
    def __init__(self, code, body=""):
        self.code = code
        msg = body
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            try:
                d = json.loads(body)
                msg = d.get("error_description") or d.get("error") or body
            except Exception:
                pass
        super().__init__(("[%s] %s" % (code, msg)) if code else str(msg))


class Progress:
    """GLOBAL progress bar, safe to use from several threads."""

    def __init__(self, label, files, total):
        self.label, self.files, self.total = label, files, total
        self.files_done, self.done = 0, 0
        self.errors = []
        self.lock = threading.Lock()
        self.t0 = time.time()
        self.last_draw = 0.0
        self.last_t, self.last_b, self.speed = self.t0, 0, 0.0

    def add(self, n):
        with self.lock:
            self.done += n
            self._draw()

    def file_done(self):
        with self.lock:
            self.files_done += 1
            self._draw()

    def fail(self, name, err):
        with self.lock:
            self.errors.append((name, str(err)))

    def _draw(self, force=False):
        now = time.time()
        if not force and now - self.last_draw < 0.15:
            return
        self.last_draw = now
        if now - self.last_t >= 0.5:
            inst = (self.done - self.last_b) / (now - self.last_t)
            self.speed = inst if self.speed <= 0 else 0.7 * self.speed + 0.3 * inst
            self.last_t, self.last_b = now, self.done
        line = "  %s %d/%d archivos  %s" % (self.label, self.files_done, self.files, human(max(self.done, 0)))
        if self.total:
            pct = min(100, max(0, self.done) * 100 // self.total)
            line += " / %s  %d%%" % (human(self.total), pct)
        if self.speed > 0:
            line += "  %s/s" % human(self.speed)
            if self.total and self.done < self.total:
                line += "  ETA %s" % fmt_time((self.total - self.done) / self.speed)
        cols = shutil.get_terminal_size((100, 24)).columns - 1
        sys.stdout.write("\r" + line[:cols].ljust(cols))
        sys.stdout.flush()

    def finish(self):
        with self.lock:
            if not self.files:
                return
            self._draw(force=True)
            el = max(time.time() - self.t0, 0.001)
            sys.stdout.write("\n  Terminado en %s (media %s/s)\n" % (fmt_time(el), human(max(self.done, 0) / el)))
            sys.stdout.flush()


def run_parallel(fn, items, workers=WORKERS):
    """Run fn(item) in a thread pool. On Ctrl+C (or any other error) cancel what is pending."""
    CANCEL.clear()
    ex = cf.ThreadPoolExecutor(max_workers=max(1, min(workers, len(items) or 1)))
    futs = [ex.submit(fn, it) for it in items]
    try:
        for f in cf.as_completed(futs):
            f.result()
    except BaseException:
        CANCEL.set()
        for f in futs:
            f.cancel()
        raise
    finally:
        ex.shutdown(wait=True)


# ----------------------------------------------------------------- OAuth
def post_form(url, form):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(form).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise DriveError(e.code, e.read().decode("utf-8", "replace"))


class Auth:
    def __init__(self, cfg, email):
        self.cfg, self.email = cfg, email
        self.access, self.exp = None, 0
        self.lock = threading.Lock()     # several threads request a token at once

    def invalidate(self):
        self.access = None

    def token(self):
        with self.lock:
            if self.access and time.time() < self.exp - 60:
                return self.access
            rt = load_json(TOKENS_FILE).get(self.email.lower(), {}).get("refresh_token")
            if rt:
                try:
                    d = post_form(TOKEN_URL, {"client_id": self.cfg["client_id"],
                                              "client_secret": self.cfg["client_secret"],
                                              "refresh_token": rt, "grant_type": "refresh_token"})
                    self.access = d["access_token"]
                    self.exp = time.time() + int(d.get("expires_in", 3600))
                    return self.access
                except DriveError as e:
                    if e.code not in (400, 401):
                        raise
                    print("La sesion guardada caduco; hay que autorizar de nuevo.")
            self.login()
            return self.access

    def forget(self):
        t = load_json(TOKENS_FILE)
        t.pop(self.email.lower(), None)
        save_json(TOKENS_FILE, t)
        self.access = None

    def login(self):
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(16)
        box = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}
                if "code" not in q and "error" not in q:
                    self.send_response(404)
                    self.end_headers()
                    return
                box.update(q)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<html><body style='font-family:sans-serif'><h2>Listo</h2>"
                                 "<p>Ya puedes cerrar esta pestana y volver a la terminal.</p>"
                                 "</body></html>".encode("utf-8"))

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        srv.timeout = 2
        redirect = "http://127.0.0.1:%d" % srv.server_address[1]
        url = AUTH_URL + "?" + urllib.parse.urlencode({
            "client_id": self.cfg["client_id"], "redirect_uri": redirect, "response_type": "code",
            "scope": SCOPE, "code_challenge": challenge, "code_challenge_method": "S256",
            "access_type": "offline", "prompt": "consent", "login_hint": self.email, "state": state})

        print("\nGoogle no permite iniciar sesion con contrasena desde programas externos.")
        print("Hay que autorizar UNA vez en el navegador (despues queda guardado).")
        print("Si no se abre solo, copia este enlace en cualquier navegador de ESTE equipo:\n\n%s\n" % url)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        print("Esperando autorizacion (max. 5 min)... Ctrl+C para cancelar.")
        deadline = time.time() + 300
        while "code" not in box and "error" not in box and time.time() < deadline:
            srv.handle_request()
        srv.server_close()

        if "error" in box:
            raise DriveError(0, "Autorizacion rechazada: %s" % box["error"])
        if "code" not in box:
            raise DriveError(0, "Tiempo de espera agotado.")
        if box.get("state") != state:
            raise DriveError(0, "Respuesta de autorizacion invalida.")

        d = post_form(TOKEN_URL, {"client_id": self.cfg["client_id"], "client_secret": self.cfg["client_secret"],
                                  "code": box["code"], "code_verifier": verifier,
                                  "redirect_uri": redirect, "grant_type": "authorization_code"})
        self.access = d["access_token"]
        self.exp = time.time() + int(d.get("expires_in", 3600))

        req = urllib.request.Request(API + "/about?fields=user(emailAddress)",
                                     headers={"Authorization": "Bearer " + self.access})
        with urllib.request.urlopen(req, timeout=30) as r:
            real = json.load(r)["user"]["emailAddress"]
        if real.lower() != self.email.lower():
            print("AVISO: iniciaste sesion con %s (no con %s). Se usara %s." % (real, self.email, real))
            self.email = real
        if d.get("refresh_token"):
            t = load_json(TOKENS_FILE)
            t[real.lower()] = {"refresh_token": d["refresh_token"]}
            save_json(TOKENS_FILE, t)


def ensure_config():
    cfg = load_json(CONFIG_FILE)
    if cfg.get("client_id") and cfg.get("client_secret"):
        return cfg
    print("""=== Configuracion inicial (solo la primera vez) ===
Para acceder a TU Drive necesitas tus propias credenciales OAuth (gratis):
 1. Entra en https://console.cloud.google.com/ y crea un proyecto.
 2. APIs y servicios > Biblioteca > activa "Google Drive API".
 3. APIs y servicios > Pantalla de consentimiento OAuth: tipo "Externo" y,
    en "Usuarios de prueba", anade tu propio correo.
 4. Credenciales > Crear credenciales > ID de cliente de OAuth >
    tipo de aplicacion "Aplicacion de escritorio".
 5. Descarga el JSON (o copia el ID y el secreto).
""")
    p = ask_path("Ruta del JSON descargado (o Enter para pegar ID y secreto a mano): ")
    if p:
        data = load_json(os.path.expanduser(p))
        data = data.get("installed") or data.get("web") or {}
        cid, sec = data.get("client_id", ""), data.get("client_secret", "")
    else:
        cid = input("client_id: ").strip()
        sec = input("client_secret: ").strip()
    if not cid or not sec:
        print("Credenciales no validas.")
        sys.exit(1)
    cfg = {"client_id": cid, "client_secret": sec}
    save_json(CONFIG_FILE, cfg)
    print("Guardado en %s\n" % CONFIG_FILE)
    return cfg


# ----------------------------------------------------------------- HTTP
class Http:
    """HTTP layer with persistent HTTPS connections (one per thread and host).

    Reusing the connection avoids repeating DNS + TCP + TLS on every request,
    which is what hurts the most with many small files.
    Rule: ALWAYS read the whole response (or call reset()) before the next
    request in the same thread."""

    GOOGLE_SUFFIXES = (".googleapis.com", ".googleusercontent.com", ".google.com")

    def __init__(self, auth):
        self.auth = auth
        self.local = threading.local()

    def _conns(self):
        c = getattr(self.local, "conns", None)
        if c is None:
            c = self.local.conns = {}
        return c

    def reset(self):
        c = self._conns()
        for conn in c.values():
            try:
                conn.close()
            except Exception:
                pass
        c.clear()

    def _drop(self, host):
        conn = self._conns().pop(host, None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    def send(self, url, method="GET", data=None, headers=None, follow=True, retries=6):
        """Return the response (status < 400) UNREAD. Retries transient errors."""
        last_code, last_msg = 0, ""
        refreshed, attempt, redirects = False, 0, 0
        while attempt < retries:
            u = urllib.parse.urlsplit(url)
            host = u.netloc
            path = u.path + (("?" + u.query) if u.query else "")
            h = {"Authorization": "Bearer " + self.auth.token(), "Accept-Encoding": "identity"}
            h.update(headers or {})
            try:
                conns = self._conns()
                conn = conns.get(host)
                if conn is None:
                    conn = conns[host] = http.client.HTTPSConnection(host, timeout=300)
                conn.request(method, path, body=data, headers=h)
                r = conn.getresponse()
            except (OSError, http.client.HTTPException) as e:
                self._drop(host)
                last_code, last_msg = 0, str(e)
                time.sleep(0 if attempt == 0 else min(2 ** attempt, 20))
                attempt += 1
                continue
            st = r.status
            loc = r.getheader("Location")
            if follow and st in (301, 302, 303, 307, 308) and loc and redirects < 5:
                r.read()
                new = urllib.parse.urljoin(url, loc)
                nh = urllib.parse.urlsplit(new).hostname or ""
                if not nh.endswith(self.GOOGLE_SUFFIXES):
                    raise DriveError(0, "Redireccion a un servidor no esperado: %s" % nh)
                url = new
                redirects += 1
                continue
            if st < 400:
                return r
            body = r.read().decode("utf-8", "replace")
            if st == 401 and not refreshed:
                refreshed = True
                self.auth.invalidate()
                continue
            if st in (429, 500, 502, 503, 504) or (st == 403 and "ateLimit" in body):
                last_code, last_msg = st, body
                time.sleep(min(2 ** attempt, 20) + random.random())
                attempt += 1
                continue
            raise DriveError(st, body)
        raise DriveError(last_code, last_msg or "Sin conexion o el servidor no responde.")


# ----------------------------------------------------------------- Drive
class FileJob:
    """A file to download (may be split into several parts)."""

    def __init__(self, f, target, export=None):
        self.f, self.target, self.export = f, target, export
        self.tmp = target + ".part"
        self.size = 0 if export else int(f.get("size") or 0)
        self.lock = threading.Lock()
        self.remaining = 0
        self.error = None
        self.done = False


class Drive:
    def __init__(self, auth):
        self.auth = auth
        self.http = Http(auth)

    def call(self, path, params=None, method="GET", body=None):
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data, headers = None, {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=UTF-8"
        r = self.http.send(url, method, data, headers)
        raw = r.read()
        return json.loads(raw) if raw else {}

    # ---- listing
    def _list_q(self, q, order=True):
        out, token = [], None
        while True:
            params = {"q": q, "pageSize": 1000,
                      "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,parents,shortcutDetails)",
                      "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
            if order:
                params["orderBy"] = "folder,name"
            if token:
                params["pageToken"] = token
            d = self.call("/files", params)
            out.extend(d.get("files", []))
            token = d.get("nextPageToken")
            if not token:
                return out

    def list(self, kind, ident):
        if kind == "shared":
            q = "sharedWithMe = true and trashed = false"
        elif kind == "search":
            term = ident.replace("\\", "\\\\").replace("'", "\\'")
            q = "name contains '%s' and trashed = false" % term
        else:
            q = "'%s' in parents and trashed = false" % ident
        return self._list_q(q)

    def list_children(self, ids):
        """List the contents of MANY folders with few queries (batches in parallel)."""
        out = {i: [] for i in ids}
        batches = [ids[i:i + LIST_BATCH] for i in range(0, len(ids), LIST_BATCH)]

        def one(batch):
            q = "(%s) and trashed = false" % " or ".join("'%s' in parents" % i for i in batch)
            return self._list_q(q, order=False)

        if len(batches) == 1:
            results = [one(batches[0])]
        else:
            with cf.ThreadPoolExecutor(min(WORKERS, len(batches))) as ex:
                results = list(ex.map(one, batches))
        for res in results:
            for f in res:
                for p in f.get("parents") or []:
                    if p in out:
                        out[p].append(f)
        return out

    # ---- download
    def _finish_part(self, job, prog):
        with job.lock:
            job.remaining -= 1
            last = job.remaining == 0
        if not last:
            return
        if job.error is None and not CANCEL.is_set():
            try:
                os.replace(job.tmp, job.target)
                job.done = True
                prog.file_done()
                return
            except OSError as e:
                job.error = e
        try:
            os.remove(job.tmp)
        except OSError:
            pass
        if job.error is not None:
            prog.fail(job.f["name"], job.error)

    def _dl_task(self, task, prog):
        job, start, end = task
        if not (CANCEL.is_set() or job.error):
            try:
                if job.export:
                    self._fetch_export(job, prog)
                else:
                    self._fetch_range(job, start, end, prog)
            except Exception as e:      # one failure must not bring down the remaining files
                job.error = e
        self._finish_part(job, prog)

    def _fetch_range(self, job, start, end, prog):
        url = "%s/files/%s?alt=media&supportsAllDrives=true" % (API, job.f["id"])
        pos, fails = start, 0
        with open(job.tmp, "r+b") as fh:
            while pos <= end:
                if CANCEL.is_set():
                    return
                try:
                    r = self.http.send(url, headers={"Range": "bytes=%d-%d" % (pos, end)})
                    if r.status == 200 and pos != 0:
                        self.http.reset()
                        raise DriveError(0, "El servidor no admite descargas por trozos.")
                    fh.seek(pos)
                    remaining = end - pos + 1
                    while remaining > 0:
                        if CANCEL.is_set():
                            self.http.reset()
                            return
                        b = r.read(min(BUF, remaining))
                        if not b:
                            raise ConnectionError("Conexion cortada por el servidor.")
                        fh.write(b)
                        pos += len(b)
                        remaining -= len(b)
                        prog.add(len(b))
                    if r.status == 200:      # server sent more than requested: do not reuse the connection
                        self.http.reset()
                except NET_ERRORS as e:
                    fails += 1
                    self.http.reset()
                    if fails > 5:
                        raise DriveError(0, "Descarga interrumpida: %s" % e)
                    time.sleep(min(2 ** fails, 15))

    def _fetch_export(self, job, prog):
        ext, mime = job.export
        url = "%s/files/%s/export?%s" % (API, job.f["id"], urllib.parse.urlencode({"mimeType": mime}))
        for attempt in range(4):
            added = 0
            try:
                r = self.http.send(url)
                with open(job.tmp, "wb") as fh:
                    while True:
                        if CANCEL.is_set():
                            self.http.reset()
                            return
                        b = r.read(BUF)
                        if not b:
                            break
                        fh.write(b)
                        added += len(b)
                        prog.add(len(b))
                cl = r.getheader("Content-Length")
                if cl and cl.isdigit() and added != int(cl):
                    raise ConnectionError("Descarga incompleta.")
                return
            except NET_ERRORS as e:
                self.http.reset()
                prog.add(-added)
                if attempt == 3:
                    raise DriveError(0, "Descarga interrumpida: %s" % e)
                time.sleep(2 ** attempt)

    def run_downloads(self, jobs):
        """Download all FileJobs in parallel. Large files are split into parts."""
        jobs = sorted(jobs, key=lambda j: -j.size)          # largest first
        prog = Progress("Descargando", len(jobs), sum(j.size for j in jobs))
        tasks = []
        for job in jobs:
            try:
                if job.export:
                    job.remaining = 1
                    tasks.append((job, None, None))
                elif job.size == 0:
                    open(job.target, "wb").close()
                    job.done = True
                    prog.file_done()
                else:
                    n = -(-job.size // PART) if job.size >= BIG_FILE else 1
                    job.remaining = n
                    with open(job.tmp, "wb") as fh:
                        fh.truncate(job.size)
                    for i in range(n):
                        s = i * PART
                        e = min(job.size, s + PART) - 1 if n > 1 else job.size - 1
                        tasks.append((job, s, e))
            except OSError as e:
                job.error = e
                prog.fail(job.f["name"], e)
        try:
            run_parallel(lambda t: self._dl_task(t, prog), tasks)
        finally:
            for job in jobs:                                 # clean up .part files if cancelled
                if not job.done and os.path.exists(job.tmp):
                    try:
                        os.remove(job.tmp)
                    except OSError:
                        pass
            prog.finish()
        return {"ok": prog.files_done, "fail": [n for n, _ in prog.errors], "errors": prog.errors}

    def download(self, f, dest_dir, export=None):
        os.makedirs(dest_dir, exist_ok=True)
        name = safe_name(f["name"])
        if export and not name.lower().endswith("." + export[0]):
            name += "." + export[0]
        target = unique_path(os.path.join(dest_dir, name))
        st = self.run_downloads([FileJob(f, target, export)])
        if st["errors"]:
            raise DriveError(0, st["errors"][0][1])
        return target

    def download_folder(self, folder_id, name, dest_dir):
        """Download a whole folder (recursive). Native Google files are exported
        to the first format in EXPORTS (docx/xlsx/pptx/png or pdf)."""
        root = unique_path(os.path.join(dest_dir, safe_name(name)))
        os.makedirs(root, exist_ok=True)
        print("Carpeta: %s" % root)
        sys.stdout.write("  Leyendo estructura...")
        sys.stdout.flush()
        jobs, level = [], [(folder_id, root)]
        while level:
            kids = self.list_children([fid for fid, _ in level])
            nxt = []
            for fid, local in level:
                used = set()
                for f in kids.get(fid, []):
                    mt = f["mimeType"]
                    if mt == SHORTCUT:
                        continue            # shortcuts are skipped (avoids loops)
                    if mt == FOLDER:
                        sub = reserve(local, safe_name(f["name"]), used)
                        os.makedirs(sub, exist_ok=True)
                        nxt.append((f["id"], sub))
                        continue
                    export, fname = None, safe_name(f["name"])
                    if mt.startswith(GAPPS):
                        export = EXPORTS.get(mt[len(GAPPS):], [("pdf", "application/pdf")])[0]
                        if not fname.lower().endswith("." + export[0]):
                            fname += "." + export[0]
                    jobs.append(FileJob(f, reserve(local, fname, used), export))
            level = nxt
        print(" %d archivos." % len(jobs))
        return root, self.run_downloads(jobs)

    # ---- viewer
    def view(self, f):
        mt, name = f["mimeType"], f["name"]
        if mt.startswith(GAPPS):
            key = mt[len(GAPPS):]
            if key in ("document", "presentation", "spreadsheet"):
                mime = "text/csv" if key == "spreadsheet" else "text/plain"
                url = "%s/files/%s/export?%s" % (API, f["id"], urllib.parse.urlencode({"mimeType": mime}))
                data = self.http.send(url).read(MAX_TEXT)
                self.http.reset()
                title = name + (" (solo la primera hoja)" if key == "spreadsheet" else "")
                pager(data.decode("utf-8", "replace").lstrip("\ufeff"), title)
                return
            exp = ("png", "image/png") if key == "drawing" else ("pdf", "application/pdf")
            open_external(self.download(f, tempfile.mkdtemp(prefix="drive_term_"), exp))
            return
        size = int(f.get("size") or 0)
        ext = os.path.splitext(name)[1].lower()
        is_text = mt.startswith("text/") or mt in TEXT_MIMES or ext in TEXT_EXTS
        if is_text:
            data = b""
            if size:
                url = "%s/files/%s?alt=media&supportsAllDrives=true" % (API, f["id"])
                data = self.http.send(url, headers={"Range": "bytes=0-%d" % (MAX_TEXT - 1)}).read(MAX_TEXT)
                self.http.reset()
            txt = data.decode("utf-8", "replace").lstrip("\ufeff")
            if size > MAX_TEXT:
                txt += "\n\n[... mostrado solo el primer MB de %s; descarga el archivo para verlo entero ...]" % human(size)
            pager(txt, name)
            return
        if size > 100 * 1024 * 1024:
            if input("Pesa %s. Descargar para abrirlo? [s/N]: " % human(size)).strip().lower() != "s":
                return
        open_external(self.download(f, tempfile.mkdtemp(prefix="drive_term_")))

    # ---- upload
    def create_folder(self, name, parent):
        d = self.call("/files", {"fields": "id", "supportsAllDrives": "true"}, "POST",
                      {"name": name, "mimeType": FOLDER, "parents": [parent]})
        return d["id"]

    def upload_path(self, path, parent):
        """Upload a file or a whole folder. First creates the remote folders
        (level by level, in parallel) and then uploads all files at once."""
        path = os.path.abspath(path)
        files, skipped = [], []
        if os.path.isdir(path):
            print("  Preparando carpetas en Drive...")
            level = [(path, parent)]
            while level:
                ids = {}

                def mk(item, ids=ids):
                    if CANCEL.is_set():
                        return
                    ids[item[0]] = self.create_folder(os.path.basename(item[0]) or "carpeta", item[1])

                run_parallel(mk, level)
                nxt = []
                for local, _ in level:
                    fid = ids[local]
                    try:
                        with os.scandir(local) as it:
                            for e in sorted(it, key=lambda e: e.name.lower()):
                                try:
                                    if e.is_dir(follow_symlinks=False):
                                        nxt.append((e.path, fid))
                                    elif e.is_file():
                                        files.append((e.path, fid, e.stat().st_size))
                                except OSError:
                                    skipped.append(e.path)
                    except OSError:
                        skipped.append(local)
                level = nxt
        else:
            files.append((path, parent, os.path.getsize(path)))
        return self.upload_files(files, skipped)

    def upload_files(self, files, skipped=()):
        files = sorted(files, key=lambda x: -x[2])          # largest first
        prog = Progress("Subiendo", len(files), sum(s for _, _, s in files))
        fails = []

        def work(item):
            path, parent, size = item
            if CANCEL.is_set():
                return
            try:
                self.upload_file(path, parent, size, prog)
                if not CANCEL.is_set():
                    prog.file_done()
            except Exception as e:
                fails.append((os.path.basename(path), str(e)))

        try:
            run_parallel(work, files)
        finally:
            prog.finish()
        return {"ok": prog.files_done, "fail": [n for n, _ in fails], "errors": fails, "skipped": list(skipped)}

    def upload_file(self, path, parent, size, prog):
        name = os.path.basename(path)
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        meta = {"name": name, "parents": [parent]}

        if size <= SMALL_UPLOAD:
            # Small file: metadata + content in ONE request (half the network round trips).
            with open(path, "rb") as fh:
                content = fh.read()
            b = secrets.token_hex(16).encode()
            body = (b"--" + b + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
                    + json.dumps(meta).encode("utf-8")
                    + b"\r\n--" + b + b"\r\nContent-Type: " + mime.encode("ascii", "ignore") + b"\r\n\r\n"
                    + content + b"\r\n--" + b + b"--")
            r = self.http.send(UPLOAD_URL + "?uploadType=multipart&supportsAllDrives=true&fields=id", "POST", body,
                               {"Content-Type": 'multipart/related; boundary="%s"' % b.decode()})
            r.read()
            prog.add(len(content))
            return

        # Large file: resumable session, big chunks over a persistent connection.
        r = self.http.send(UPLOAD_URL + "?uploadType=resumable&supportsAllDrives=true&fields=id", "POST",
                           json.dumps(meta).encode("utf-8"),
                           {"Content-Type": "application/json; charset=UTF-8",
                            "X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(size)})
        r.read()
        session = r.getheader("Location")
        if not session:
            raise DriveError(0, "Drive no devolvio la sesion de subida.")
        pos, fails, need_query = 0, 0, False
        with open(path, "rb") as fh:
            while pos < size:
                if CANCEL.is_set():
                    return
                try:
                    if need_query:
                        new = self._query_session(session, size)
                        need_query = False
                    else:
                        fh.seek(pos)
                        new = self._put_chunk(session, fh.read(UP_CHUNK), pos, size)
                except DriveError as e:
                    if e.code not in RETRY_CODES or fails >= 6:
                        raise
                    fails += 1
                    need_query = True       # after a failure, ask Drive how far it got
                    self.http.reset()
                    time.sleep(min(2 ** fails, 20))
                    continue
                prog.add(new - pos)
                pos = new

    @staticmethod
    def _session_pos(r, size):
        if r.status in (200, 201):
            return size
        if r.status == 308:
            rng = r.getheader("Range")      # "bytes=0-N"
            return int(rng.split("-")[-1]) + 1 if rng else 0
        raise DriveError(r.status, "Respuesta inesperada de Drive.")

    def _put_chunk(self, session, chunk, pos, size):
        end = pos + len(chunk) - 1
        r = self.http.send(session, "PUT", chunk,
                           {"Content-Length": str(len(chunk)),
                            "Content-Range": "bytes %d-%d/%d" % (pos, end, size)},
                           follow=False, retries=1)
        r.read()
        return self._session_pos(r, size)

    def _query_session(self, session, size):
        r = self.http.send(session, "PUT", b"",
                           {"Content-Length": "0", "Content-Range": "bytes */%d" % size},
                           follow=False, retries=1)
        r.read()
        return self._session_pos(r, size)


# ----------------------------------------------------------------- interface
def resolve(f):
    sd = f.get("shortcutDetails")
    if f["mimeType"] == SHORTCUT and sd:
        g = dict(f)
        g["id"], g["mimeType"] = sd["targetId"], sd.get("targetMimeType", "")
        return g
    return f


def row(i, f, namew):
    mt = f["mimeType"]
    tag = "DIR" if mt == FOLDER else "LNK" if mt == SHORTCUT else "GDOC" if mt.startswith(GAPPS) else "FILE"
    size = human(int(f["size"])) if f.get("size") else "-"
    name = f["name"]
    if len(name) > namew:
        name = name[:namew - 1] + "~"
    return "%4d  %-4s  %-*s  %9s  %s" % (i, tag, namew, name, size, (f.get("modifiedTime") or "")[:10])


def file_menu(drive, f):
    """Return True if the listing changed."""
    while True:
        clear()
        print("Archivo : %s" % f["name"])
        print("Tipo    : %s" % f["mimeType"])
        if f.get("size"):
            print("Tamano  : %s" % human(int(f["size"])))
        print("\n  1) Ver      2) Descargar      3) Informacion")
        print("  4) Mover a la papelera           0) Volver")
        op = input("\n> ").strip()
        try:
            if op == "1":
                drive.view(f)
                pause()
            elif op == "2":
                default = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.isdir(default):
                    default = os.getcwd()
                dest = ask_path("Carpeta destino [%s]: " % default) or default
                export = None
                if f["mimeType"].startswith(GAPPS):
                    opts = EXPORTS.get(f["mimeType"][len(GAPPS):], [("pdf", "application/pdf")])
                    print("Formato de exportacion: " + "  ".join("%d) %s" % (i + 1, o[0]) for i, o in enumerate(opts)))
                    sel = input("Elige [1]: ").strip() or "1"
                    export = opts[int(sel) - 1] if sel.isdigit() and 1 <= int(sel) <= len(opts) else opts[0]
                print("Guardado en: %s" % drive.download(f, os.path.expanduser(dest), export))
                pause()
            elif op == "3":
                d = drive.call("/files/" + f["id"], {
                    "fields": "id,name,mimeType,size,createdTime,modifiedTime,webViewLink,owners(displayName,emailAddress)",
                    "supportsAllDrives": "true"})
                print()
                for k, v in d.items():
                    if k == "owners":
                        v = ", ".join("%s <%s>" % (o.get("displayName", ""), o.get("emailAddress", "")) for o in v)
                    print("  %-12s %s" % (k, v))
                pause()
            elif op == "4":
                if input("Mover '%s' a la papelera? [s/N]: " % f["name"]).strip().lower() == "s":
                    drive.call("/files/" + f["id"], {"supportsAllDrives": "true"}, "PATCH", {"trashed": True})
                    print("Movido a la papelera.")
                    pause()
                    return True
            elif op in ("0", ""):
                return False
        except KeyboardInterrupt:
            print("\nCancelado.")
            pause()
        except (DriveError, OSError, ValueError) as e:
            print("\nError: %s" % e)
            pause()


def summary(st, what):
    msg = "%s: %d archivos" % (what, st["ok"])
    if st["fail"]:
        msg += ", %d con error" % len(st["fail"])
        msg += "\n   Fallaron: " + ", ".join(st["fail"][:5])
        msg += "\n   Motivo del primero: " + st["errors"][0][1]
    if st.get("skipped"):
        msg += "\n   Omitidos (sin permiso/ilegibles): %d" % len(st["skipped"])
    return msg


def browse(drive, root_id):
    stack = [("folder", root_id, "Mi unidad")]
    items, page, notice = None, 0, ""
    while True:
        kind, ident, _ = stack[-1]
        if items is None:
            clear()
            print("Cargando...")
            try:
                items = drive.list(kind, ident)
            except DriveError as e:
                items, notice = [], "Error: %s" % e
            page = 0
        pages = max(1, -(-len(items) // PAGE_SIZE))
        page = max(0, min(page, pages - 1))
        cols = shutil.get_terminal_size((100, 24)).columns
        namew = max(20, min(cols - 38, 80))
        clear()
        print("=== Drive: %s ===" % drive.auth.email)
        print("Ruta: %s\n" % " / ".join(s[2] for s in stack))
        print("%4s  %-4s  %-*s  %9s  %s" % ("#", "Tipo", namew, "Nombre", "Tamano", "Modificado"))
        print("-" * min(cols - 1, namew + 36))
        start = page * PAGE_SIZE
        for i, f in enumerate(items[start:start + PAGE_SIZE], start + 1):
            print(row(i, f, namew))
        if not items:
            print("  (vacio)")
        print("\nPagina %d/%d - %d elementos\n%s" % (page + 1, pages, len(items), HELP))
        if notice:
            print("\n>> " + notice)
            notice = ""
        try:
            cmd = input("\n> ").strip()
        except EOFError:
            return "quit"
        low = cmd.lower()
        try:
            if low in ("q", "salir"):
                return "quit"
            elif low == "x":
                return "logout"
            elif low == "b":
                if len(stack) > 1:
                    stack.pop()
                    items = None
            elif low == "h":
                stack = stack[:1]
                items = None
            elif low == "r":
                items = None
            elif low == "n":
                page += 1
            elif low == "p":
                page -= 1
            elif low == "c":
                stack = stack[:1] + [("shared", "", "Compartido conmigo")]
                items = None
            elif low == "s":
                term = input("Buscar nombre que contenga: ").strip()
                if term:
                    stack.append(("search", term, "Busqueda: " + term))
                    items = None
            elif low == "m":
                if kind != "folder":
                    notice = "Solo se pueden crear carpetas dentro de una carpeta."
                else:
                    name = input("Nombre de la nueva carpeta: ").strip()
                    if name:
                        drive.create_folder(name, ident)
                        items, notice = None, "Carpeta creada."
            elif low == "u":
                if kind != "folder":
                    notice = "Entra primero en una carpeta para subir ahi."
                else:
                    p = ask_path("Ruta local del archivo o carpeta (Enter = cancelar): ")
                    if p:
                        p = os.path.expanduser(p)
                        if not os.path.exists(p):
                            notice = "No existe: %s" % p
                        else:
                            st = drive.upload_path(p, ident)
                            items, notice = None, summary(st, "Subida completada")
            elif low.startswith("d ") and low[2:].strip().isdigit():
                n = int(low[2:].strip())
                if not 1 <= n <= len(items):
                    notice = "Numero fuera de rango."
                else:
                    f = resolve(items[n - 1])
                    dest = ask_dest()
                    if f["mimeType"] == FOLDER:
                        local, st = drive.download_folder(f["id"], f["name"], dest)
                        notice = summary(st, "Carpeta descargada en %s" % local)
                    else:
                        export = None
                        if f["mimeType"].startswith(GAPPS):
                            export = EXPORTS.get(f["mimeType"][len(GAPPS):], [("pdf", "application/pdf")])[0]
                        notice = "Guardado en: %s" % drive.download(f, dest, export)
            elif low.isdigit():
                n = int(low)
                if not 1 <= n <= len(items):
                    notice = "Numero fuera de rango."
                else:
                    f = resolve(items[n - 1])
                    if f["mimeType"] == FOLDER:
                        stack.append(("folder", f["id"], f["name"]))
                        items = None
                    elif file_menu(drive, f):
                        items = None
            elif cmd:
                notice = "Comando no reconocido."
        except KeyboardInterrupt:
            print()
            items, notice = None, "Transferencia cancelada."
        except (DriveError, OSError) as e:
            notice = "Error: %s" % e


def main():
    if "--reset-config" in sys.argv:
        for p in (CONFIG_FILE, TOKENS_FILE):
            if os.path.exists(p):
                os.remove(p)
        print("Credenciales borradas.")
        return 0
    if os.name == "nt":
        os.system("")  # enables ANSI sequences in Windows consoles
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    cfg = ensure_config()
    print("=== Google Drive en la terminal ===\n")
    email = input("email: ").strip()
    if "@" not in email:
        print("Correo no valido.")
        return 1
    auth = Auth(cfg, email)
    drive = Drive(auth)
    try:
        about = drive.call("/about", {"fields": "user(displayName,emailAddress),storageQuota(limit,usage)"})
        root_id = drive.call("/files/root", {"fields": "id"})["id"]
    except DriveError as e:
        print("No se pudo conectar: %s" % e)
        return 1
    q = about.get("storageQuota", {})
    print("\nConectado como %s" % about["user"].get("emailAddress", email))
    if q.get("usage"):
        print("Espacio usado: %s%s" % (human(int(q["usage"])),
                                       (" de " + human(int(q["limit"]))) if q.get("limit") else ""))
    print("Transferencias en paralelo: %d hilos (DRIVE_WORKERS para cambiarlo)" % WORKERS)
    time.sleep(1.2)

    result = browse(drive, root_id)
    if result == "logout":
        auth.forget()
        print("Sesion cerrada y token borrado de este equipo.")
    else:
        print("Hasta luego.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
    except (urllib.error.URLError, DriveError) as e:
        print("\nError: %s" % e)
        sys.exit(1)

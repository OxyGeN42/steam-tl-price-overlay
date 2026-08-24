"""
Steam TL Price Overlay v3 (profesyonel surum)
================================================
Steam magaza/sepet/istek listesi sayfalarindaki HER USD fiyatini kendi
gercek degeriyle okuyup, guncel doviz kuruyla TL karsiligini yaninda
gosterir. Steam client Chromium/CEF tabanli oldugu icin bu, "remote
debugging" ile disaridan JS calistirarak yapilir.

ONEMLI TASARIM NOTU
--------------------
Onceki surumlerde tek appid'in Steam API fiyati cekilip sayfadaki TUM
fiyatlarin yanina ayni deger yaziliyordu (paket/bundle sayfalarinda yanlis
sonuc veriyordu). Bu surumde artik Steam API'sine hic gerek yok: JS,
sayfada gordugu her "$XX.XX" metnini kendi degeriyle okuyup kur ile
carpiyor. Bu sayede tek appid, paket, sepet, istek listesi, arama
sonuclari -- hepsi doğru sekilde calisir.

------------------------------------------------------------------
ILK KURULUM (bir kere yapilir)
------------------------------------------------------------------
1) Steam'i tamamen kapat (sistem tepsisinden de cikis yap).
2) Remote debugging dosyasini olustur:
       python steam_tl_price_overlay.py --setup "C:\\Program Files (x86)\\Steam"
3) Kutuphaneleri kur:
       pip install websocket-client requests
4) Steam'i tekrar ac.
5) Test icin elle calistir:
       python steam_tl_price_overlay.py --debug
   Bir magaza sayfasi ac, fiyatlarin yaninda TL rozeti belirmeli.

------------------------------------------------------------------
OTOMATIK BASLATMA (bir kere kurulur, sonra hic dokunmazsin)
------------------------------------------------------------------
       python steam_tl_price_overlay.py --install
Windows baslangicina, konsolsuz calisacak sekilde eklenir. Bilgisayar her
acildiginda arka planda otomatik baslar, Steam'i bekler.

Kaldirmak icin:
       python steam_tl_price_overlay.py --uninstall

Loglar: %LOCALAPPDATA%\\SteamTLOverlay\\overlay.log
------------------------------------------------------------------
"""

import argparse
import json
import os
import sys
import time
import traceback

import requests
import websocket

CEF_PORT = 8080
CEF_BASE = f"http://localhost:{CEF_PORT}"

# Kur yalnizca sistem baslatildiginda bir kez alinir, yeniden baslangica kadar sabit kalir.

APPDATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "SteamTLOverlay")
LOG_FILE = os.path.join(APPDATA_DIR, "overlay.log")
INSTALLED_SCRIPT = os.path.join(APPDATA_DIR, "steam_tl_price_overlay.py")

DEBUG = False


def log(msg, to_file_only=False):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    if not to_file_only:
        try:
            print(line)
        except Exception:
            pass
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


RATE_CACHE_FILE = os.path.join(APPDATA_DIR, "rate_cache.json")


def _save_rate_cache(rate: float):
    """Kuru diske kaydet (bir sonraki baslatmada fallback olarak kullanilir)."""
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        with open(RATE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"rate": rate, "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, f)
    except Exception:
        pass


def _load_rate_cache() -> float:
    """Onceden kaydedilmis kuru diskten yukle. Bulunamazsa 0.0 doner."""
    try:
        with open(RATE_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        rate = float(data.get("rate", 0.0))
        saved_at = data.get("saved_at", "?")
        log(f"[*] Onceki kayitli kur kullaniliyor: 1 USD = {rate:.4f} TL (kaydedilme: {saved_at})")
        return rate
    except Exception:
        return 0.0


def get_usd_try_rate():
    """Kuru API'den ceker; basarisiz olursa disk cache'ten yukler."""
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        rate = r.json()["rates"]["TRY"]
        _save_rate_cache(rate)  # Basarili cekildi, diske kaydet
        log(f"[*] Baslangic kuru alindi: 1 USD = {rate:.4f} TL (sistem yeniden baslatilana kadar bu kur kullanilir)")
        return rate
    except Exception as e:
        log(f"[!] Kur alinamadi: {e} -- Disk cache'ten yuklenmeye calisiliyor...")
        return _load_rate_cache()


def build_inject_js(rate):
    """
    Sayfadaki her '$XX.XX' fiyatini kendi degeriyle okur, kur ile carpar.
    3 katmanli badge sistemi:
      - Orijinal (ustu cizgili) fiyat -> soluk gri badge
      - Indirimli / gercek fiyat      -> mavi accent badge
      - Tasarruf miktari              -> yesil badge (sadece indirim varsa)
    """
    return f"""
    (function() {{
        var RATE = {rate};
        var re = /\\$\\s?([\\d,]+\\.\\d{{2}})/;

        // --- Stil sabitleri ---
        // Gercek / indirimli fiyat (mavi)
        var BADGE_STYLE = [
            'display:inline',
            'margin-left:5px',
            'padding:1px 5px 1px 4px',
            'background:rgba(10,26,40,0.90)',
            'border-left:3px solid #66c0f4',
            'border-radius:2px',
            'font-size:0.83em',
            'font-weight:600',
            'color:#e8f4fd',
            'white-space:nowrap',
            'letter-spacing:0.01em'
        ].join(';');
        var SYM_STYLE = 'color:#66c0f4;font-weight:700;margin-right:2px;';

        // Orijinal (ustu cizgili) fiyat (soluk gri - ne kadar dustu gosterir)
        var ORIG_BADGE_STYLE = [
            'display:inline',
            'margin-left:4px',
            'padding:0 3px',
            'font-size:0.78em',
            'font-weight:500',
            'color:rgba(155,155,155,0.70)',
            'white-space:nowrap'
        ].join(';');
        var ORIG_SYM_STYLE = 'color:rgba(130,130,130,0.65);margin-right:1px;';

        // --- Orijinal fiyat tespiti ---
        var ORIG_CLASSES = ['original_price', 'discount_original_price', 'strike'];
        function isOriginalPrice(el) {{
            var cur = el;
            for (var i = 0; i < 5; i++) {{
                if (!cur) break;
                var cn = (typeof cur.className === 'string') ? cur.className : '';
                for (var s = 0; s < ORIG_CLASSES.length; s++) {{
                    if (cn.indexOf(ORIG_CLASSES[s]) !== -1) return true;
                }}
                try {{
                    if ((window.getComputedStyle(cur).textDecoration || '').indexOf('line-through') !== -1) return true;
                }} catch(e) {{}}
                cur = cur.parentElement;
            }}
            return false;
        }}

        // --- FAZ 1: Tum USD fiyatlarini yuru, badge ekle ---
        var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
        var count = 0;
        var node;
        while ((node = walker.nextNode())) {{
            if (!node.nodeValue) continue;
            var m = node.nodeValue.match(re);
            if (!m) continue;
            var parent = node.parentElement;
            if (!parent) continue;
            if (parent.dataset && parent.dataset.tlOverlayDone === m[0]) continue;

            var usdVal = parseFloat(m[1].replace(/,/g, ''));
            if (isNaN(usdVal)) continue;
            var tlVal = usdVal * RATE;
            var tlFmt = tlVal.toLocaleString('tr-TR', {{minimumFractionDigits:2, maximumFractionDigits:2}});

            // Mevcut badge varsa kaldir
            var prevBadge = node.nextSibling;
            if (prevBadge && prevBadge.classList && prevBadge.classList.contains('tl-overlay-badge')) {{
                prevBadge.remove();
            }}

            var isOrig = isOriginalPrice(parent);

            var badge = document.createElement('span');
            badge.className = 'tl-overlay-badge';
            badge.style.cssText = isOrig ? ORIG_BADGE_STYLE : BADGE_STYLE;
            badge.dataset.tlTry = String(tlVal);
            badge.dataset.tlIsOrig = isOrig ? '1' : '0';

            var sym = document.createElement('span');
            sym.style.cssText = isOrig ? ORIG_SYM_STYLE : SYM_STYLE;
            sym.textContent = '\u20ba';

            // Orijinal fiyatta 'TL' yazisi gosterme (compactlik icin)
            badge.appendChild(sym);
            badge.appendChild(document.createTextNode(tlFmt + (isOrig ? '' : ' TL')));

            node.parentNode.insertBefore(badge, node.nextSibling);
            if (parent.dataset) parent.dataset.tlOverlayDone = m[0];
            count++;
        }}

        // --- FAZ 2: Tasarruf badge'lari ---
        // Her orijinal badge icin, ortak container'da final badge ara; farki hesapla
        var origBadges = document.querySelectorAll('.tl-overlay-badge[data-tl-is-orig="1"]');
        for (var ob = 0; ob < origBadges.length; ob++) {{
            var origBadge = origBadges[ob];
            var container = origBadge.parentElement;
            for (var d = 0; d < 8; d++) {{
                if (!container) break;
                var finalBadge = container.querySelector('.tl-overlay-badge[data-tl-is-orig="0"]');
                if (finalBadge) {{
                    var origTL  = parseFloat(origBadge.dataset.tlTry);
                    var finalTL = parseFloat(finalBadge.dataset.tlTry);
                    var savings = origTL - finalTL;
                    if (savings > 0.5) {{
                        // Daha once eklenmemisse ekle
                        var nextEl = finalBadge.nextSibling;
                        if (!nextEl || !nextEl.classList || !nextEl.classList.contains('tl-savings-badge')) {{
                            var sb = document.createElement('span');
                            sb.className = 'tl-savings-badge';
                            sb.style.cssText = SAVE_STYLE;
                            var savFmt = savings.toLocaleString('tr-TR', {{minimumFractionDigits:0, maximumFractionDigits:0}});
                            sb.textContent = '\u2193 -\u20ba' + savFmt + ' tasarruf';
                            finalBadge.parentNode.insertBefore(sb, finalBadge.nextSibling);
                        }}
                    }}
                    break;
                }}
                container = container.parentElement;
            }}
        }}

        return 'injected:' + count;
    }})();
    """



class CefTab:
    def __init__(self, tab_info):
        self.id = tab_info["id"]
        self.url = tab_info["url"]
        self.ws_url = tab_info["webSocketDebuggerUrl"]
        self.ws = None
        self._msg_id = 0

    def connect(self):
        self.ws = websocket.create_connection(self.ws_url, timeout=10)

    def send(self, method, params=None):
        self._msg_id += 1
        payload = {"id": self._msg_id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(payload))
        return json.loads(self.ws.recv())

    def eval_js(self, js):
        return self.send("Runtime.evaluate", {"expression": js})

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass


def get_all_tabs():
    r = requests.get(f"{CEF_BASE}/json", timeout=5)
    return r.json()


def get_store_tabs():
    tabs = get_all_tabs()
    # Magaza, sepet, istek listesi, paket sayfalari -- steampowered.com altindaki her sey
    return [t for t in tabs if "steampowered.com" in t.get("url", "") and t.get("type") == "page"]


def process_tab(tab_info, rate):
    tab = CefTab(tab_info)
    try:
        tab.connect()
        result = tab.eval_js(build_inject_js(rate))
        result_node = result.get("result", {})
        exc = result_node.get("exceptionDetails")
        if exc:
            desc = exc.get("exception", {}).get("description", str(exc))
            log(f"[!] JS hatasi ({tab_info.get('url')}): {desc}")
            if DEBUG:
                log(f"[debug] Ham CDP yaniti: {json.dumps(result)}", to_file_only=True)
            return
        ret_value = result_node.get("result", {}).get("value", "(deger okunamadi)")
        if DEBUG:
            log(f"[debug] {tab_info.get('url')} -> {ret_value}")
        elif ret_value not in ("injected:0", "(deger okunamadi)"):
            log(f"[+] {tab_info.get('url')} -> {ret_value}")
    except Exception as e:
        log(f"[!] Enjeksiyon hatasi ({tab_info.get('url')}): {e}")
        if DEBUG:
            log(traceback.format_exc(), to_file_only=True)
    finally:
        tab.close()


def watch_loop(interval=2):
    log("[*] Baslangic kuru aliniyor...")
    rate = get_usd_try_rate()
    if not rate:
        log("[!] Kur alinamadi, sistem durduruldu. Internet baglantisini kontrol et.")
        return
    log(f"[*] Steam sayfalari izleniyor... Kur: 1 USD = {rate:.4f} TL (Ctrl+C ile durdur)")
    while True:
        try:
            tabs = get_store_tabs()
            if DEBUG:
                log(f"[debug] {len(tabs)} sekme bulundu.")
            for t in tabs:
                process_tab(t, rate)
        except requests.exceptions.ConnectionError:
            log("[!] Port 8080'e baglanilamadi. Steam kapali olabilir, bekleniyor...", to_file_only=not DEBUG)
        except Exception as e:
            log(f"[!] Beklenmeyen hata: {e}")
        time.sleep(interval)


def setup_debug_file(steam_path):
    path = os.path.join(steam_path, ".cef-enable-remote-debugging")
    try:
        open(path, "w").close()
        print(f"[+] Olusturuldu: {path}")
        print("[*] Simdi Steam'i tamamen kapatip (tepsi ikonundan da cikis yap) tekrar acmalisin.")
    except Exception as e:
        print(f"[!] Dosya olusturulamadi: {e}")
        print("[*] Yonetici olarak acilmis CMD'de tekrar dene.")


def install_startup():
    import shutil

    os.makedirs(APPDATA_DIR, exist_ok=True)
    shutil.copyfile(os.path.abspath(__file__), INSTALLED_SCRIPT)

    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_dir, "SteamTLOverlay.vbs")

    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.Run """{pythonw}"" ""{INSTALLED_SCRIPT}""", 0, False\n'
    )
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        print(f"[+] Kalici script: {INSTALLED_SCRIPT}")
        print(f"[+] Baslangic girisi olusturuldu: {vbs_path}")
        print("[*] Bilgisayari yeniden baslattiginda script arka planda, konsolsuz calisacak.")
        print(f"[*] Simdi elle baslatmak icin cift tikla: {vbs_path}")
        print(f"[*] Loglari buradan takip edebilirsin: {LOG_FILE}")
    except Exception as e:
        print(f"[!] Baslangic girisi olusturulamadi: {e}")


def uninstall_startup():
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_dir, "SteamTLOverlay.vbs")
    if os.path.exists(vbs_path):
        os.remove(vbs_path)
        print(f"[+] Baslangic girisi kaldirildi: {vbs_path}")
    else:
        print("[*] Zaten kurulu degildi.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steam icin gercek kurla TL fiyat overlay araci")
    parser.add_argument("--setup", metavar="STEAM_PATH", help="CEF remote debugging dosyasini olusturur")
    parser.add_argument("--interval", type=int, default=2, help="Tarama araligi (saniye, varsayilan 2)")
    parser.add_argument("--debug", action="store_true", help="Detayli log goster")
    parser.add_argument("--install", action="store_true", help="Windows acilisinda otomatik, konsolsuz baslat")
    parser.add_argument("--uninstall", action="store_true", help="Otomatik baslatmayi kaldirir")
    args = parser.parse_args()

    DEBUG = args.debug

    if args.setup:
        setup_debug_file(args.setup)
        sys.exit(0)

    if args.install:
        install_startup()
        sys.exit(0)

    if args.uninstall:
        uninstall_startup()
        sys.exit(0)

    watch_loop(args.interval)
"""
SHelper — Профессиональная утилита для обхода вредоносного ПО и винлокеров
Opensource Windows Recovery Utility
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import subprocess
import os
import sys
import threading
import shutil
from pathlib import Path
from datetime import datetime

# ─── Проверка прав администратора ───────────────────────────────────────────
def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    import ctypes
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f'"{os.path.abspath(__file__)}"', None, 1
        )
        sys.exit(0)

# ─── Цветовая схема (сайт SHelper: чёрный + зелёный/циан) ──────────────────
C = {
    "bg":        "#0b0b0b",
    "bg2":       "#0f0f0f",
    "panel":     "#111111",
    "card":      "#151515",
    "card2":     "#1a1a1a",
    "border":    "#1e2e20",
    "green":     "#00ff88",
    "green_dim": "#00cc66",
    "cyan":      "#00d4ff",
    "cyan_dim":  "#0099bb",
    "yellow":    "#ffcc00",
    "red":       "#ff4455",
    "text":      "#d0d0d0",
    "text_dim":  "#555555",
    "text_mid":  "#888888",
    "log_bg":    "#050505",
}

FONT_MONO   = ("Consolas", 9)
FONT_MONO_B = ("Consolas", 9, "bold")
FONT_MONO_S = ("Consolas", 8)
FONT_MONO_L = ("Consolas", 11, "bold")
FONT_BIG    = ("Consolas", 18, "bold")


# ════════════════════════════════════════════════════════════════════════════
class SHelperApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SHelper — Windows Recovery Utility")
        self.root.geometry("1200x780")
        self.root.minsize(950, 620)
        self.root.configure(bg=C["bg"])

        try:
            ico_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass

        self.admin     = is_admin()
        self.on_top_v  = tk.BooleanVar(value=False)
        self._log_lock = threading.Lock()

        self._setup_ttk_styles()
        self._build_header()
        self._build_body()
        self._build_statusbar()

        self.log("SHelper инициализирован", "info")
        if self.admin:
            self.log("[+] Запущен с правами администратора", "ok")
        else:
            self.log("[!] Нет прав администратора — часть функций недоступна", "warn")
            self.log("    Перезапустите от имени администратора (ПКМ → Запуск от администратора)", "dim")

    # ─── TTK стили ──────────────────────────────────────────────────────────
    def _setup_ttk_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("TNotebook",
            background=C["bg"], borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab",
            background=C["panel"], foreground=C["text_dim"],
            padding=[16, 8], font=FONT_MONO_B, borderwidth=0)
        s.map("TNotebook.Tab",
            background=[("selected", C["card"]), ("active", C["card2"])],
            foreground=[("selected", C["green"]), ("active", C["text"])])

        s.configure("Vertical.TScrollbar",
            background=C["panel"], troughcolor=C["bg2"],
            borderwidth=0, arrowcolor=C["text_dim"],
            relief=tk.FLAT)
        s.map("Vertical.TScrollbar",
            background=[("active", C["card2"])])

        s.configure("TFrame", background=C["bg"])
        s.configure("TSeparator", background=C["border"])

    # ─── Хедер ──────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["bg2"], height=58)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        # Лого
        logo = tk.Frame(hdr, bg=C["bg2"])
        logo.pack(side=tk.LEFT, padx=20)
        tk.Label(logo, text="S", fg=C["green"], bg=C["bg2"],
                 font=("Consolas", 24, "bold")).pack(side=tk.LEFT)
        tk.Label(logo, text="HELPER", fg=C["text"], bg=C["bg2"],
                 font=("Consolas", 15, "bold")).pack(side=tk.LEFT, padx=(1, 0))

        tk.Label(hdr, text="// WINDOWS RECOVERY UTILITY",
                 fg=C["text_dim"], bg=C["bg2"], font=FONT_MONO_S).pack(side=tk.LEFT, padx=12)

        # Правая часть хедера
        right = tk.Frame(hdr, bg=C["bg2"])
        right.pack(side=tk.RIGHT, padx=18)

        # Бэйдж admin
        admin_txt   = "● ADMIN" if self.admin else "● NO ADMIN"
        admin_color = C["green"] if self.admin else C["red"]
        tk.Label(right, text=admin_txt, fg=admin_color, bg=C["bg2"],
                 font=FONT_MONO_B).pack(side=tk.LEFT, padx=14)

        # Запрос UAC
        if not self.admin:
            tk.Button(right, text="Получить права ↑",
                      command=self._elevate,
                      fg=C["yellow"], bg=C["card2"],
                      activeforeground=C["yellow"], activebackground=C["card"],
                      font=FONT_MONO_S, relief=tk.FLAT, bd=0,
                      padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Поверх окон
        def _toggle_top():
            self.root.attributes("-topmost", self.on_top_v.get())
        cb = tk.Checkbutton(right, text="Поверх окон", variable=self.on_top_v,
                            command=_toggle_top,
                            fg=C["text_dim"], bg=C["bg2"],
                            selectcolor=C["bg2"], activebackground=C["bg2"],
                            activeforeground=C["cyan"], font=FONT_MONO_S, cursor="hand2")
        cb.pack(side=tk.LEFT, padx=6)

        # Разделитель под хедером
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill=tk.X)

    # ─── Основная область ────────────────────────────────────────────────────
    def _build_body(self):
        pw = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                            bg=C["bg"], sashwidth=4,
                            sashrelief=tk.FLAT, bd=0)
        pw.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(pw, bg=C["bg"])
        right = tk.Frame(pw, bg=C["bg2"])
        pw.add(left,  minsize=680)
        pw.add(right, minsize=240)

        self._build_tabs(left)
        self._build_log_panel(right)

    # ─── Вкладки ─────────────────────────────────────────────────────────────
    def _build_tabs(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill=tk.BOTH, expand=True)

        pages = [
            ("🚀  Автозагрузка", self._page_startup),
            ("🔓  Блокировки",   self._page_unlock),
            ("🛡️  Восстановление", self._page_recovery),
            ("⚙️  Система",      self._page_system),
            ("🧹  Очистка",      self._page_cleanup),
            ("💾  Диски",        self._page_disks),
            ("👤  Пользователи", self._page_users),
            ("🔗  Ассоциации",   self._page_assoc),
        ]
        for label, builder in pages:
            f = tk.Frame(nb, bg=C["card"])
            nb.add(f, text=label)
            builder(f)

    # ─── Лог-консоль ─────────────────────────────────────────────────────────
    def _build_log_panel(self, parent):
        tk.Frame(parent, bg=C["bg2"], height=1).pack(fill=tk.X)

        top = tk.Frame(parent, bg=C["bg2"])
        top.pack(fill=tk.X, padx=10, pady=(8, 2))
        tk.Label(top, text="// КОНСОЛЬ", fg=C["cyan"],
                 bg=C["bg2"], font=FONT_MONO_B).pack(side=tk.LEFT)
        tk.Button(top, text="× очистить", command=self._clear_log,
                  fg=C["text_dim"], bg=C["bg2"], font=FONT_MONO_S,
                  relief=tk.FLAT, bd=0, cursor="hand2",
                  activeforeground=C["red"], activebackground=C["bg2"]).pack(side=tk.RIGHT)

        self.log_text = tk.Text(parent, bg=C["log_bg"], fg=C["green"],
                                font=("Consolas", 8), wrap=tk.WORD,
                                bd=0, relief=tk.FLAT,
                                insertbackground=C["green"],
                                selectbackground="#1a3a2a",
                                state=tk.DISABLED, padx=8, pady=6)
        scr = ttk.Scrollbar(parent, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scr.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=(0, 6))
        scr.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 6), padx=(0, 2))

        self.log_text.tag_config("ok",   foreground=C["green"])
        self.log_text.tag_config("warn", foreground=C["yellow"])
        self.log_text.tag_config("err",  foreground=C["red"])
        self.log_text.tag_config("info", foreground=C["cyan"])
        self.log_text.tag_config("dim",  foreground=C["text_dim"])

    def _build_statusbar(self):
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill=tk.X)
        bar = tk.Frame(self.root, bg=C["bg2"], height=26)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="Готов")
        tk.Label(bar, textvariable=self.status_var,
                 fg=C["text_dim"], bg=C["bg2"], font=FONT_MONO_S,
                 anchor=tk.W).pack(side=tk.LEFT, padx=12)
        tk.Label(bar, text="Opensource // github.com/konikc/-SHelper---Opensource-project",
                 fg=C["text_dim"], bg=C["bg2"], font=FONT_MONO_S).pack(side=tk.RIGHT, padx=12)

    # ════════════════════════════════════════════════════════════════════════
    #  Вспомогательные виджеты
    # ════════════════════════════════════════════════════════════════════════
    def _scrollable_frame(self, parent) -> tk.Frame:
        canvas = tk.Canvas(parent, bg=C["card"], highlightthickness=0, bd=0)
        vsb    = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner  = tk.Frame(canvas, bg=C["card"])
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        def _mw(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", _mw)
        return inner

    def _section(self, parent: tk.Frame, title: str) -> tk.Frame:
        wrap = tk.Frame(parent, bg=C["panel"], bd=0)
        wrap.pack(fill=tk.X, padx=14, pady=(6, 0))

        hdr = tk.Frame(wrap, bg=C["panel"])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=title, fg=C["cyan"], bg=C["panel"],
                 font=FONT_MONO_B).pack(side=tk.LEFT, padx=12, pady=(8, 4))

        sep = tk.Frame(wrap, bg=C["border"], height=1)
        sep.pack(fill=tk.X, padx=8)

        body = tk.Frame(wrap, bg=C["panel"])
        body.pack(fill=tk.X, padx=8, pady=6)
        return body

    def _btn(self, parent: tk.Frame, text: str, cmd,
             color: str = None, danger: bool = False,
             full: bool = False, icon: str = "") -> tk.Button:
        c  = C["red"] if danger else (color or C["green"])
        ab = "#2a0000" if danger else "#0a2a14"
        label = f"{icon}  {text}" if icon else text
        b = tk.Button(parent, text=label, command=cmd,
                      fg=c, bg=C["card2"],
                      activeforeground=c, activebackground=ab,
                      font=FONT_MONO_S, relief=tk.FLAT, bd=0,
                      padx=12, pady=6, cursor="hand2",
                      highlightbackground=c, highlightthickness=1)
        if full:
            b.pack(fill=tk.X, padx=4, pady=2)
        else:
            b.pack(side=tk.LEFT, padx=4, pady=4)
        return b

    def _warn_label(self, parent: tk.Frame, text: str):
        tk.Label(parent, text=f"⚠  {text}",
                 fg=C["yellow"], bg=C["panel"],
                 font=FONT_MONO_S, anchor=tk.W).pack(
                     anchor=tk.W, padx=6, pady=2)

    # ════════════════════════════════════════════════════════════════════════
    #  Лог / статус
    # ════════════════════════════════════════════════════════════════════════
    def log(self, msg: str, tag: str = "ok"):
        ts = datetime.now().strftime("%H:%M:%S")
        with self._log_lock:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{ts}] ", "dim")
            self.log_text.insert(tk.END, msg + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _status(self, msg: str):
        self.status_var.set(msg)

    # ════════════════════════════════════════════════════════════════════════
    #  Выполнение команд
    # ════════════════════════════════════════════════════════════════════════
    def _run(self, cmd: str, show_output: bool = True,
             as_admin: bool = False) -> str:
        self.log(f"$ {cmd}", "dim")
        self._status(f"Выполнение: {cmd[:60]}...")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, encoding="cp866", errors="replace"
            )
            out = (result.stdout + result.stderr).strip()
            if show_output and out:
                for line in out.splitlines()[:60]:
                    self.log(f"  {line}", "ok")
            self._status("Готов")
            return out
        except Exception as e:
            self.log(f"[ОШИБКА] {e}", "err")
            self._status("Ошибка")
            return ""

    def _run_thread(self, cmd: str, label: str = ""):
        self.log(f"→ {label or cmd}", "info")
        threading.Thread(target=self._run, args=(cmd,), daemon=True).start()

    def _run_visible(self, cmd: str):
        """Запуск в новом видимом cmd-окне"""
        self.log(f"$ {cmd}", "dim")
        os.popen(f'start cmd /k "{cmd}"')

    def _open_file(self, path: str):
        try:
            os.startfile(path)
        except Exception as e:
            self.log(f"[!] {e}", "err")

    def _elevate(self):
        run_as_admin()

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Автозагрузка
    # ════════════════════════════════════════════════════════════════════════
    def _page_startup(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        # --- Реестр Run ---
        s = self._section(inner, "// РЕЕСТР — АВТОЗАГРУЗКА")
        self._btn(s, "Run (HKCU)",   lambda: self._reg_show(
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"))
        self._btn(s, "Run (HKLM)",   lambda: self._reg_show(
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"))
        self._btn(s, "RunOnce (HKCU)", lambda: self._reg_show(
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce"))
        self._btn(s, "RunOnce (HKLM)", lambda: self._reg_show(
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"))

        s2 = self._section(inner, "// Winlogon / AppInit_DLLs")
        self._btn(s2, "Winlogon",     lambda: self._reg_show(
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"))
        self._btn(s2, "AppInit_DLLs", self._show_appinit)
        self._btn(s2, "Очистить AppInit_DLLs", self._clear_appinit, danger=True)

        s3 = self._section(inner, "// ПАПКА АВТОЗАГРУЗКИ")
        self._btn(s3, "Startup (текущий пользователь)",
                  lambda: self._open_file(
                      os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")))
        self._btn(s3, "Startup (все пользователи)",
                  lambda: self._open_file(
                      os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup")))

        s4 = self._section(inner, "// ПЛАНИРОВЩИК ЗАДАЧ")
        self._btn(s4, "Список задач",        self._list_tasks)
        self._btn(s4, "Удалить задачу...",   self._delete_task, danger=True)
        self._btn(s4, "taskschd.msc",        lambda: self._run("taskschd.msc"))

        s5 = self._section(inner, "// СЛУЖБЫ Windows")
        self._btn(s5, "Список служб",        self._list_services)
        self._btn(s5, "Запустить службу...", self._start_service)
        self._btn(s5, "Остановить службу...",self._stop_service)
        self._btn(s5, "Удалить службу...",   self._delete_service, danger=True)
        self._btn(s5, "services.msc",        lambda: self._run("services.msc"))

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Блокировки
    # ════════════════════════════════════════════════════════════════════════
    def _page_unlock(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// DisallowRun — ЗАПРЕТ ЗАПУСКА ПРОГРАММ")
        self._btn(s, "Показать DisallowRun", self._show_disallowrun)
        self._btn(s, "Очистить DisallowRun", self._clear_disallowrun, danger=True)

        s2 = self._section(inner, "// Debuggers — ПОДМЕНА ПРИЛОЖЕНИЙ (Image File Execution Options)")
        self._btn(s2, "Показать Debuggers", self._show_debuggers)
        self._btn(s2, "Очистить Debuggers", self._clear_debuggers, danger=True)

        s3 = self._section(inner, "// ScancodeMap — ПЕРЕНАЗНАЧЕНИЕ КЛАВИШ")
        self._btn(s3, "Показать ScancodeMap", self._show_scancodemap)
        self._btn(s3, "Сбросить ScancodeMap", self._clear_scancodemap, danger=True)

        s4 = self._section(inner, "// HOSTS FILE — БЛОКИРОВКА САЙТОВ")
        self._btn(s4, "Просмотреть Hosts",   self._view_hosts)
        self._btn(s4, "Открыть в Блокноте",  self._open_hosts_notepad)
        self._btn(s4, "Восстановить Hosts",  self._restore_hosts, danger=True)

        self._warn_label(s4, "Восстановление перезапишет hosts стандартным содержимым Windows")

        s5 = self._section(inner, "// ОГРАНИЧЕНИЯ РЕЕСТРА (Policies)")
        self._btn(s5, "Показать ограничения Explorer", self._show_policies)
        self._btn(s5, "Снять DisableTaskMgr", self._enable_taskmgr)
        self._btn(s5, "Снять DisableRegistryTools", self._enable_regedit)
        self._btn(s5, "Снять DisableCMD", self._enable_cmd)

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Восстановление
    # ════════════════════════════════════════════════════════════════════════
    def _page_recovery(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// ЦЕЛОСТНОСТЬ СИСТЕМНЫХ ФАЙЛОВ")
        self._btn(s, "sfc /scannow",           self._sfc_scannow)
        self._btn(s, "DISM — Восстановить",    self._dism_restore)
        self._btn(s, "chkdsk C: /f /r",        self._chkdsk_schedule)

        s2 = self._section(inner, "// ЭКРАН ВХОДА — LogonUI / ТЕМА")
        self._btn(s2, "Восстановить LogonUI",    self._restore_logonui)
        self._btn(s2, "Вернуть стандартную тему",self._restore_theme)
        self._btn(s2, "Починить шрифты",         self._fix_fonts)

        s3 = self._section(inner, "// РАСКЛАДКА И ЯЗЫК")
        self._btn(s3, "Вернуть русский язык (RU)",  self._restore_russian)
        self._btn(s3, "Открыть Language Settings",
                  lambda: self._run("control intl.cpl"))

        s4 = self._section(inner, "// ПРОВОДНИК И ОБОЛОЧКА")
        self._btn(s4, "Перезапустить Explorer",     self._restart_explorer)
        self._btn(s4, "Восстановить Shell в реестре", self._restore_shell)
        self._btn(s4, "Альтернативный Explorer...", self._alt_explorer)

        s5 = self._section(inner, "// WinRE — СРЕДА ВОССТАНОВЛЕНИЯ")
        self._btn(s5, "Войти в WinRE",          self._enter_winre, danger=True)
        self._btn(s5, "Сохранить конфиг WinRE", self._save_winre_cfg)
        self._btn(s5, "Восстановить WinRE",     self._restore_winre)
        self._btn(s5, "reagentc /info",          self._reagent_info)

        s6 = self._section(inner, "// ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ")
        self._btn(s6, "Выйти из сеанса",          self._logoff)
        self._btn(s6, "Открыть cmd (Admin)",       self._open_cmd_admin)
        self._btn(s6, "Открыть PowerShell (Admin)",self._open_ps_admin)
        self._btn(s6, "msconfig",                  lambda: self._run("msconfig"))

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Система
    # ════════════════════════════════════════════════════════════════════════
    def _page_system(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// UAC — КОНТРОЛЬ УЧЁТНЫХ ЗАПИСЕЙ")
        self._btn(s, "Включить UAC",              self._enable_uac)
        self._btn(s, "Отключить UAC (опасно!)",   self._disable_uac, danger=True)
        self._btn(s, "Статус UAC",                self._show_uac_status)
        self._btn(s, "UserAccountControlSettings",
                  lambda: self._run("UserAccountControlSettings.exe"))

        s2 = self._section(inner, "// ТЕСТОВЫЙ РЕЖИМ ДРАЙВЕРОВ (Test Mode)")
        self._btn(s2, "Выключить тестовый режим",  self._disable_test_mode)
        self._btn(s2, "Включить подписанные драйверы", self._enable_driver_signing)
        self._btn(s2, "Статус загрузчика (bcdedit)", self._show_boot_status)

        s3 = self._section(inner, "// ЗАМЕНА sethc / utilman")
        self._warn_label(s3, "Только для WinRE! Открывает cmd на экране блокировки.")
        self._btn(s3, "Заменить sethc → cmd",      self._replace_sethc, danger=True)
        self._btn(s3, "Заменить utilman → cmd",     self._replace_utilman, danger=True)
        self._btn(s3, "Восстановить sethc",         self._restore_sethc)
        self._btn(s3, "Восстановить utilman",       self._restore_utilman)

        s4 = self._section(inner, "// ПРАВА НА ФАЙЛ")
        self._btn(s4, "Взять права на файл...",    self._take_ownership)
        self._btn(s4, "Полный доступ к файлу...",  self._full_access)

        s5 = self._section(inner, "// БЫСТРЫЙ ДОСТУП")
        self._btn(s5, "Добавить в PATH",            self._add_to_path)
        self._btn(s5, "Добавить в контекстное меню",self._add_context_menu)

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Очистка
    # ════════════════════════════════════════════════════════════════════════
    def _page_cleanup(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// ВРЕМЕННЫЕ ФАЙЛЫ")
        self._btn(s, "Temp пользователя",   self._clean_user_temp)
        self._btn(s, "Temp системный",      self._clean_sys_temp, danger=True)
        self._btn(s, "Prefetch",            self._clean_prefetch)
        self._btn(s, "Recent",              self._clean_recent)

        s2 = self._section(inner, "// ОЧИСТКА КОРЗИНЫ")
        self._btn(s2, "Очистить корзину",   self._clean_recycle, danger=True)

        s3 = self._section(inner, "// КЭШ БРАУЗЕРОВ")
        self._btn(s3, "Chrome",   self._clean_chrome)
        self._btn(s3, "Edge",     self._clean_edge)
        self._btn(s3, "Firefox",  self._clean_firefox)

        s4 = self._section(inner, "// СТОРОННИЕ ДРАЙВЕРЫ")
        self._btn(s4, "Список сторонних драйверов", self._list_3rd_drivers)
        self._btn(s4, "Удалить драйвер...",         self._delete_driver, danger=True)

        s5 = self._section(inner, "// Встроенная очистка Windows")
        self._btn(s5, "cleanmgr", lambda: self._run("cleanmgr"))
        self._btn(s5, "Показать размер Temp-папок", self._show_temp_sizes)

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Диски
    # ════════════════════════════════════════════════════════════════════════
    def _page_disks(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// УПРАВЛЕНИЕ ДИСКАМИ")
        self._btn(s, "diskmgmt.msc",       lambda: self._run("diskmgmt.msc"))
        self._btn(s, "Список дисков",      self._list_disks)
        self._btn(s, "Список томов",       self._list_volumes)
        self._btn(s, "diskpart",           lambda: self._run_visible("diskpart"))

        s2 = self._section(inner, "// mbrRE — РЕЗЕРВНОЕ КОПИРОВАНИЕ MBR")
        self._warn_label(s2, "Операции с MBR выполняются на физическом диске — будьте осторожны!")
        self._btn(s2, "Сохранить MBR...",    self._mbr_backup)
        self._btn(s2, "Восстановить MBR...", self._mbr_restore, danger=True)
        self._btn(s2, "Исправить MBR (bootrec)", self._mbr_fix, danger=True)
        self._btn(s2, "Исправить BCD",           self._fix_bcd, danger=True)

        s3 = self._section(inner, "// ИНФОРМАЦИЯ О ДИСКАХ")
        self._btn(s3, "Место на дисках (wmic)",  self._disk_space)
        self._btn(s3, "SMART (wmic)",             self._disk_smart)

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Пользователи
    # ════════════════════════════════════════════════════════════════════════
    def _page_users(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ")
        self._btn(s, "Список пользователей",     self._list_users)
        self._btn(s, "Создать пользователя...",  self._create_user)
        self._btn(s, "Удалить пользователя...",  self._delete_user, danger=True)
        self._btn(s, "Сбросить пароль...",       self._reset_password)

        s2 = self._section(inner, "// ГРУППЫ")
        self._btn(s2, "Список администраторов",  self._list_admins)
        self._btn(s2, "Добавить в Admins...",    self._add_to_admins)
        self._btn(s2, "Убрать из Admins...",     self._remove_from_admins, danger=True)

        s3 = self._section(inner, "// GUI ИНСТРУМЕНТЫ")
        self._btn(s3, "lusrmgr.msc",  lambda: self._run("lusrmgr.msc"))
        self._btn(s3, "netplwiz",     lambda: self._run("netplwiz"))

    # ════════════════════════════════════════════════════════════════════════
    #  СТРАНИЦА: Ассоциации
    # ════════════════════════════════════════════════════════════════════════
    def _page_assoc(self, parent: tk.Frame):
        inner = self._scrollable_frame(parent)

        s = self._section(inner, "// ВОССТАНОВЛЕНИЕ АССОЦИАЦИЙ ФАЙЛОВ")
        exts = [
            (".exe", self._fix_exe),
            (".bat", self._fix_bat),
            (".txt", self._fix_txt),
            (".lnk", self._fix_lnk),
            (".reg", self._fix_reg),
            (".html",self._fix_html),
            (".msi", self._fix_msi),
        ]
        row = None
        for i, (ext, fn) in enumerate(exts):
            if i % 4 == 0:
                row = tk.Frame(s, bg=C["panel"])
                row.pack(fill=tk.X)
            self._btn(row, f"Восстановить {ext}", fn)

        s2 = self._section(inner, "// РЕЕСТР АССОЦИАЦИЙ")
        self._btn(s2, "Открыть HKCR в regedit", self._open_hkcr)
        self._btn(s2, "Экспорт HKCR в файл",    self._export_hkcr)
        self._btn(s2, "Показать текущие assoc",  self._show_assoc)

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — АВТОЗАГРУЗКА
    # ════════════════════════════════════════════════════════════════════════
    def _reg_show(self, key: str):
        self._run_thread(f'reg query "{key}"', f"Запрос реестра: {key}")

    def _show_appinit(self):
        self._reg_show(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows")

    def _clear_appinit(self):
        if messagebox.askyesno("Подтверждение", "Очистить AppInit_DLLs?"):
            self._run(r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" '
                      r'/v AppInit_DLLs /t REG_SZ /d "" /f')
            self.log("[+] AppInit_DLLs очищен", "ok")

    def _list_tasks(self):
        self._run_thread("schtasks /query /fo LIST /v", "Список задач планировщика")

    def _delete_task(self):
        name = simpledialog.askstring("Удалить задачу", "Введите имя задачи:")
        if name:
            self._run_thread(f'schtasks /delete /tn "{name}" /f', f"Удаление задачи: {name}")

    def _list_services(self):
        self._run_thread("sc query type= all state= all", "Список служб")

    def _start_service(self):
        name = simpledialog.askstring("Запуск службы", "Имя службы:")
        if name:
            self._run_thread(f'sc start "{name}"', f"Запуск: {name}")

    def _stop_service(self):
        name = simpledialog.askstring("Остановить службу", "Имя службы:")
        if name:
            self._run_thread(f'sc stop "{name}"', f"Остановка: {name}")

    def _delete_service(self):
        name = simpledialog.askstring("Удалить службу", "Имя службы:")
        if name and messagebox.askyesno("Подтверждение", f"Удалить службу '{name}'?"):
            self._run_thread(f'sc delete "{name}"', f"Удаление службы: {name}")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — БЛОКИРОВКИ
    # ════════════════════════════════════════════════════════════════════════
    def _show_disallowrun(self):
        self._reg_show(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun")

    def _clear_disallowrun(self):
        if messagebox.askyesno("Подтверждение", "Удалить все ключи DisallowRun?"):
            self._run(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun" /f')
            self.log("[+] DisallowRun очищен", "ok")

    def _show_debuggers(self):
        self._run_thread(
            r'reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options" /s',
            "Просмотр IFEO Debuggers")

    def _clear_debuggers(self):
        if messagebox.askyesno("Подтверждение",
                               "Удалить все записи Debugger из Image File Execution Options?\n"
                               "Это может затронуть легитимные отладчики."):
            out = self._run(
                r'reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options" /s')
            self.log("[!] Ручная очистка: откройте regedit и удалите ключи Debugger вручную", "warn")

    def _show_scancodemap(self):
        self._reg_show(r"HKLM\SYSTEM\CurrentControlSet\Control\Keyboard Layout")

    def _clear_scancodemap(self):
        if messagebox.askyesno("Подтверждение",
                               "Удалить ScancodeMap (сброс переназначений клавиш)?\n"
                               "Требуется перезагрузка."):
            self._run(r'reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Keyboard Layout" /v "Scancode Map" /f')
            self.log("[+] ScancodeMap удалён. Перезагрузите компьютер.", "ok")

    def _view_hosts(self):
        hosts = r"C:\Windows\System32\drivers\etc\hosts"
        self.log(f"// Содержимое {hosts}:", "info")
        try:
            with open(hosts, encoding="utf-8", errors="replace") as f:
                for line in f:
                    self.log(f"  {line.rstrip()}", "ok")
        except Exception as e:
            self.log(f"[!] {e}", "err")

    def _open_hosts_notepad(self):
        self._run('notepad C:\\Windows\\System32\\drivers\\etc\\hosts')

    def _restore_hosts(self):
        if messagebox.askyesno("Подтверждение",
                               "Восстановить стандартный hosts файл Windows?\n"
                               "Все изменения будут потеряны!"):
            default = "# Copyright (c) 1993-2009 Microsoft Corp.\r\n#\r\n" \
                      "# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.\r\n#\r\n" \
                      "# 127.0.0.1       localhost\r\n" \
                      "# ::1             localhost\r\n"
            hosts = r"C:\Windows\System32\drivers\etc\hosts"
            try:
                with open(hosts, "w") as f:
                    f.write(default)
                self.log("[+] Hosts файл восстановлен", "ok")
            except Exception as e:
                self.log(f"[!] {e}", "err")

    def _show_policies(self):
        self._reg_show(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System")
        self._reg_show(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")

    def _enable_taskmgr(self):
        self._run(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableTaskMgr /f')
        self.log("[+] Диспетчер задач разблокирован", "ok")

    def _enable_regedit(self):
        self._run(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableRegistryTools /f')
        self.log("[+] Редактор реестра разблокирован", "ok")

    def _enable_cmd(self):
        self._run(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableCMD /f')
        self.log("[+] Командная строка разблокирована", "ok")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — ВОССТАНОВЛЕНИЕ
    # ════════════════════════════════════════════════════════════════════════
    def _sfc_scannow(self):
        self.log("→ Запуск sfc /scannow (может занять несколько минут)...", "info")
        self._run_visible("sfc /scannow")

    def _dism_restore(self):
        self.log("→ Запуск DISM /RestoreHealth...", "info")
        self._run_visible("DISM /Online /Cleanup-Image /RestoreHealth")

    def _chkdsk_schedule(self):
        if messagebox.askyesno("chkdsk", "Запланировать chkdsk C: при следующей загрузке?"):
            self._run("chkdsk C: /f /r /x")
            self.log("[+] chkdsk запланирован на следующую загрузку", "ok")

    def _restore_logonui(self):
        self.log("→ Восстановление LogonUI...", "info")
        self._run("sfc /scanfile=C:\\Windows\\System32\\LogonUI.exe")
        self.log("[+] Готово. Если не помогло — запустите sfc /scannow", "ok")

    def _restore_theme(self):
        if messagebox.askyesno("Тема", "Применить стандартную тему Windows?"):
            self._run(r'rundll32.exe themecpl.dll,OpenThemeAction C:\Windows\Resources\Themes\aero.theme')

    def _fix_fonts(self):
        if messagebox.askyesno("Шрифты", "Сбросить системный шрифт к стандартному (Segoe UI)?"):
            cmd = (
                r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes" '
                r'/v "MS Shell Dlg" /t REG_SZ /d "Microsoft Sans Serif" /f && '
                r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes" '
                r'/v "MS Shell Dlg 2" /t REG_SZ /d "Tahoma" /f'
            )
            self._run(cmd)
            self.log("[+] Шрифты сброшены. Перезагрузите компьютер.", "ok")

    def _restore_russian(self):
        self.log("→ Восстановление русской раскладки...", "info")
        self._run(
            r'reg add "HKCU\Keyboard Layout\Preload" /v 1 /t REG_SZ /d 00000419 /f')
        self.log("[+] Русский язык добавлен. Перезайдите в систему.", "ok")

    def _restart_explorer(self):
        self._run("taskkill /f /im explorer.exe && start explorer.exe")
        self.log("[+] Explorer перезапущен", "ok")

    def _restore_shell(self):
        self._run(
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" '
            r'/v Shell /t REG_SZ /d Explorer.exe /f')
        self.log("[+] Shell восстановлен (Explorer.exe). Перезагрузите компьютер.", "ok")

    def _alt_explorer(self):
        path = filedialog.askopenfilename(title="Выберите файл Explorer/проводника",
                                          filetypes=[("Executable", "*.exe")])
        if path:
            self._open_file(path)

    def _enter_winre(self):
        if messagebox.askyesno("WinRE",
                               "Перезагрузить компьютер в среду восстановления Windows (WinRE)?"):
            self._run("reagentc /boottore")
            self._run("shutdown /r /t 5 /f")

    def _save_winre_cfg(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")],
                                            title="Сохранить конфиг WinRE")
        if path:
            out = self._run("reagentc /info")
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            self.log(f"[+] Конфиг WinRE сохранён: {path}", "ok")

    def _restore_winre(self):
        self._run("reagentc /enable")
        self.log("[+] WinRE включён", "ok")

    def _reagent_info(self):
        self._run_thread("reagentc /info", "Информация о WinRE")

    def _logoff(self):
        if messagebox.askyesno("Выход", "Завершить текущий сеанс?"):
            self._run("logoff")

    def _open_cmd_admin(self):
        os.popen("start cmd")

    def _open_ps_admin(self):
        os.popen("start powershell")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — СИСТЕМА
    # ════════════════════════════════════════════════════════════════════════
    def _enable_uac(self):
        self._run(
            r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" '
            r'/v EnableLUA /t REG_DWORD /d 1 /f')
        self.log("[+] UAC включён. Перезагрузите компьютер.", "ok")

    def _disable_uac(self):
        if messagebox.askyesno("UAC",
                               "Отключить UAC? Это снизит безопасность системы.\n"
                               "Требуется перезагрузка."):
            self._run(
                r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" '
                r'/v EnableLUA /t REG_DWORD /d 0 /f')
            self.log("[+] UAC отключён. Перезагрузите компьютер.", "ok")

    def _show_uac_status(self):
        self._reg_show(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")

    def _disable_test_mode(self):
        if messagebox.askyesno("Тестовый режим", "Выключить тестовый режим загрузки?"):
            self._run("bcdedit /set testsigning off")
            self.log("[+] Тестовый режим отключён. Перезагрузите компьютер.", "ok")

    def _enable_driver_signing(self):
        self._run("bcdedit /set nointegritychecks off")
        self.log("[+] Проверка подписи драйверов включена.", "ok")

    def _show_boot_status(self):
        self._run_thread("bcdedit /enum all", "Информация о загрузчике")

    def _replace_sethc(self):
        if messagebox.askyesno("sethc → cmd",
                               "Заменить sethc.exe на cmd.exe?\n"
                               "После этого 5×Shift на экране блокировки откроет cmd!"):
            self._run("takeown /f C:\\Windows\\System32\\sethc.exe")
            self._run('icacls C:\\Windows\\System32\\sethc.exe /grant administrators:F')
            self._run("copy /y C:\\Windows\\System32\\cmd.exe C:\\Windows\\System32\\sethc.exe")
            self.log("[+] sethc заменён на cmd", "ok")

    def _replace_utilman(self):
        if messagebox.askyesno("utilman → cmd",
                               "Заменить utilman.exe на cmd.exe?\n"
                               "Win+U на экране блокировки откроет cmd!"):
            self._run("takeown /f C:\\Windows\\System32\\utilman.exe")
            self._run('icacls C:\\Windows\\System32\\utilman.exe /grant administrators:F')
            self._run("copy /y C:\\Windows\\System32\\cmd.exe C:\\Windows\\System32\\utilman.exe")
            self.log("[+] utilman заменён на cmd", "ok")

    def _restore_sethc(self):
        self._run("sfc /scanfile=C:\\Windows\\System32\\sethc.exe")
        self.log("[+] sethc восстановлен через SFC", "ok")

    def _restore_utilman(self):
        self._run("sfc /scanfile=C:\\Windows\\System32\\utilman.exe")
        self.log("[+] utilman восстановлен через SFC", "ok")

    def _take_ownership(self):
        path = filedialog.askopenfilename(title="Выберите файл для взятия прав")
        if path:
            self._run(f'takeown /f "{path}"')
            self.log(f"[+] Права на {path} получены", "ok")

    def _full_access(self):
        path = filedialog.askopenfilename(title="Выберите файл для полного доступа")
        if path:
            self._run(f'takeown /f "{path}"')
            self._run(f'icacls "{path}" /grant administrators:F')
            self.log(f"[+] Полный доступ к {path} выдан", "ok")

    def _add_to_path(self):
        exe = os.path.abspath(sys.executable)
        folder = os.path.dirname(exe)
        current = os.environ.get("PATH", "")
        if folder not in current:
            self._run(f'setx PATH "%PATH%;{folder}"')
            self.log(f"[+] Добавлено в PATH: {folder}", "ok")
        else:
            self.log("[i] Уже есть в PATH", "info")

    def _add_context_menu(self):
        exe = os.path.abspath(sys.argv[0])
        self._run(
            f'reg add "HKCR\\*\\shell\\SHelper" /ve /d "Открыть в SHelper" /f')
        self._run(
            f'reg add "HKCR\\*\\shell\\SHelper\\command" /ve /d "{exe} \\"%1\\"" /f')
        self.log("[+] SHelper добавлен в контекстное меню", "ok")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — ОЧИСТКА
    # ════════════════════════════════════════════════════════════════════════
    def _clean_folder(self, folder: str, label: str):
        folder = os.path.expandvars(folder)
        self.log(f"→ Очистка {folder}...", "info")
        count = 0
        for item in Path(folder).iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    count += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    count += 1
            except Exception:
                pass
        self.log(f"[+] {label}: удалено {count} объектов", "ok")

    def _clean_user_temp(self):
        self._clean_folder("%TEMP%", "Temp пользователя")

    def _clean_sys_temp(self):
        if messagebox.askyesno("Системный Temp",
                               "Очистить C:\\Windows\\Temp?\n(Требуются права администратора)"):
            self._clean_folder("C:\\Windows\\Temp", "Системный Temp")

    def _clean_prefetch(self):
        if messagebox.askyesno("Prefetch", "Очистить C:\\Windows\\Prefetch?"):
            self._clean_folder("C:\\Windows\\Prefetch", "Prefetch")

    def _clean_recent(self):
        self._clean_folder(
            r"%APPDATA%\Microsoft\Windows\Recent", "Recent (последние файлы)")

    def _clean_recycle(self):
        if messagebox.askyesno("Корзина", "Очистить корзину?"):
            self._run("rd /s /q C:\\$Recycle.Bin")
            self.log("[+] Корзина очищена", "ok")

    def _clean_chrome(self):
        p = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache")
        if os.path.exists(p):
            self._clean_folder(p, "Chrome Cache")
        else:
            self.log("[!] Chrome Cache не найден", "warn")

    def _clean_edge(self):
        p = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache")
        if os.path.exists(p):
            self._clean_folder(p, "Edge Cache")
        else:
            self.log("[!] Edge Cache не найден", "warn")

    def _clean_firefox(self):
        profile_root = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
        if os.path.exists(profile_root):
            for profile in os.listdir(profile_root):
                cache = os.path.join(profile_root, profile, "cache2")
                if os.path.exists(cache):
                    self._clean_folder(cache, f"Firefox Cache ({profile})")
        else:
            self.log("[!] Firefox профиль не найден", "warn")

    def _list_3rd_drivers(self):
        self._run_thread(
            "driverquery /fo LIST /si", "Сторонние драйверы (подписанные)")

    def _delete_driver(self):
        name = simpledialog.askstring("Удалить драйвер",
                                      "Введите имя .inf файла драйвера:")
        if name and messagebox.askyesno("Подтверждение", f"Удалить драйвер '{name}'?"):
            self._run(f'pnputil /delete-driver "{name}" /uninstall /force')

    def _show_temp_sizes(self):
        for folder in ["%TEMP%", "C:\\Windows\\Temp", "C:\\Windows\\Prefetch"]:
            expanded = os.path.expandvars(folder)
            try:
                size = sum(
                    f.stat().st_size
                    for f in Path(expanded).rglob("*")
                    if f.is_file()
                ) // (1024 * 1024)
                self.log(f"  {folder}: ~{size} МБ", "ok")
            except Exception:
                self.log(f"  {folder}: нет доступа", "warn")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — ДИСКИ
    # ════════════════════════════════════════════════════════════════════════
    def _list_disks(self):
        self._run_thread(
            'echo list disk | diskpart', "Список физических дисков")

    def _list_volumes(self):
        self._run_thread(
            'echo list volume | diskpart', "Список томов")

    def _disk_space(self):
        self._run_thread(
            "wmic logicaldisk get Caption,FreeSpace,Size,FileSystem",
            "Место на дисках")

    def _disk_smart(self):
        self._run_thread(
            "wmic diskdrive get Status,Model,MediaType",
            "SMART-статус дисков")

    def _mbr_backup(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".bin", title="Сохранить MBR",
            filetypes=[("Binary", "*.bin"), ("All", "*.*")])
        if path:
            self.log(f"→ Сохранение MBR в {path}...", "info")
            # Используем PowerShell для чтения MBR
            ps = (
                f'$disk = New-Object System.IO.FileStream("\\\\.\\PhysicalDrive0",[IO.FileMode]::Open,'
                f'[IO.FileAccess]::Read); $buf = New-Object byte[] 512; '
                f'$disk.Read($buf,0,512) | Out-Null; $disk.Close(); '
                f'[IO.File]::WriteAllBytes("{path}",$buf)'
            )
            self._run(f'powershell -Command "{ps}"')
            self.log(f"[+] MBR сохранён: {path}", "ok")

    def _mbr_restore(self):
        path = filedialog.askopenfilename(
            title="Выберите файл MBR", filetypes=[("Binary", "*.bin"), ("All", "*.*")])
        if path and messagebox.askyesno(
                "Восстановить MBR",
                f"Восстановить MBR из:\n{path}\n\n⚠ Это перезапишет MBR диска! Продолжить?"):
            ps = (
                f'$buf = [IO.File]::ReadAllBytes("{path}"); '
                f'$disk = New-Object System.IO.FileStream("\\\\.\\PhysicalDrive0",'
                f'[IO.FileMode]::Open,[IO.FileAccess]::Write); '
                f'$disk.Write($buf,0,$buf.Length); $disk.Close()'
            )
            self._run(f'powershell -Command "{ps}"')
            self.log("[+] MBR восстановлен", "ok")

    def _mbr_fix(self):
        if messagebox.askyesno("Исправить MBR",
                               "Запустить bootrec /fixmbr?\nЭто перезапишет MBR."):
            self._run("bootrec /fixmbr")
            self._run("bootrec /fixboot")
            self.log("[+] MBR исправлен", "ok")

    def _fix_bcd(self):
        if messagebox.askyesno("Исправить BCD", "Восстановить BCD (загрузчик Windows)?"):
            self._run("bootrec /rebuildbcd")
            self.log("[+] BCD перестроен", "ok")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — ПОЛЬЗОВАТЕЛИ
    # ════════════════════════════════════════════════════════════════════════
    def _list_users(self):
        self._run_thread("net user", "Список локальных пользователей")

    def _list_admins(self):
        self._run_thread('net localgroup "Administrators"', "Администраторы")

    def _create_user(self):
        name = simpledialog.askstring("Создать пользователя", "Имя пользователя:")
        if not name:
            return
        pwd = simpledialog.askstring("Создать пользователя",
                                     "Пароль (Enter — без пароля):", show="*") or ""
        self._run(f'net user "{name}" "{pwd}" /add')
        self.log(f"[+] Пользователь '{name}' создан", "ok")

    def _delete_user(self):
        name = simpledialog.askstring("Удалить пользователя", "Имя пользователя:")
        if name and messagebox.askyesno("Подтверждение", f"Удалить пользователя '{name}'?"):
            self._run(f'net user "{name}" /delete')
            self.log(f"[+] Пользователь '{name}' удалён", "ok")

    def _reset_password(self):
        name = simpledialog.askstring("Сброс пароля", "Имя пользователя:")
        if not name:
            return
        pwd = simpledialog.askstring("Сброс пароля", "Новый пароль:", show="*")
        if pwd is not None:
            self._run(f'net user "{name}" "{pwd}"')
            self.log(f"[+] Пароль для '{name}' изменён", "ok")

    def _add_to_admins(self):
        name = simpledialog.askstring("Добавить в Admins", "Имя пользователя:")
        if name:
            self._run(f'net localgroup "Administrators" "{name}" /add')
            self.log(f"[+] '{name}' добавлен в Administrators", "ok")

    def _remove_from_admins(self):
        name = simpledialog.askstring("Убрать из Admins", "Имя пользователя:")
        if name and messagebox.askyesno("Подтверждение",
                                        f"Убрать '{name}' из группы Administrators?"):
            self._run(f'net localgroup "Administrators" "{name}" /delete')
            self.log(f"[+] '{name}' убран из Administrators", "ok")

    # ════════════════════════════════════════════════════════════════════════
    #  ЛОГИКА — АССОЦИАЦИИ
    # ════════════════════════════════════════════════════════════════════════
    def _show_assoc(self):
        self._run_thread("assoc", "Текущие ассоциации файлов")

    def _open_hkcr(self):
        self._run('regedit /e "%TEMP%\\hkcr.reg" HKEY_CLASSES_ROOT')
        self.log("[i] regedit открывается на HKEY_CLASSES_ROOT", "info")
        self._run("regedit")

    def _export_hkcr(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".reg", title="Экспорт HKCR",
            filetypes=[("Registry", "*.reg")])
        if path:
            self._run(f'reg export "HKCR" "{path}" /y')
            self.log(f"[+] HKCR экспортирован: {path}", "ok")

    def _fix_exe(self):
        script = (
            r'reg add "HKCR\exefile\shell\open\command" /ve '
            r'/d "\"%1\" %*" /f && '
            r'reg add "HKCR\.exe" /ve /d "exefile" /f'
        )
        self._run(script)
        self.log("[+] Ассоциация .exe восстановлена", "ok")

    def _fix_bat(self):
        self._run(r'reg add "HKCR\.bat" /ve /d "batfile" /f')
        self.log("[+] Ассоциация .bat восстановлена", "ok")

    def _fix_txt(self):
        self._run(r'reg add "HKCR\.txt" /ve /d "txtfile" /f')
        self.log("[+] Ассоциация .txt восстановлена", "ok")

    def _fix_lnk(self):
        self._run(r'reg add "HKCR\.lnk" /ve /d "lnkfile" /f')
        self.log("[+] Ассоциация .lnk восстановлена", "ok")

    def _fix_reg(self):
        self._run(r'reg add "HKCR\.reg" /ve /d "regfile" /f')
        self.log("[+] Ассоциация .reg восстановлена", "ok")

    def _fix_html(self):
        self._run(r'reg add "HKCR\.html" /ve /d "htmlfile" /f')
        self.log("[+] Ассоциация .html восстановлена", "ok")

    def _fix_msi(self):
        self._run(r'reg add "HKCR\.msi" /ve /d "Msi.Package" /f')
        self.log("[+] Ассоциация .msi восстановлена", "ok")


# ════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    app  = SHelperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

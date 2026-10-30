"""Compact, accessible desktop UI for voluntary donation mining.

No unattended or background mining mode: every session requires visible consent.
"""
import argparse
import queue
import threading
import time

from . import engine
from .public_config import DONATION_ADDRESS

VERSION = "0.1.0-preview.1"
COLORS = {
    "background": "#F3F6FA", "card": "#FFFFFF", "ink": "#17243A",
    "muted": "#5E6D80", "subtle": "#8391A2", "border": "#DCE4EE",
    "primary": "#2458CF", "primary_active": "#1748B6",
    "primary_soft": "#E9F0FE", "ok": "#137A56", "ok_soft": "#E3F4EC",
    "warning": "#995B13", "warning_soft": "#FFF4DD",
    "danger": "#AE3944", "danger_soft": "#FCECEF",
}


def self_test():
    assert engine.valid_address(DONATION_ADDRESS)
    assert engine.threads_for("Low", 8) == 2
    assert engine.threads_for("Medium", 8) == 4
    assert engine.seconds_for("1 hour") == 3600
    assert engine.parse_hashrate("speed 10s/60s/15m 123.5 n/a n/a H/s") == 123.5
    print("CPU Tip Jar self-test PASS (no mining started)")


def main():
    parser = argparse.ArgumentParser(description="Visible, opt-in Monero donation miner")
    parser.add_argument("--self-test", action="store_true", help="Harmless test; no GUI or mining")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return

    import tkinter as tk
    from tkinter import messagebox, ttk

    engine.os_name()
    c = COLORS
    root = tk.Tk()
    root.title("CPU Tip Jar — voluntary CPU donations")
    root.configure(bg=c["background"])
    root.geometry("754x720")
    root.minsize(690, 680)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Support.TCombobox", font=("DejaVu Sans", 11),
                    fieldbackground=c["card"], background=c["card"],
                    foreground=c["ink"], arrowcolor=c["muted"],
                    padding=(9, 8), bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"])
    style.map("Support.TCombobox",
              fieldbackground=[("readonly", c["card"])],
              selectbackground=[("readonly", c["card"])],
              selectforeground=[("readonly", c["ink"])])

    session = engine.Session()
    events = queue.Queue()
    downloading = False
    closing = False

    # A single column keeps the interface simple on both operating systems.
    page = tk.Frame(root, bg=c["background"], padx=26, pady=15)
    page.pack(fill="both", expand=True)

    def label(parent, text, *, size=11, weight="normal", color="ink",
              bg=None, wrap=None):
        return tk.Label(parent, text=text, font=("DejaVu Sans", size, weight),
                        fg=c.get(color, color), bg=bg or parent.cget("bg"),
                        anchor="w", justify="left", wraplength=wrap)

    def card(parent, *, padx=17, pady=11):
        f = tk.Frame(parent, bg=c["card"], highlightbackground=c["border"],
                     highlightthickness=1, bd=0, padx=padx, pady=pady)
        return f

    def button(parent, text, action, *, kind="neutral", width=None):
        bg, fg, active = {
            "neutral": (c["primary_soft"], c["primary"], "#DBE7FD"),
            "primary": (c["primary"], "#FFFFFF", c["primary_active"]),
            "danger": (c["danger_soft"], c["danger"], "#F7D9DE"),
        }[kind]
        b = tk.Button(parent, text=text, command=action,
                      font=("DejaVu Sans", 10, "bold"), bg=bg, fg=fg,
                      activebackground=active, activeforeground=fg,
                      disabledforeground="#9AA6B5", relief="flat", bd=0,
                      cursor="hand2", padx=13, pady=11, takefocus=1,
                      highlightthickness=1, highlightbackground=c["border"])
        if width:
            b.config(width=width)
        return b

    # Header
    top = tk.Frame(page, bg=c["background"])
    top.pack(fill="x")
    label(top, "CPU Tip Jar", size=21, weight="bold").pack(side="left")
    label(top, f"v{VERSION}", size=9, weight="bold", color="warning",
          bg=c["warning_soft"]).pack(side="right", padx=7, pady=4)
    label(page, "A simple way to support independent open-source work with CPU time.",
          color="muted", size=10).pack(anchor="w", pady=(3, 10))

    # Donation destination: always visible and copyable.
    destination = card(page)
    destination.pack(fill="x", pady=(0, 9))
    dhead = tk.Frame(destination, bg=c["card"])
    dhead.pack(fill="x")
    label(dhead, "Donation destination", size=12, weight="bold").pack(side="left")
    def copy_address():
        root.clipboard_clear()
        root.clipboard_append(DONATION_ADDRESS)
        root.update_idletasks()
        copy_button.config(text="Copied!")
        root.after(2200, lambda: copy_button.config(text="Copy address") if copy_button.winfo_exists() else None)
    copy_button = button(dhead, "Copy address", copy_address)
    copy_button.config(pady=5, padx=10, font=("DejaVu Sans", 9))
    copy_button.pack(side="right")
    label(destination, "Pool rewards go to this public Monero address, not to the volunteer.",
          color="muted", size=9).pack(anchor="w", pady=(5, 9))
    wallet = tk.Text(destination, height=2, wrap="char", bg="#F7F9FC",
                     fg=c["ink"], font=("DejaVu Sans Mono", 9),
                     padx=9, pady=8, relief="flat", borderwidth=0,
                     highlightthickness=1, highlightbackground=c["border"])
    wallet.insert("1.0", DONATION_ADDRESS[:48] + "\n" + DONATION_ADDRESS[48:])
    wallet.configure(state="disabled", cursor="arrow", takefocus=0)
    wallet.pack(fill="x")
    label(destination, "MoneroOcean  •  Official XMRig v6.26.0  •  XMRig developer donation: 1%",
          color="muted", size=9).pack(anchor="w", pady=(8, 0))

    # The two choices are side-by-side and never buried in settings.
    choices = tk.Frame(page, bg=c["background"])
    choices.pack(fill="x", pady=(0, 9))
    left = card(choices, padx=16, pady=10)
    right = card(choices, padx=16, pady=10)
    left.pack(side="left", fill="both", expand=True, padx=(0, 6))
    right.pack(side="left", fill="both", expand=True, padx=(6, 0))
    label(left, "CPU contribution", size=12, weight="bold").pack(anchor="w")
    label(right, "Maximum duration", size=12, weight="bold").pack(anchor="w")

    cpu = tk.StringVar(value="Low")
    duration = tk.StringVar(value="1 hour")
    cpu_combo = ttk.Combobox(left, textvariable=cpu, values=("Low", "Medium", "High"),
                             state="readonly", style="Support.TCombobox", width=19)
    cpu_combo.pack(fill="x", pady=(9, 7))
    duration_combo = ttk.Combobox(right, textvariable=duration,
                                  values=("1 hour", "1 day", "10 days", "30 days"),
                                  state="readonly", style="Support.TCombobox", width=19)
    duration_combo.pack(fill="x", pady=(9, 7))
    cpu_detail = label(left, "", color="muted", size=9)
    cpu_detail.pack(anchor="w")
    label(right, "Stops at the limit; keep app open.", color="muted", size=9).pack(anchor="w")

    def update_cpu(*_):
        cpu_detail.configure(text=f"{engine.threads_for(cpu.get())} of {engine.os.cpu_count() or 1} logical threads • not an exact CPU %")
    cpu.trace_add("write", update_cpu)
    update_cpu()

    consent = tk.BooleanVar(value=False)
    consent_row = card(page, padx=13, pady=8)
    consent_row.pack(fill="x", pady=(0, 9))
    check = tk.Checkbutton(
        consent_row, variable=consent, bg=c["card"], activebackground=c["card"],
        fg=c["ink"], activeforeground=c["ink"], anchor="w",
        font=("DejaVu Sans", 10),
        text="I choose to donate my CPU time and electricity. I can stop at any time.",
        selectcolor=c["card"], takefocus=1, bd=0, relief="flat", highlightthickness=0)
    check.pack(anchor="w")

    # Actions: separate engine download and mining consent.
    actions = tk.Frame(page, bg=c["background"])
    actions.pack(fill="x", pady=(0, 9))

    status = tk.StringVar(value="Ready — not mining")
    speed = tk.StringVar(value="— H/s")
    remaining = tk.StringVar(value="—")
    details = tk.StringVar(value="Install the verified mining engine to get started.")
    state_color = [c["muted"]]

    def update_buttons():
        busy = downloading or session.running()
        download_btn.config(state="disabled" if busy else "normal")
        remove_btn.config(state="disabled" if busy else "normal")
        start_btn.config(state="disabled" if busy else "normal")
        stop_btn.config(state="normal" if session.running() else "disabled")
        cpu_combo.config(state="disabled" if session.running() else "readonly")
        duration_combo.config(state="disabled" if session.running() else "readonly")

    def show_state(message, state="idle"):
        status.set(message)
        state_color[0] = {"idle": c["muted"], "active": c["ok"],
                          "error": c["danger"]}[state]
        status_view.config(fg=state_color[0])

    def download():
        nonlocal downloading
        if session.running() or downloading:
            return
        if not messagebox.askyesno("Install verified mining engine?",
                                   "Download official XMRig 6.26.0 from GitHub and check its SHA-256 hash?\n\n"
                                   "This installs only the engine. It does not start mining or configure startup."):
            return
        downloading = True
        show_state("Downloading official XMRig…")
        details.set("Checking the download before installation. Mining is not running.")
        update_buttons()
        def worker():
            try:
                engine.install_verified(lambda msg: events.put(("install_status", msg)))
                events.put(("installed", ""))
            except Exception as exc:
                events.put(("install_error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def start():
        if downloading or session.running():
            return
        if not consent.get():
            messagebox.showwarning("Consent required", "Read and tick the donation consent box before starting.")
            return
        if not engine.miner_path().is_file():
            messagebox.showinfo("Download XMRig first", "Choose Download verified XMRig before starting a session.")
            return
        threads = engine.threads_for(cpu.get())
        if not messagebox.askyesno(
                "Start donation mining?",
                f"Start mining for up to {duration.get()} using {threads} logical CPU thread(s)?\n\n"
                "All pool rewards go to the public address shown above.\n"
                "The app must remain open. You can stop at any time."):
            return
        try:
            engine.verified_local_executable()
            session.start(cpu.get(), duration.get())
            show_state("Mining active", "active")
            speed.set("Warming up…")
            details.set("Connection active. Waiting for pool shares.")
            update_buttons()
        except Exception as exc:
            show_state("Unable to start", "error")
            messagebox.showerror("Cannot start mining", str(exc))

    def stop():
        if session.running():
            session.stop()
        if session.running():
            show_state("Stop failed — miner still running", "error")
            details.set("Check your process list and stop XMRig manually.")
        else:
            show_state("Stopped — not mining")
            details.set("The mining session has ended.")
            speed.set("— H/s")
            remaining.set("—")
        update_buttons()

    def remove():
        if downloading or session.running():
            return
        target = engine.miner_path()
        if not target.exists():
            show_state("XMRig not installed")
            return
        if messagebox.askyesno("Remove XMRig?",
                               "Remove this app's downloaded XMRig executable?\n"
                               "This does not remove the CPU Tip Jar application."):
            try:
                target.unlink()
                show_state("XMRig removed")
                details.set("You can download the verified mining engine again at any time.")
            except OSError as exc:
                messagebox.showerror("Could not remove XMRig", str(exc))
            update_buttons()

    download_btn = button(actions, "1. Download verified XMRig", download)
    download_btn.pack(side="left", padx=(0, 8))
    start_btn = button(actions, "2. Start mining", start, kind="primary")
    start_btn.pack(side="left", padx=(0, 8))
    stop_btn = button(actions, "STOP mining", stop, kind="danger")
    stop_btn.pack(side="left")
    remove_btn = button(actions, "Remove XMRig", remove)
    remove_btn.config(pady=6, padx=10, font=("DejaVu Sans", 9))
    remove_btn.pack(side="right")

    # Session summary: prominent status and speed, concise secondary details.
    monitor = card(page, pady=11)
    monitor.pack(fill="x")
    mhead = tk.Frame(monitor, bg=c["card"])
    mhead.pack(fill="x")
    label(mhead, "Session status", size=12, weight="bold").pack(side="left")
    status_view = label(mhead, "", size=10, weight="bold", color="muted")
    status_view.config(textvariable=status)
    status_view.pack(side="right")
    stats = tk.Frame(monitor, bg=c["card"])
    stats.pack(fill="x", pady=(12, 6))
    stats_left = tk.Frame(stats, bg=c["card"])
    stats_right = tk.Frame(stats, bg=c["card"])
    stats_left.pack(side="left", fill="x", expand=True)
    stats_right.pack(side="left", fill="x", expand=True)
    label(stats_left, "HASH RATE", size=9, weight="bold", color="muted").pack(anchor="w")
    label(stats_right, "TIME REMAINING", size=9, weight="bold", color="muted").pack(anchor="w")
    speed_label = label(stats_left, "", size=18, weight="bold")
    speed_label.config(textvariable=speed)
    speed_label.pack(anchor="w", pady=(3, 1))
    time_label = label(stats_right, "", size=18, weight="bold")
    time_label.config(textvariable=remaining)
    time_label.pack(anchor="w", pady=(3, 1))
    detail_label = label(monitor, "", size=9, color="muted", wrap=650)
    detail_label.config(textvariable=details)
    detail_label.pack(anchor="w", pady=(5, 0))

    footer = label(page,
                   "Mining uses electricity and can produce heat. No auto-start or background service. "
                   "Preview: if the app crashes unexpectedly, check that XMRig stopped.",
                   color="muted", size=9, wrap=685)
    footer.pack(anchor="w", pady=(8, 0))

    def refresh():
        nonlocal downloading
        if closing:
            return
        while True:
            try:
                event, value = events.get_nowait()
            except queue.Empty:
                break
            if event == "install_status":
                show_state(value)
            elif event == "installed":
                downloading = False
                show_state("Engine verified — ready")
                details.set("XMRig is installed. Choose your settings and start when ready.")
                update_buttons()
            elif event == "install_error":
                downloading = False
                show_state("Verified download failed", "error")
                details.set("Mining has not started.")
                update_buttons()
                messagebox.showerror("Download failed", value)
        while True:
            try:
                kind, value = session.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "rate" and session.running():
                speed.set(f"{value:.1f} H/s")
            elif kind == "shares" and session.running():
                details.set(value)
            elif kind == "exit" and not session.running():
                show_state(f"Not mining — process ended ({value})")
                speed.set("— H/s")
                remaining.set("—")
                update_buttons()
        if session.tick():
            show_state("Duration complete — not mining")
            speed.set("— H/s")
            remaining.set("—")
            details.set("The selected donation period has finished.")
            update_buttons()
        if session.running():
            seconds = max(0, int(session.deadline - time.monotonic()))
            remaining.set(f"{seconds // 3600}h {(seconds % 3600) // 60}m")
        root.after(400, refresh)

    def close():
        nonlocal closing
        # Never intentionally leave a miner running when this window closes.
        if session.running():
            session.stop()
            if session.running():
                messagebox.showerror("Miner still running",
                                     "Unable to stop XMRig. Check the process list and stop it manually.")
                return
        closing = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    update_buttons()
    refresh()
    root.mainloop()

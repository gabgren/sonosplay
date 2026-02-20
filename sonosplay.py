#!/usr/bin/env python3
"""SonosPlay – play local MP3 files on Sonos speakers."""

import http.server
import os
import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote

import soco


# ── Local HTTP server (serves the MP3 so Sonos can stream it) ────────────

class _SingleFileHandler(http.server.SimpleHTTPRequestHandler):
    """Serves exactly one file, mapped to /file.mp3."""

    file_path: str = ""

    def translate_path(self, path):
        return self.file_path

    def log_message(self, fmt, *args):
        pass  # silence console noise


def _get_local_ip() -> str:
    """Return this machine's LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class FileServer:
    """Tiny HTTP server that exposes a single MP3 file."""

    def __init__(self):
        self._httpd: http.server.HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def serve(self, file_path: str) -> str:
        """Start (or restart) serving *file_path*. Returns the URL."""
        self.stop()
        _SingleFileHandler.file_path = file_path

        self._httpd = http.server.HTTPServer(("", 0), _SingleFileHandler)
        port = self._httpd.server_address[1]

        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

        ip = _get_local_ip()
        filename = quote(os.path.basename(file_path))
        return f"http://{ip}:{port}/{filename}"

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None
            self._thread = None


# ── GUI ──────────────────────────────────────────────────────────────────

class SonosPlayApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SonosPlay")
        self.root.geometry("520x400")
        self.root.resizable(False, False)

        self.file_server = FileServer()
        self.speakers: dict[str, soco.SoCo] = {}
        self.selected_file: str = ""
        self.active_speaker: soco.SoCo | None = None

        self._build_ui()

    # ── UI layout ────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}

        # — File selection —
        file_frame = ttk.LabelFrame(self.root, text="MP3 File")
        file_frame.pack(fill="x", **pad)

        self.file_label = ttk.Label(file_frame, text="No file selected", anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=6)

        ttk.Button(file_frame, text="Browse…", command=self._browse_file).pack(
            side="right", padx=8, pady=6
        )

        # — Speaker list —
        speaker_frame = ttk.LabelFrame(self.root, text="Sonos Speakers")
        speaker_frame.pack(fill="both", expand=True, **pad)

        self.speaker_list = tk.Listbox(speaker_frame, selectmode="browse")
        self.speaker_list.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)

        scrollbar = ttk.Scrollbar(
            speaker_frame, orient="vertical", command=self.speaker_list.yview
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=6)
        self.speaker_list.config(yscrollcommand=scrollbar.set)

        ttk.Button(self.root, text="Refresh Speakers", command=self._refresh_speakers).pack(
            **pad
        )

        # — Transport controls —
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill="x", **pad)

        self.play_btn = ttk.Button(ctrl_frame, text="▶  Play", command=self._play)
        self.play_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.stop_btn = ttk.Button(ctrl_frame, text="■  Stop", command=self._stop)
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # — Status bar —
        self.status = ttk.Label(self.root, text="Ready", relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom", ipady=2)

        # kick off initial discovery
        self._refresh_speakers()

    # ── Actions ──────────────────────────────────────────────────────

    def _set_status(self, text: str):
        self.status.config(text=text)
        self.root.update_idletasks()

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select MP3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
        )
        if path:
            self.selected_file = path
            self.file_label.config(text=os.path.basename(path))

    def _refresh_speakers(self):
        self._set_status("Discovering Sonos speakers…")
        self.speaker_list.delete(0, "end")
        self.speakers.clear()

        def discover():
            found = soco.discover(timeout=5) or set()
            self.root.after(0, lambda: self._populate_speakers(found))

        threading.Thread(target=discover, daemon=True).start()

    def _populate_speakers(self, found: set):
        for sp in sorted(found, key=lambda s: s.player_name):
            name = sp.player_name
            self.speakers[name] = sp
            self.speaker_list.insert("end", name)
        count = len(self.speakers)
        self._set_status(f"Found {count} speaker{'s' if count != 1 else ''}")

    def _get_selected_speaker(self) -> soco.SoCo | None:
        sel = self.speaker_list.curselection()
        if not sel:
            messagebox.showwarning("No speaker", "Select a Sonos speaker first.")
            return None
        name = self.speaker_list.get(sel[0])
        return self.speakers[name]

    def _play(self):
        if not self.selected_file:
            messagebox.showwarning("No file", "Select an MP3 file first.")
            return

        speaker = self._get_selected_speaker()
        if not speaker:
            return

        self._set_status("Starting playback…")

        def do_play():
            try:
                url = self.file_server.serve(self.selected_file)
                speaker.play_uri(url, title=os.path.basename(self.selected_file))
                self.active_speaker = speaker
                self.root.after(
                    0,
                    lambda: self._set_status(
                        f"Playing on {speaker.player_name}"
                    ),
                )
            except Exception as e:
                self.root.after(
                    0,
                    lambda: (
                        self._set_status("Playback failed"),
                        messagebox.showerror("Error", str(e)),
                    ),
                )

        threading.Thread(target=do_play, daemon=True).start()

    def _stop(self):
        if self.active_speaker:
            try:
                self.active_speaker.stop()
                self._set_status("Stopped")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            self._set_status("Nothing playing")
        self.file_server.stop()
        self.active_speaker = None


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    SonosPlayApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

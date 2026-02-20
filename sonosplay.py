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
        self.root.geometry("520x450")
        self.root.resizable(False, False)

        self.file_server = FileServer()
        # Maps display label -> (coordinator, [all members])
        self.groups: dict[str, tuple[soco.SoCo, list[soco.SoCo]]] = {}
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
        speaker_frame = ttk.LabelFrame(self.root, text="Sonos Speakers / Groups")
        speaker_frame.pack(fill="both", expand=True, **pad)

        self.speaker_list = tk.Listbox(speaker_frame, selectmode="browse")
        self.speaker_list.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)

        scrollbar = ttk.Scrollbar(
            speaker_frame, orient="vertical", command=self.speaker_list.yview
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=6)
        self.speaker_list.config(yscrollcommand=scrollbar.set)
        self.speaker_list.bind("<<ListboxSelect>>", self._on_speaker_select)

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

        # — Volume —
        vol_frame = ttk.LabelFrame(self.root, text="Volume")
        vol_frame.pack(fill="x", **pad)

        self.volume_var = tk.IntVar(value=0)
        self.volume_slider = ttk.Scale(
            vol_frame, from_=0, to=100, orient="horizontal",
            variable=self.volume_var, command=self._on_volume_change,
        )
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)

        self.volume_label = ttk.Label(vol_frame, text="0", width=4, anchor="center")
        self.volume_label.pack(side="right", padx=(0, 8), pady=6)

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
        self.groups.clear()

        def discover():
            found = soco.discover(timeout=5) or set()
            # Collect unique groups by coordinator
            seen: set[str] = set()
            groups: list[tuple[str, soco.SoCo, list[soco.SoCo]]] = []
            for sp in found:
                group = sp.group
                coord = group.coordinator
                if coord.uid in seen:
                    continue
                seen.add(coord.uid)
                members = sorted(group.members, key=lambda s: s.player_name)
                label = " + ".join(m.player_name for m in members)
                groups.append((label, coord, members))
            groups.sort(key=lambda g: g[0])
            self.root.after(0, lambda: self._populate_groups(groups))

        threading.Thread(target=discover, daemon=True).start()

    def _populate_groups(self, groups: list[tuple[str, soco.SoCo, list[soco.SoCo]]]):
        for label, coord, members in groups:
            self.groups[label] = (coord, members)
            self.speaker_list.insert("end", label)
        count = len(self.groups)
        self._set_status(f"Found {count} group{'s' if count != 1 else ''}")

    def _get_selected_group(self) -> tuple[soco.SoCo, list[soco.SoCo]] | None:
        sel = self.speaker_list.curselection()
        if not sel:
            messagebox.showwarning("No speaker", "Select a Sonos speaker/group first.")
            return None
        label = self.speaker_list.get(sel[0])
        return self.groups[label]

    def _on_speaker_select(self, _event=None):
        sel = self.speaker_list.curselection()
        if not sel:
            return
        label = self.speaker_list.get(sel[0])
        group = self.groups.get(label)
        if not group:
            return
        _coord, members = group

        def fetch_vol():
            try:
                avg = sum(m.volume for m in members) // len(members)
                self.root.after(0, lambda: self._set_volume_display(avg))
            except Exception:
                pass

        threading.Thread(target=fetch_vol, daemon=True).start()

    def _set_volume_display(self, vol: int):
        self.volume_var.set(vol)
        self.volume_label.config(text=str(vol))

    def _on_volume_change(self, value):
        vol = int(float(value))
        self.volume_label.config(text=str(vol))

        sel = self.speaker_list.curselection()
        if not sel:
            return
        label = self.speaker_list.get(sel[0])
        group = self.groups.get(label)
        if not group:
            return
        _coord, members = group

        def set_vol():
            for m in members:
                try:
                    m.volume = vol
                except Exception:
                    pass

        threading.Thread(target=set_vol, daemon=True).start()

    def _play(self):
        if not self.selected_file:
            messagebox.showwarning("No file", "Select an MP3 file first.")
            return

        group = self._get_selected_group()
        if not group:
            return

        coordinator, _members = group
        self._set_status("Starting playback…")

        def do_play():
            try:
                url = self.file_server.serve(self.selected_file)
                coordinator.play_uri(url, title=os.path.basename(self.selected_file))
                self.active_speaker = coordinator
                self.root.after(
                    0,
                    lambda: self._set_status(
                        f"Playing on {coordinator.player_name}"
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

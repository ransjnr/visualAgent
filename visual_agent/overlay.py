from __future__ import annotations

import queue
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class OverlayMessage:
    title: str
    body: str


class Overlay:
    """
    Very small always-on-top overlay using tkinter.
    Runs UI in a dedicated thread; safe cross-thread updates via a queue.
    """

    def __init__(self) -> None:
        self._q: "queue.Queue[OverlayMessage]" = queue.Queue()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def post(self, msg: OverlayMessage) -> None:
        self._q.put(msg)

    def _run(self) -> None:
        try:
            import tkinter as tk
        except Exception:
            # If tkinter isn't installed, silently do nothing.
            return

        root = tk.Tk()
        root.title("Visual Agent")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        # Small, unobtrusive window (top-right-ish).
        root.geometry("420x220+1200+40")

        title_var = tk.StringVar(value="Visual Agent")
        body_var = tk.StringVar(value="Watching screen…")

        title_lbl = tk.Label(root, textvariable=title_var, font=("Arial", 12, "bold"), anchor="w", justify="left")
        title_lbl.pack(fill="x", padx=10, pady=(10, 4))

        body_lbl = tk.Label(root, textvariable=body_var, font=("Arial", 10), anchor="nw", justify="left", wraplength=400)
        body_lbl.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def pump() -> None:
            updated = False
            last: OverlayMessage | None = None
            try:
                while True:
                    last = self._q.get_nowait()
                    updated = True
            except queue.Empty:
                pass
            if updated and last:
                title_var.set(last.title)
                body_var.set(last.body)
            root.after(150, pump)

        pump()
        root.mainloop()


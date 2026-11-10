from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from .help import TOPICS, help_for_label


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.pending = None
        self.window = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")
        widget.bind("<Destroy>", self.hide, add="+")

    def schedule(self, event=None):
        self.hide()
        self.pending = self.widget.after(450, self.show)

    def show(self):
        self.pending = None
        if not self.widget.winfo_exists():
            return
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        label = tk.Label(
            self.window,
            text=self.text,
            justify="left",
            wraplength=470,
            padx=10,
            pady=7,
            background="#fff8d9",
            foreground="#142e47",
            borderwidth=1,
            relief="solid",
        )
        label.pack()
        self.window.update_idletasks()
        x = min(
            self.widget.winfo_rootx() + 12,
            self.widget.winfo_screenwidth() - self.window.winfo_width() - 8,
        )
        y = min(
            self.widget.winfo_rooty() + self.widget.winfo_height() + 5,
            self.widget.winfo_screenheight() - self.window.winfo_height() - 8,
        )
        self.window.geometry(f"+{max(0,x)}+{max(0,y)}")

    def hide(self, event=None):
        if self.pending:
            try:
                self.widget.after_cancel(self.pending)
            except tk.TclError:
                pass
            self.pending = None
        if self.window:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None


def install_tooltips(parent, english=False):
    for widget in parent.winfo_children():
        if isinstance(widget, (ttk.Button, ttk.Checkbutton)) and not hasattr(
            widget, "_help_tooltip"
        ):
            widget._help_tooltip = Tooltip(widget, help_for_label(widget.cget("text"), english))
        install_tooltips(widget, english)


class Manual(ttk.Frame):
    def __init__(self, parent, english=False):
        super().__init__(parent)
        self.english = english
        self.filtered = []
        ttk.Label(self, text="Search help / 도움말 검색" if not english else "Search help").pack(
            anchor="w"
        )
        self.query = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.query)
        entry.pack(fill="x", pady=5)
        self.topics = ttk.Combobox(self, state="readonly")
        self.topics.pack(fill="x")
        self.topics.bind("<<ComboboxSelected>>", lambda e: self.show())
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True, pady=6)
        self.text = tk.Text(area, wrap="word", width=45, font="TkDefaultFont")
        scroll = ttk.Scrollbar(area, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        self.query.trace_add("write", lambda *a: self.filter())
        self.filter()

    def filter(self):
        q = self.query.get().casefold()
        self.filtered = [
            t
            for t in TOPICS
            if q
            in " ".join(
                [t["title_ko"], t["title_en"], t["body_ko"], t["body_en"], *t["buttons"]]
            ).casefold()
        ]
        self.topics["values"] = [
            t["title_en" if self.english else "title_ko"] for t in self.filtered
        ]
        if self.filtered:
            self.topics.current(0)
        else:
            self.topics.set("")
        self.show()

    def show(self):
        i = self.topics.current()
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        if 0 <= i < len(self.filtered):
            t = self.filtered[i]
            lang = "en" if self.english else "ko"
            aliases = ", ".join(b for b in t["buttons"] if not self.english or b.isascii())
            self.text.insert(
                "1.0",
                t["title_" + lang]
                + "\n\n"
                + t["summary_" + lang]
                + "\n\n"
                + t["body_" + lang]
                + "\n\nButtons: "
                + aliases,
            )
        self.text.configure(state="disabled")

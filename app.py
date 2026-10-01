import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

from model import Instrument, Duration, Partiture
from editor import DrumEditor, DURATIONS_ORDERED
from export import export_pdf


INSTRUMENT_LABELS = {
    Instrument.CRASH_CYMBAL: "Crash",
    Instrument.HI_HAT: "Charleston",
    Instrument.RIDE_CYMBAL: "Ride",
    Instrument.HIGH_TOM: "Tom Haut",
    Instrument.SNARE: "Caisse Claire",
    Instrument.MID_TOM: "Tom Médium",
    Instrument.FLOOR_TOM: "Tom Basse",
    Instrument.BASS_DRUM: "Grosse Caisse",
}

INSTRUMENT_ORDER_DISPLAY = [
    Instrument.CRASH_CYMBAL,
    Instrument.HI_HAT,
    Instrument.RIDE_CYMBAL,
    Instrument.HIGH_TOM,
    Instrument.SNARE,
    Instrument.MID_TOM,
    Instrument.FLOOR_TOM,
    Instrument.BASS_DRUM,
]

DARK_BG = "#1e1e1e"
DARK_BG2 = "#2d2d2d"
DARK_FG = "#e0e0e0"
DARK_SEL = "#4a90d9"
DARK_BTN = "#3c3c3c"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Drumpart - \u00c9diteur de partitions Batterie")
        self.geometry("1200x700")
        self.minsize(900, 500)

        self.current_file: str | None = None
        self.partiture = Partiture()

        self._apply_theme()
        self._build_menu()
        self._build_statusbar()

        self.editor = DrumEditor(self, partiture=self.partiture)
        self.editor.pack(fill=tk.BOTH, expand=True)

        self._build_toolbar()

        self.protocol("WM_DELETE_WINDOW", self._on_quit)

    def _apply_theme(self):
        self.configure(bg=DARK_BG)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=DARK_BG2, foreground=DARK_FG, fieldbackground=DARK_BG)
        style.configure("TFrame", background=DARK_BG2)
        style.configure("TLabelframe", background=DARK_BG2, foreground=DARK_FG)
        style.configure("TLabel", background=DARK_BG2, foreground=DARK_FG)
        style.configure("TButton", background=DARK_BTN, foreground=DARK_FG, bordercolor="#555", lightcolor="#555", darkcolor="#222")
        style.map("TButton", background=[("active", "#555")])
        style.configure("TSeparator", background="#555")
        style.configure("Sunk.TLabel", background=DARK_BG, foreground=DARK_FG, relief=tk.SUNKEN)

    def _build_menu(self):
        mb = tk.Menu(self, bg=DARK_BG2, fg=DARK_FG, activebackground=DARK_SEL, activeforeground="#fff")
        self.configure(menu=mb)

        fm = tk.Menu(mb, tearoff=0, bg=DARK_BG2, fg=DARK_FG, activebackground=DARK_SEL, activeforeground="#fff")
        fm.add_command(label="Nouveau", command=self._new, accelerator="Ctrl+N")
        fm.add_command(label="Ouvrir...", command=self._open, accelerator="Ctrl+O")
        fm.add_command(label="Enregistrer", command=self._save, accelerator="Ctrl+S")
        fm.add_command(label="Enregistrer sous...", command=self._save_as)
        fm.add_separator()
        fm.add_command(label="Exporter PDF...", command=self._export_pdf, accelerator="Ctrl+P")
        fm.add_separator()
        fm.add_command(label="Quitter", command=self._on_quit)
        mb.add_cascade(label="Fichier", menu=fm)

        em = tk.Menu(mb, tearoff=0, bg=DARK_BG2, fg=DARK_FG, activebackground=DARK_SEL, activeforeground="#fff")
        em.add_command(label="Ajouter une mesure", command=self._add_measure, accelerator="Ctrl+M")
        em.add_command(label="Supprimer derni\u00e8re mesure", command=self._remove_measure)
        mb.add_cascade(label="\u00c9dition", menu=em)

        hm = tk.Menu(mb, tearoff=0, bg=DARK_BG2, fg=DARK_FG, activebackground=DARK_SEL, activeforeground="#fff")
        hm.add_command(label="\u00c0 propos", command=self._show_about)
        mb.add_cascade(label="Aide", menu=hm)

        self.bind_all("<Control-n>", lambda e: self._new())
        self.bind_all("<Control-o>", lambda e: self._open())
        self.bind_all("<Control-s>", lambda e: self._save())
        self.bind_all("<Control-p>", lambda e: self._export_pdf())
        self.bind_all("<Control-m>", lambda e: self._add_measure())

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=DARK_BG2, bd=0, highlightthickness=0)
        tb.pack(fill=tk.X, before=self.editor)

        lbl_instr = tk.Label(tb, text="Instrument:", font=("Helvetica", 9, "bold"),
                             bg=DARK_BG2, fg=DARK_FG)
        lbl_instr.pack(side=tk.LEFT, padx=(8, 4))

        self._instr_var = tk.StringVar(self)
        instr_names = [INSTRUMENT_LABELS[i] for i in INSTRUMENT_ORDER_DISPLAY]
        self._instr_var.set(instr_names[0])
        self._instr_dropdown = tk.OptionMenu(tb, self._instr_var, *instr_names,
                                              command=self._on_instr_dropdown)
        self._instr_dropdown.configure(bg=DARK_BTN, fg=DARK_FG, activebackground="#555",
                                        font=("Helvetica", 9, "bold"), bd=1, relief=tk.RAISED,
                                        highlightthickness=0)
        menu = self._instr_dropdown["menu"]
        menu.configure(bg=DARK_BG2, fg=DARK_FG, activebackground=DARK_SEL, activeforeground="#fff",
                       font=("Helvetica", 9))
        self._instr_dropdown.pack(side=tk.LEFT, padx=(0, 12))

        self._instr_label_map = dict(zip(instr_names, INSTRUMENT_ORDER_DISPLAY))

        lbl_dur = tk.Label(tb, text="Dur\u00e9es:", font=("Helvetica", 9, "bold"),
                           bg=DARK_BG2, fg=DARK_FG)
        lbl_dur.pack(side=tk.LEFT, padx=(6, 4))

        self._dur_buttons = {}
        dur_frame = tk.Frame(tb, bg=DARK_BG2)
        dur_frame.pack(side=tk.LEFT)
        for dur in DURATIONS_ORDERED:
            btn = tk.Button(
                dur_frame, text=dur.label(), width=8,
                font=("Helvetica", 9, "bold"),
                relief=tk.RAISED, bd=1,
                bg=DARK_BTN, fg=DARK_FG, activebackground="#555",
                command=lambda d=dur: self._select_duration(d),
            )
            btn.pack(side=tk.LEFT, padx=1)
            self._dur_buttons[dur] = btn

        sep = tk.Frame(tb, width=2, bg="#555")
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=12)

        tk.Button(tb, text="+ Mesure", command=self._add_measure, width=9,
                  bg=DARK_BTN, fg=DARK_FG, activebackground="#555", bd=1, relief=tk.RAISED,
                  font=("Helvetica", 9)).pack(side=tk.LEFT, padx=1)
        tk.Button(tb, text="- Mesure", command=self._remove_measure, width=9,
                  bg=DARK_BTN, fg=DARK_FG, activebackground="#555", bd=1, relief=tk.RAISED,
                  font=("Helvetica", 9)).pack(side=tk.LEFT, padx=1)

        sep2 = tk.Frame(tb, width=2, bg="#555")
        sep2.pack(side=tk.LEFT, fill=tk.Y, padx=12)

        lbl_ts = tk.Label(tb, text="Mesure:", font=("Helvetica", 9, "bold"),
                          bg=DARK_BG2, fg=DARK_FG)
        lbl_ts.pack(side=tk.LEFT, padx=(0, 4))

        self._ts_buttons = {}
        for ts_val, ts_label in [(4, "4/4"), (3, "3/4")]:
            btn = tk.Button(
                tb, text=ts_label, width=4,
                font=("Helvetica", 9, "bold"),
                relief=tk.RAISED, bd=1,
                bg=DARK_BTN, fg=DARK_FG, activebackground="#555",
                command=lambda v=ts_val: self._select_time_sig(v),
            )
            btn.pack(side=tk.LEFT, padx=1)
            self._ts_buttons[ts_val] = btn

        self._select_time_sig(4)

        self._select_instrument(Instrument.SNARE)
        self._select_duration(Duration.QUARTER)

    def _build_statusbar(self):
        self.status = tk.Label(
            self, text="Pr\u00eat", anchor=tk.W,
            bg=DARK_BG, fg=DARK_FG, font=("Helvetica", 9),
        )
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def _on_instr_dropdown(self, selection: str):
        instr = self._instr_label_map[selection]
        self._select_instrument(instr)

    def _select_instrument(self, instr: Instrument):
        self.editor.set_instrument(instr)
        self._instr_var.set(INSTRUMENT_LABELS[instr])
        self.status.configure(text=f"Instrument: {instr.value}")

    def _select_duration(self, dur: Duration):
        self.editor.set_duration(dur)
        for d, btn in self._dur_buttons.items():
            selected = d == dur
            btn.configure(
                relief=tk.SUNKEN if selected else tk.RAISED,
                bg=DARK_SEL if selected else DARK_BTN,
                fg="#fff",
            )

    def _select_time_sig(self, beats: int):
        self.partiture.set_time_sig(beats, 4)
        self.editor.render()
        for ts, btn in self._ts_buttons.items():
            selected = ts == beats
            btn.configure(
                relief=tk.SUNKEN if selected else tk.RAISED,
                bg=DARK_SEL if selected else DARK_BTN,
                fg="#fff",
            )
        self._update_status(f"Mesure en {beats}/4")

    def _add_measure(self, event=None):
        self.partiture.add_measure()
        self.editor.render()
        self._update_status(f"Mesure {len(self.partiture.measures)} ajout\u00e9e")

    def _remove_measure(self):
        if self.partiture.remove_last_measure():
            self.editor.render()
            self._update_status("Derni\u00e8re mesure supprim\u00e9e")
        else:
            self._update_status("Impossible de supprimer : il reste 1 mesure")

    def _new(self):
        if messagebox.askyesno("Nouveau", "Voulez-vous cr\u00e9er une nouvelle partition ?"):
            self.partiture = Partiture()
            self.current_file = None
            self.editor.set_partiture(self.partiture)
            self.title("Drumpart - \u00c9diteur de partitions Batterie")
            self._update_status("Nouvelle partition cr\u00e9\u00e9e")

    def _open(self):
        path = filedialog.askopenfilename(
            filetypes=[("Fichiers Drumpart", "*.drum.json"), ("Tous", "*.*")],
            title="Ouvrir une partition",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.partiture = Partiture.from_json(text)
            self.current_file = path
            self.editor.set_partiture(self.partiture)
            self.title(f"Drumpart - {os.path.basename(path)}")
            self._update_status(f"Partition charg\u00e9e : {path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier :\n{e}")

    def _save(self):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self._save_as()

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".drum.json",
            filetypes=[("Fichiers Drumpart", "*.drum.json"), ("Tous", "*.*")],
            title="Enregistrer la partition",
        )
        if not path:
            return
        self.current_file = path
        self._write_file(path)

    def _write_file(self, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.partiture.to_json())
            self.title(f"Drumpart - {os.path.basename(path)}")
            self._update_status(f"Partition enregistr\u00e9e : {path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer :\n{e}")

    def _export_pdf(self, event=None):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Exporter en PDF",
        )
        if not path:
            return
        try:
            export_pdf(self.partiture, path)
            self._update_status(f"PDF export\u00e9 : {path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'export PDF :\n{e}")

    def _show_about(self):
        messagebox.showinfo(
            "\u00c0 propos",
            "Drumpart v1.0\n\n\u00c9diteur de partitions de batterie\nCr\u00e9\u00e9 avec Python & Tkinter",
        )

    def _on_quit(self):
        self.destroy()

    def _update_status(self, msg: str):
        self.status.configure(text=msg)

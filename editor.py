import tkinter as tk
import math
from model import Instrument, Duration, Note, Partiture, Measure

SPACING = 14
STAFF_TOP = 110
STAFF_LEFT = 80
MEASURE_WIDTH = 160
NOTEHEAD_W = 10
NOTEHEAD_H = 8
MARGIN = 8
SYSTEM_SPACING = 50

DARK_CANVAS = "#1e1e1e"
DARK_LINE = "#888888"
DARK_TEXT = "#cccccc"
DARK_NOTE = "#ffffff"
DARK_MUTED = "#666666"
DARK_BG2 = "#333333"
DARK_FG = "#cccccc"

INSTRUMENT_POSITIONS = {
    Instrument.CRASH_CYMBAL: -2.0,
    Instrument.HI_HAT: -1.0,
    Instrument.RIDE_CYMBAL: 0.0,
    Instrument.HIGH_TOM: 1.0,
    Instrument.SNARE: 2.0,
    Instrument.MID_TOM: 3.0,
    Instrument.FLOOR_TOM: 4.0,
    Instrument.BASS_DRUM: 5.0,
}

INSTRUMENTS_ORDERED = [
    Instrument.CRASH_CYMBAL,
    Instrument.HI_HAT,
    Instrument.RIDE_CYMBAL,
    Instrument.HIGH_TOM,
    Instrument.SNARE,
    Instrument.MID_TOM,
    Instrument.FLOOR_TOM,
    Instrument.BASS_DRUM,
]

DURATIONS_ORDERED = [Duration.QUARTER, Duration.EIGHTH, Duration.SIXTEENTH, Duration.TRIOLET]


def _rotated_notehead_pts(cx, cy, rx, ry, n=16):
    pts = []
    a = math.radians(-15)
    for i in range(n):
        t = 2 * math.pi * i / n
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        pts.append(cx + x * math.cos(a) - y * math.sin(a))
        pts.append(cy + x * math.sin(a) + y * math.cos(a))
    return pts


def instrument_y(instr: Instrument) -> float:
    return STAFF_TOP + INSTRUMENT_POSITIONS[instr] * SPACING


class DrumEditor(tk.Frame):
    def __init__(self, parent, partiture: Partiture | None = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.partiture = partiture or Partiture()
        self.selected_instrument = Instrument.SNARE
        self.selected_duration = Duration.QUARTER
        self._note_rects: dict[tuple[int, int], int] = {}
        self._title_entry: tk.Entry | None = None
        self._author_entry: tk.Entry | None = None
        self._tempo_entry: tk.Entry | None = None
        self._layout_systems: list[dict] = []

        self._setup_ui()
        self.render()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self, bg=DARK_CANVAS, highlightthickness=0)
        self.scrollbar_h = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview,
                                        bg="#333", troughcolor="#222", highlightbackground="#444")
        self.scrollbar_v = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview,
                                        bg="#333", troughcolor="#222", highlightbackground="#444")
        self.canvas.configure(xscrollcommand=self.scrollbar_h.set,
                              yscrollcommand=self.scrollbar_v.set)

        self.scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        self.render()

    def set_partiture(self, partiture: Partiture):
        self.partiture = partiture
        self.render()

    def render(self):
        self.canvas.delete("all")
        self._note_rects.clear()
        self._clean_entries()
        self._layout_systems.clear()

        cw = max(self.canvas.winfo_width(), 300)
        n = len(self.partiture.measures)

        header_h = STAFF_TOP
        system_h = 5 * SPACING + SYSTEM_SPACING
        line_w = cw - STAFF_LEFT - MARGIN

        meas_per_sys = max(1, int(line_w / MEASURE_WIDTH))
        n_systems = max(1, math.ceil(n / meas_per_sys))
        actual_meas_per_sys = max(1, math.ceil(n / n_systems))
        actual_mw = line_w / actual_meas_per_sys
        total_h = header_h + n_systems * system_h + 60

        self.canvas.configure(scrollregion=(0, 0, cw, total_h))

        self._draw_title()
        self._draw_author()
        self._draw_tempo()

        for sys_idx in range(n_systems):
            start = sys_idx * actual_meas_per_sys
            end = min(start + actual_meas_per_sys, n)
            staff_top = STAFF_TOP + sys_idx * system_h
            n_in_line = end - start

            self._layout_systems.append({
                "staff_top": staff_top,
                "start_idx": start,
                "end_idx": end,
                "actual_mw": actual_mw,
                "line_w": line_w,
            })

            self._draw_staff_lines(staff_top, line_w)
            self._draw_clef_at(staff_top)
            self._draw_measures_range(staff_top, line_w, start, end, actual_mw)

    def _draw_title(self):
        tid = self.canvas.create_text(
            STAFF_LEFT, 22, anchor=tk.W, text=self.partiture.title,
            font=("Helvetica", 16, "bold"), fill=DARK_TEXT,
        )
        self.canvas.tag_bind(tid, "<Button-1>", lambda e: self._edit_title())

    def _draw_author(self):
        aid = self.canvas.create_text(
            STAFF_LEFT + 2, 46, anchor=tk.W,
            text=f"Par : {self.partiture.author}",
            font=("Helvetica", 10), fill=DARK_MUTED,
        )
        self.canvas.tag_bind(aid, "<Button-1>", lambda e: self._edit_author())

    def _draw_tempo(self):
        nw, nh = 8, 6
        nx = STAFF_LEFT + 4
        ny = 71
        self.canvas.create_oval(
            nx - nw // 2, ny - nh // 2,
            nx + nw // 2, ny + nh // 2,
            fill=DARK_MUTED, outline=DARK_MUTED,
        )
        self.canvas.create_line(nx, ny - nh // 2, nx, ny - nh // 2 - 20, fill=DARK_MUTED, width=2)
        tid = self.canvas.create_text(
            nx + 14, 68, anchor=tk.W,
            text=f"{self.partiture.tempo} BPM",
            font=("Helvetica", 11), fill=DARK_MUTED,
        )
        self.canvas.tag_bind(tid, "<Button-1>", lambda e: self._edit_tempo())

    def _clean_entries(self):
        if self._title_entry:
            self._title_entry.destroy()
            self._title_entry = None
        if self._author_entry:
            self._author_entry.destroy()
            self._author_entry = None
        if self._tempo_entry:
            self._tempo_entry.destroy()
            self._tempo_entry = None

    def _edit_title(self):
        self._clean_entries()
        e = tk.Entry(self.canvas, bg=DARK_BG2, fg=DARK_FG, font=("Helvetica", 16, "bold"),
                     bd=1, relief=tk.SUNKEN, highlightbackground="#555")
        e.insert(0, self.partiture.title)
        e.select_range(0, tk.END)
        e.place(x=STAFF_LEFT, y=2, width=400, height=28)
        e.focus_set()

        def commit(event=None):
            val = e.get().strip()
            if val:
                self.partiture.title = val
            self._clean_entries()
            self.render()

        e.bind("<Return>", commit)
        e.bind("<FocusOut>", commit)
        self._title_entry = e

    def _edit_author(self):
        self._clean_entries()
        e = tk.Entry(self.canvas, bg=DARK_BG2, fg=DARK_FG, font=("Helvetica", 10),
                     bd=1, relief=tk.SUNKEN, highlightbackground="#555")
        e.insert(0, self.partiture.author)
        e.select_range(0, tk.END)
        e.place(x=STAFF_LEFT + 2, y=34, width=300, height=22)
        e.focus_set()

        def commit(event=None):
            val = e.get().strip()
            if val:
                self.partiture.author = val
            self._clean_entries()
            self.render()

        e.bind("<Return>", commit)
        e.bind("<FocusOut>", commit)
        self._author_entry = e

    def _edit_tempo(self):
        self._clean_entries()
        e = tk.Entry(self.canvas, bg=DARK_BG2, fg=DARK_FG, font=("Helvetica", 11),
                     bd=1, relief=tk.SUNKEN, highlightbackground="#555")
        e.insert(0, str(self.partiture.tempo))
        e.select_range(0, tk.END)
        e.place(x=STAFF_LEFT + 4, y=52, width=100, height=24)
        e.focus_set()

        def commit(event=None):
            raw = e.get().strip()
            try:
                val = int(raw)
                if 0 <= val <= 999:
                    self.partiture.tempo = val
            except ValueError:
                pass
            self._clean_entries()
            self.render()

        e.bind("<Return>", commit)
        e.bind("<FocusOut>", commit)
        self._tempo_entry = e

    def _draw_staff_lines(self, staff_top: float, line_w: float):
        for i in range(5):
            y = staff_top + i * SPACING
            self.canvas.create_line(
                STAFF_LEFT, y, STAFF_LEFT + line_w, y,
                fill=DARK_LINE, width=1,
            )

    def _draw_clef_at(self, staff_top: float):
        cx = STAFF_LEFT - 28
        mid_y = staff_top + 2 * SPACING
        bar_w = 4
        gap = 6
        top = staff_top - 6
        bot = staff_top + 4 * SPACING + 6
        self.canvas.create_rectangle(
            cx - bar_w, top, cx, bot,
            fill=DARK_LINE, outline="",
        )
        self.canvas.create_rectangle(
            cx + gap, top, cx + gap + bar_w, bot,
            fill=DARK_LINE, outline="",
        )

    def _draw_measures_range(self, staff_top: float, line_w: float,
                              start_idx: int, end_idx: int, mw: float):
        measures = self.partiture.measures
        for j in range(start_idx, end_idx):
            measure = measures[j]
            local_j = j - start_idx
            mx = STAFF_LEFT + local_j * mw
            self._draw_barline(mx, staff_top, is_start=(local_j == 0))
            self._draw_time_sig(mx, staff_top, measure, j)
            self._draw_measure_number(mx, staff_top, mw, j)
            beats = measure.beats()
            beam_info = self._get_beam_group(staff_top, mx, measure, beats, mw)
            if beam_info:
                for note in measure.notes:
                    self._draw_note(staff_top, mx, note, beats, mw, beam_info)
                self._draw_beam_lines(beam_info)
            else:
                for note in measure.notes:
                    self._draw_note(staff_top, mx, note, beats, mw)

        last_x = STAFF_LEFT + (end_idx - start_idx) * mw
        self._draw_barline(last_x, staff_top, double=True)

    def _get_beam_group(self, staff_top: float, mx: float, measure: Measure,
                        beats: int, mw: float) -> dict | None:
        if beats != 4:
            return None
        beats_with_notes = set(int(n.beat) for n in measure.notes)
        if 0 not in beats_with_notes or 2 not in beats_with_notes:
            return None
        group: dict = {}
        for note in measure.notes:
            b = int(note.beat)
            if b not in (0, 2):
                continue
            ny = staff_top + INSTRUMENT_POSITIONS[note.instrument] * SPACING
            stem_up = INSTRUMENT_POSITIONS[note.instrument] < 2.0
            stem_len = 28
            if stem_up:
                tip = (ny - NOTEHEAD_H // 2 - 1) - stem_len
            else:
                tip = (ny + NOTEHEAD_H // 2 + 1) + stem_len
            if b not in group:
                group[b] = {"tips": [tip], "up": stem_up}
            else:
                group[b]["tips"].append(tip)
                if group[b]["up"] != stem_up:
                    return None
        if group[0]["up"] != group[2]["up"]:
            return None
        all_tips = group[0]["tips"] + group[2]["tips"]
        common_tip = min(all_tips) if group[0]["up"] else max(all_tips)
        edges = {}
        for note in measure.notes:
            nb = int(note.beat)
            if nb not in (0, 2):
                continue
            ny = staff_top + INSTRUMENT_POSITIONS[note.instrument] * SPACING
            stem_up = INSTRUMENT_POSITIONS[note.instrument] < 2.0
            nx = mx + (mw * (note.beat + 0.5) / beats)
            stem_x = nx + (NOTEHEAD_W // 3 if stem_up else -NOTEHEAD_W // 3)
            if nb not in edges:
                edges[nb] = [stem_x, stem_x]
            else:
                edges[nb][0] = min(edges[nb][0], stem_x)
                edges[nb][1] = max(edges[nb][1], stem_x)
        return {
            "up": group[0]["up"],
            "common_tip": common_tip,
            "edges": edges,
            "beats": (0, 2),
        }

    def _draw_beam_lines(self, info: dict):
        up = info["up"]
        tip = info["common_tip"]
        edges = info["edges"]
        x1 = edges[0][0]
        x2 = edges[2][1]
        for i in range(2):
            dy = i * 6 * (1 if up else -1)
            self.canvas.create_line(
                x1 - 2, tip + dy, x2 + 2, tip + dy,
                fill=DARK_NOTE, width=2, capstyle=tk.ROUND,
            )

    def _draw_barline(self, x: float, staff_top: float, is_start: bool = False, double: bool = False):
        top = staff_top - 10
        bot = staff_top + 4 * SPACING + 10
        if double:
            self.canvas.create_line(x + 4, top, x + 4, bot, fill=DARK_LINE, width=2)
            self.canvas.create_line(x, top, x, bot, fill=DARK_LINE, width=1)
        else:
            width = 2 if is_start else 1
            self.canvas.create_line(x, top, x, bot, fill=DARK_LINE, width=width)

    def _draw_time_sig(self, mx: float, staff_top: float, measure: Measure, idx: int):
        if idx == 0:
            ts = measure.time_sig
            cx = mx + 20
            mid = staff_top + 1.5 * SPACING
            self.canvas.create_text(cx, mid - 6, text=str(ts[0]),
                                    font=("Helvetica", 11, "bold"), fill=DARK_TEXT)
            self.canvas.create_text(cx, mid + 12, text=str(ts[1]),
                                    font=("Helvetica", 11, "bold"), fill=DARK_TEXT)

    def _draw_measure_number(self, mx: float, staff_top: float, mw: float, idx: int):
        self.canvas.create_text(
            mx + mw // 2, staff_top - 22,
            text=str(idx + 1), font=("Helvetica", 8), fill=DARK_MUTED,
        )

    def _draw_note(self, staff_top: float, mx: float, note: Note, beats: int = 4,
                   mw: float = MEASURE_WIDTH, beam_info: dict | None = None):
        nx = mx + (mw * (note.beat + 0.5) / beats)
        ny = staff_top + INSTRUMENT_POSITIONS[note.instrument] * SPACING
        stem_len = 28
        is_cym = note.instrument.is_cymbal()
        stem_up = INSTRUMENT_POSITIONS[note.instrument] < 2.0

        if is_cym:
            s = NOTEHEAD_W // 2
            self.canvas.create_line(nx - s, ny - s, nx + s, ny + s, fill=DARK_NOTE, width=2)
            self.canvas.create_line(nx + s, ny - s, nx - s, ny + s, fill=DARK_NOTE, width=2)
        else:
            pts = _rotated_notehead_pts(nx, ny, NOTEHEAD_W // 2, NOTEHEAD_H // 2)
            self.canvas.create_polygon(*pts, fill=DARK_NOTE, outline=DARK_NOTE, smooth=True)

        stem_x = nx + (NOTEHEAD_W // 3 if stem_up else -NOTEHEAD_W // 3)
        if beam_info and int(note.beat) in beam_info["beats"]:
            stem_end = beam_info["common_tip"]
        elif stem_up:
            stem_end = (ny - NOTEHEAD_H // 2 - 1) - stem_len
        else:
            stem_end = (ny + NOTEHEAD_H // 2 + 1) + stem_len
        if stem_up:
            stem_start = ny - NOTEHEAD_H // 2 - 1
        else:
            stem_start = ny + NOTEHEAD_H // 2 + 1
        self.canvas.create_line(stem_x, stem_start, stem_x, stem_end, fill=DARK_NOTE, width=2)

        if beam_info and int(note.beat) in beam_info["beats"]:
            return
        flag_y = stem_end
        if note.duration in (Duration.EIGHTH, Duration.TRIOLET):
            self._draw_flag(stem_x, flag_y, 1, stem_up)
        elif note.duration == Duration.SIXTEENTH:
            self._draw_flag(stem_x, flag_y, 2, stem_up)
        if note.duration == Duration.TRIOLET:
            dy = 14 if stem_up else -14
            self.canvas.create_text(stem_x, flag_y + dy, text="3",
                                    font=("Helvetica", 8, "bold"), fill=DARK_NOTE)

    def _draw_flag(self, x: float, y: float, count: int, up: bool = True):
        for i in range(count):
            off = i * 3
            sign = -1 if up else 1
            self.canvas.create_line(
                x, y + sign * off, x + 10, y + sign * (-8 - off),
                fill=DARK_NOTE, width=2, capstyle=tk.ROUND,
            )

    def _get_system_and_measure(self, x: float, y: float) -> tuple[int, int, float] | None:
        for sys_info in self._layout_systems:
            st = sys_info["staff_top"]
            sh = 5 * SPACING + SYSTEM_SPACING
            if st <= y <= st + sh:
                for j in range(sys_info["start_idx"], sys_info["end_idx"]):
                    local_j = j - sys_info["start_idx"]
                    mx = STAFF_LEFT + local_j * sys_info["actual_mw"]
                    if mx <= x <= mx + sys_info["actual_mw"]:
                        measure = self.partiture.measures[j]
                        beat = (x - mx) / sys_info["actual_mw"] * measure.beats() - 0.5
                        max_beat = max(0.0, measure.beats() - 1.0)
                        beat = max(0.0, min(max_beat, round(beat)))
                        return j, beat, st
        return None

    def _instrument_from_y(self, y: float, staff_top: float) -> Instrument | None:
        snapped = round((y - staff_top) / SPACING)
        best = None
        for instr in INSTRUMENTS_ORDERED:
            iy = staff_top + INSTRUMENT_POSITIONS[instr] * SPACING
            iy_snapped = round((iy - staff_top) / SPACING)
            if iy_snapped == snapped:
                best = instr
                break
        return best

    def _on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        result = self._get_system_and_measure(x, y)
        if result is None:
            return
        mi, beat, staff_top = result
        instr = self._instrument_from_y(y, staff_top)
        if instr is None:
            return
        measure = self.partiture.measures[mi]
        existing = measure.find_note_at(beat, instr)
        if existing is not None:
            measure.remove_note_at(beat, instr)
        else:
            note = Note(instrument=instr, beat=beat, duration=self.selected_duration)
            measure.add_note(note)
        self.render()

    def _on_right_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        result = self._get_system_and_measure(x, y)
        if result is None:
            return
        mi, beat, staff_top = result
        instr = self._instrument_from_y(y, staff_top)
        if instr is None:
            return
        measure = self.partiture.measures[mi]
        measure.remove_note_at(beat, instr)
        self.render()

    def set_instrument(self, instr: Instrument):
        self.selected_instrument = instr

    def set_duration(self, dur: Duration):
        self.selected_duration = dur

    def get_canvas(self):
        return self.canvas
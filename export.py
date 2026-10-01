from model import Instrument, Duration, Partiture, Note, Measure
import math

SPACING = 10
NOTEHEAD_W = 8
NOTEHEAD_H = 6
MARGIN = 6

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


def instr_y(instr: Instrument) -> float:
    return INSTRUMENT_POSITIONS[instr] * SPACING


def export_pdf(partiture: Partiture, path: str):
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError(
            "Le module 'fpdf2' est requis pour exporter en PDF.\n"
            "Installez-le avec : pip install fpdf2"
        )

    pdf = FPDF(unit="pt", format="A4")
    pdf.add_page()

    pw = pdf.w
    ph = pdf.h
    margin = 50
    staff_left = margin
    usable_w = pw - 2 * margin
    staff_top = 90
    bottom_margin = 60

    measures = partiture.measures
    n_measures = len(measures)

    staff_h = 5 * SPACING
    system_h = staff_h + 36
    title_h = 80

    avail_h = ph - title_h - bottom_margin
    max_systems = max(1, int(avail_h / system_h))

    n_systems = min(max_systems, n_measures)
    meas_per_sys = math.ceil(n_measures / n_systems) if n_systems > 0 else 1
    mw = usable_w / meas_per_sys

    def draw_staff_lines(top_y: float, line_w: float):
        for i in range(5):
            y = top_y + i * SPACING
            pdf.line(staff_left, y, staff_left + line_w, y)
        cx = staff_left - 18
        top = top_y - 4
        bot = top_y + 4 * SPACING + 4
        bar_w = 3
        gap = 4
        pdf.rect(cx - bar_w, top, bar_w, bot - top, style="DF")
        pdf.rect(cx + gap, top, bar_w, bot - top, style="DF")

    def draw_barline(x: float, top_y: float, is_double: bool = False, is_start: bool = False):
        top = top_y - 8
        bot = top_y + 4 * SPACING + 8
        if is_double:
            pdf.set_line_width(2)
            pdf.line(x + 4, top, x + 4, bot)
            pdf.set_line_width(0.5)
            pdf.line(x, top, x, bot)
        elif is_start:
            pdf.set_line_width(1.5)
            pdf.line(x, top, x, bot)
        else:
            pdf.set_line_width(0.5)
            pdf.line(x, top, x, bot)
        pdf.set_line_width(0.5)

    def draw_note(mx: float, note: Note, top_y: float, beats: int = 4, mw_local: float = mw):
        nx = mx + (mw_local * (note.beat + 0.5) / beats)
        ny = instr_y(note.instrument) + top_y
        sl = 22
        is_cym = note.instrument.is_cymbal()

        pdf.set_fill_color(0, 0, 0)
        pdf.set_draw_color(0, 0, 0)

        if is_cym:
            s = NOTEHEAD_W // 2
            pdf.line(nx - s, ny - s, nx + s, ny + s)
            pdf.line(nx + s, ny - s, nx - s, ny + s)
        else:
            pdf.ellipse(
                nx - NOTEHEAD_W // 2, ny - NOTEHEAD_H // 2,
                NOTEHEAD_W, NOTEHEAD_H, style="DF",
            )

        stem_top = ny + NOTEHEAD_H // 2 + 1
        stem_bot = stem_top + sl
        pdf.line(nx, stem_top, nx, stem_bot)
        if note.duration in (Duration.EIGHTH, Duration.TRIOLET):
            pdf.line(nx, stem_bot, nx + 7, stem_bot - 6)
        elif note.duration == Duration.SIXTEENTH:
            pdf.line(nx, stem_bot, nx + 7, stem_bot - 6)
            pdf.line(nx, stem_bot - 4, nx + 7, stem_bot - 10)
        if note.duration == Duration.TRIOLET:
            pdf.set_font("Helvetica", "B", 8)
            pdf.text(nx - 2, stem_bot - 14, "3")
            pdf.set_font("Helvetica", "", 10)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(51, 51, 51)
    pdf.text(staff_left, 30, partiture.title)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(102, 102, 102)
    pdf.text(staff_left + 2, 52, f"Par : {partiture.author}")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(102, 102, 102)
    pdf.text(staff_left + 2, 68, f"{partiture.tempo} BPM")

    idx = 0
    for sys_idx in range(n_systems):
        start = sys_idx * meas_per_sys
        end = min(start + meas_per_sys, n_measures)
        line_measures = measures[start:end]
        n_in_line = len(line_measures)
        actual_mw = usable_w / n_in_line if n_in_line > 0 else mw
        y_off = staff_top + sys_idx * system_h

        draw_staff_lines(y_off, usable_w)

        for j, measure in enumerate(line_measures):
            mx = staff_left + j * actual_mw
            draw_barline(mx, y_off, is_start=(j == 0))

            if start + j == 0:
                ts = measure.time_sig
                cx = mx + 14
                mid = y_off + 1.5 * SPACING
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(51, 51, 51)
                pdf.text(cx, mid - 3, str(ts[0]))
                pdf.text(cx, mid + 12, str(ts[1]))
                pdf.set_text_color(102, 102, 102)

            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(153, 153, 153)
            pdf.text(mx + 2, y_off - 14, str(start + j + 1))
            pdf.set_text_color(0, 0, 0)

            for note in measure.notes:
                draw_note(mx, note, y_off, measure.beats(), actual_mw)

        last_x = staff_left + n_in_line * actual_mw
        draw_barline(last_x, y_off, is_double=(end >= n_measures))

    pdf.output(path)

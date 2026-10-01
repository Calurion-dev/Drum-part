from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple


class Instrument(Enum):
    BASS_DRUM = "Grosse Caisse"
    SNARE = "Caisse Claire"
    HI_HAT = "Charleston"
    RIDE_CYMBAL = "Ride"
    CRASH_CYMBAL = "Crash"
    HIGH_TOM = "Tom Haute"
    MID_TOM = "Tom Medium"
    FLOOR_TOM = "Tom Basse"

    def is_cymbal(self) -> bool:
        return self in (Instrument.HI_HAT, Instrument.RIDE_CYMBAL, Instrument.CRASH_CYMBAL)


class Duration(Enum):
    QUARTER = 1.0
    EIGHTH = 0.5
    SIXTEENTH = 0.25
    TRIOLET = 0.3333333333333333

    def label(self) -> str:
        labels = {
            Duration.QUARTER: "Noire",
            Duration.EIGHTH: "Croche",
            Duration.SIXTEENTH: "D-Croche",
            Duration.TRIOLET: "Triolet",
        }
        return labels.get(self, "")

    def divisions(self) -> int:
        return {Duration.QUARTER: 4, Duration.EIGHTH: 8, Duration.SIXTEENTH: 16, Duration.TRIOLET: 12}[self]


@dataclass
class Note:
    instrument: Instrument
    beat: float
    duration: Duration = Duration.QUARTER


@dataclass
class Measure:
    notes: List[Note] = field(default_factory=list)
    time_sig: Tuple[int, int] = (4, 4)

    def beats(self) -> int:
        return self.time_sig[0]

    def add_note(self, note: Note) -> None:
        max_notes = self.beats() * 8
        existing_at_beat = any(abs(n.beat - note.beat) < 0.01 for n in self.notes)
        if not existing_at_beat and len(self.notes) >= max_notes:
            return
        self.notes = [
            n
            for n in self.notes
            if not (abs(n.beat - note.beat) < 0.01 and n.instrument == note.instrument)
        ]
        self.notes.append(note)

    def remove_note_at(self, beat: float, instrument: Instrument) -> bool:
        for i, n in enumerate(self.notes):
            if abs(n.beat - beat) < 0.01 and n.instrument == instrument:
                self.notes.pop(i)
                return True
        return False

    def find_note_at(self, beat: float, instrument: Instrument) -> Note | None:
        for n in self.notes:
            if abs(n.beat - beat) < 0.01 and n.instrument == instrument:
                return n
        return None

    def to_dict(self) -> dict:
        return {
            "time_sig": list(self.time_sig),
            "notes": [
                {
                    "instrument": n.instrument.name,
                    "beat": n.beat,
                    "duration": n.duration.name,
                }
                for n in self.notes
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Measure":
        m = Measure(time_sig=tuple(data["time_sig"]))
        for nd in data["notes"]:
            m.notes.append(
                Note(
                    instrument=Instrument[nd["instrument"]],
                    beat=nd["beat"],
                    duration=Duration[nd["duration"]],
                )
            )
        return m


@dataclass
class Partiture:
    title: str = "Sans titre"
    author: str = "Lucas RIVOLIER"
    tempo: int = 120
    measures: List[Measure] = field(default_factory=lambda: [Measure()])

    def add_measure(self) -> None:
        ts = self.measures[-1].time_sig if self.measures else (4, 4)
        self.measures.append(Measure(time_sig=ts))

    def remove_last_measure(self) -> bool:
        if len(self.measures) > 1:
            self.measures.pop()
            return True
        return False

    def set_time_sig(self, beats: int, unit: int = 4) -> None:
        for m in self.measures:
            m.time_sig = (beats, unit)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "tempo": self.tempo,
            "measures": [m.to_dict() for m in self.measures],
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Partiture":
        p = Partiture(title=data.get("title", "Sans titre"), author=data.get("author", "Lucas RIVOLIER"), tempo=data.get("tempo", 120))
        p.measures = [Measure.from_dict(md) for md in data.get("measures", [Measure().to_dict()])]
        return p

    @classmethod
    def from_json(cls, text: str) -> "Partiture":
        import json
        return cls.from_dict(json.loads(text))

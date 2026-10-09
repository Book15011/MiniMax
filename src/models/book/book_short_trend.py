"""Frozen trend hypothesis; research/book/short_study/PROTOCOL.md."""
from ._short_study import DirectionalStudy

class Candidate(DirectionalStudy):
    def __init__(self):
        super().__init__("book_short_trend", "trend")

MODEL = Candidate()

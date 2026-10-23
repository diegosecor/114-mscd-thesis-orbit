"""Explicit display aliases for names observed in this KiltHub collection.

The catalogue's advisors string is kept verbatim after separator cleanup. This
table only groups observed abbreviations/spelling variants under faculty names.
It never infers an advisor for a missing source field.
Faculty name references: architecture.cmu.edu/profiles/{daragh-byrne,
daniel-cardoso-llach,jimmy-wei-chun-cheng}, and the CMU CodeLab faculty listing.
"""
import re

ALIASES = {
    "Darragh Byrne": "Daragh Byrne",
    "Daragh Byrme": "Daragh Byrne",
    "Daniel C Llach": "Daniel Cardoso Llach",
    "Daniel Cardoso": "Daniel Cardoso Llach",
    "Joshus Bard": "Joshua Bard",
    "Vernell Noel": "Vernelle A. A. Noel",
    "Vernelle Noel": "Vernelle A. A. Noel",
    "Vernelle A.A. Noel": "Vernelle A. A. Noel",
    "Vernelle A. A. VN Noel": "Vernelle A. A. Noel",
    "Dina El Zanfaly": "Dina El-Zanfaly",
    "Molly Steenson": "Molly Wright Steenson",
    "Jimmy Cheng": "Jimmy Wei-Chun Cheng",
    "Jimmy Wei-Chun Chung": "Jimmy Wei-Chun Cheng",
}


# Split published people, apply explicit aliases, and deduplicate in source order.
def advisor_names(value: str) -> list[str]:
    names = (name.strip() for name in re.split(r"[,;\n]+", value or ""))
    return list(dict.fromkeys(ALIASES.get(name, name) for name in names if name))

import re

# Deterministic emergency screen. Runs before any network call and cannot
# be overridden by the model. Patterns are intentionally broad: a false
# alarm sends someone to a hospital, a miss does the opposite.
#
# Note the [\w\s]{0,N} gaps. People do not write keyword-adjacent prose —
# they write "chest feels heavy", "face is drooping", "ending my life".
# Requiring adjacent words is how a screen like this silently misses the
# cases it exists for. The gaps use [\w\s] rather than . so a match can
# never span the " | " separator between two different symptom phrases.
RED_FLAGS: tuple[tuple[str, str, int], ...] = (
    # Cardiac — both word orders: "crushing chest pain", "heaviness in my chest".
    (r"(crush|squeez|press|tight|heav)\w*[\w\s]{0,20}chest"
     r"|chest[\w\s]{0,20}(pain|pressure|tight|heav|squeez|crush)",
     "CARDIOLOGIST", 90),
    (r"pain[\w\s]{0,25}(radiat|spread|shoot)\w*[\w\s]{0,20}(arm|jaw|shoulder)",
     "CARDIOLOGIST", 90),

    # Airway / breathing.
    (r"can(no|')?t breathe|cannot breathe|struggl\w*[\w\s]{0,15}breath"
     r"|gasping|fighting for (air|breath)",
     "PULMONOLOGIST", 90),

    # Stroke — FAST.
    # Both word orders again: "slurred speech" and "speech is slurred".
    (r"face[\w\s]{0,12}droop|slurred speech|speech[\w\s]{0,12}slurr"
     r"|sudden[\w\s]{0,20}(weakness|numbness)|one side of (my|the) (face|body)",
     "NEUROLOGIST", 95),
    (r"unconscious|unresponsive|seizure|convuls\w*", "NEUROLOGIST", 95),

    # Anaphylaxis.
    (r"anaphyla|throat[\w\s]{0,12}(clos|swell|tight)|tongue[\w\s]{0,10}swell",
     "GENERAL_PHYSICIAN", 95),

    # Haemorrhage.
    (r"(severe|heavy|profuse)[\w\s]{0,10}bleeding|bleeding[\w\s]{0,15}won'?t stop",
     "GENERAL_PHYSICIAN", 90),

    # Self-harm / suicidal ideation.
    (r"suicid|kill myself|end(ing|s)?[\w\s]{0,5}my (own )?life"
     r"|take my own life|self ?harm|don'?t want to (live|be here)",
     "PSYCHIATRIST", 95),

    # GI bleeding.
    (r"cough\w*[\w\s]{0,10}blood|vomit\w*[\w\s]{0,10}blood|blood in my vomit",
     "GASTROENTEROLOGIST", 85),

    # Meningitis.
    (r"stiff neck[\w\s]{0,30}(fever|rash)|purple rash|rash[\w\s]{0,20}doesn'?t fade",
     "GENERAL_PHYSICIAN", 90),
)

_COMPILED = [(re.compile(p, re.IGNORECASE), spec, score) for p, spec, score in RED_FLAGS]


def screen(symptoms: list[str]) -> tuple[str, int, list[str]] | None:
    """Return (specialization, severity, matched) if any red flag fires."""
    text = " | ".join(symptoms).lower()

    best: tuple[str, int, list[str]] | None = None
    for pattern, spec, score in _COMPILED:
        if not pattern.search(text):
            continue
        matched = [s for s in symptoms if pattern.search(s.lower())]
        if best is None or score > best[1]:
            best = (spec, score, matched)

    return best

"""Quality suite — run manually against the real API, never in CI.

    python -m tests.run_eval

Grow this to ~50 cases from real user phrasing. Re-run whenever you change
the prompt, the model ID, or the temperature, and write the score in NOTES.md.
Without it you are tuning prompts by vibes.
"""

CASES: list[tuple[list[str], str]] = [
    (["burning when I pee and going often"],                "UROLOGIST"),
    (["wheezing at night, worse in winter"],                "PULMONOLOGIST"),
    (["my 3 year old has a fever and is pulling her ear"],  "PEDIATRICIAN"),
    (["can't sleep, no appetite, hopeless for weeks"],      "PSYCHIATRIST"),
    (["blurry vision and floaters in one eye"],             "OPHTHALMOLOGIST"),
    (["sharp pain in lower right belly since last night"],  "GASTROENTEROLOGIST"),
    (["tired all the time, thirsty, losing weight"],        "ENDOCRINOLOGIST"),
    (["itchy red patches on my elbows for two weeks"],      "DERMATOLOGIST"),
    (["my knee locks up when I climb stairs"],              "ORTHOPEDIC"),
    (["periods have been irregular for six months"],        "GYNECOLOGIST"),
    (["ringing in my ears and muffled hearing"],            "ENT_SPECIALIST"),
    (["gum bleeds when I brush, one tooth aches"],          "DENTIST"),
    (["swelling in my ankles and foamy urine"],             "NEPHROLOGIST"),
    (["a mole that changed shape and colour"],              "DERMATOLOGIST"),
    (["just feel run down, nothing specific"],              "GENERAL_PHYSICIAN"),
]

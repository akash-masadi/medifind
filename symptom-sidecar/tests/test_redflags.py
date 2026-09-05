import pytest

from app import redflags

# Every entry here is prose a real person might type. Adjacent-keyword
# phrasings ("chest pain") are the easy case; these are the ones that
# catch a screen out.
MUST_FIRE = [
    ["crushing chest pain"],
    ["chest feels heavy", "left arm tingling"],
    ["there is a heaviness in my chest"],
    ["tightness in my chest since this morning"],
    ["pain that keeps radiating down my left arm"],
    ["my face is drooping on one side"],
    ["his speech is slurred and he seems confused"],
    ["sudden weakness down the right side"],
    ["I can't breathe properly"],
    ["she is struggling to breathe"],
    ["I have been thinking about ending my life"],
    ["I don't want to live any more"],
    ["throat closing after eating peanuts"],
    ["he had a seizure ten minutes ago"],
    ["coughing up blood this morning"],
]

MUST_NOT_FIRE = [
    ["mild headache for two days"],
    ["itchy rash on elbows"],
    ["tooth sensitive to cold"],
    ["chest congestion and a runny nose"],
    ["breathing exercises make my back feel better"],
    ["periods have been irregular for six months"],
    ["my knee locks up when I climb stairs"],
]


@pytest.mark.parametrize("symptoms", MUST_FIRE)
def test_emergencies_are_caught(symptoms):
    assert redflags.screen(symptoms) is not None


@pytest.mark.parametrize("symptoms", MUST_NOT_FIRE)
def test_everyday_symptoms_pass_through(symptoms):
    assert redflags.screen(symptoms) is None


def test_highest_severity_wins():
    # "unconscious" (95) must beat "chest pain" (90).
    spec, severity, _ = redflags.screen(["chest pain", "went unconscious"])
    assert spec == "NEUROLOGIST"
    assert severity == 95

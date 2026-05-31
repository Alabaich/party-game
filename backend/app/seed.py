from sqlalchemy.orm import Session
from .models import Task, TaskType

# (description, type, is_alcoholic)
SEED_TASKS = [
    # ---- Type 1: SOLO ----
    ("Find the hidden Perry the Platypus and take a photo with him.", TaskType.SOLO, False),
    ("Take a selfie wearing the Birthday Person's party hat.", TaskType.SOLO, False),
    ("Try to chug a beverage in under 30 seconds. Just try your best! (Record on video).", TaskType.SOLO, True),
    ("Take a cool selfie with the birthday person.", TaskType.SOLO, False),
    ("Record a video balancing a glass (water is fine) on your head for 10 seconds.", TaskType.SOLO, False),
    ("Video yourself taking a sip of your drink without using your hands.", TaskType.SOLO, True),
    ("Upload a photo of your goofiest face. Warning: everyone will see it on the big screen!", TaskType.SOLO, False),
    ("Record a short video toast/wish (minimum 15 seconds).", TaskType.SOLO, False),
    ("Record your reaction eating a spoonful of ketchup & mustard (use BBQ/relish if allergic).", TaskType.SOLO, False),
    ("Climb under the table and take an epic photo/selfie from there.", TaskType.SOLO, False),
    ("Take a selfie where you are trying to touch the camera lens with your nose.", TaskType.SOLO, False),
    ("Take a photo holding 5 completely different random objects at the same time.", TaskType.SOLO, False),
    ("Post a party Story (film anything) and upload a screenshot of it as proof.", TaskType.SOLO, False),

    # ---- Type 2: TARGETED ----
    ("Beat {target} in Mortal Kombat (take a photo of the victory screen).", TaskType.TARGETED, False),
    ("Secretly take a photo of {target} laughing.", TaskType.TARGETED, False),
    ("Get {target} to say \"Hakuna Matata\" on video without telling them why.", TaskType.TARGETED, False),
    ("Sneakily stick an \"I didn't even notice\" note on {target}'s back and photograph it.", TaskType.TARGETED, False),
    ("Swap a clothing item (hat, glasses, jacket) with {target} and take a photo together.", TaskType.TARGETED, False),
    ("Record a video: walk up to {target}, clink glasses, give an unexpected compliment, and drink.", TaskType.TARGETED, True),
    ("Record a blitz interview with {target} asking just one question: \"What do you think of this party?\".", TaskType.TARGETED, False),
    ("Take a photo of {target} holding or standing in front of something blue.", TaskType.TARGETED, False),
    ("Take a perfectly timed photo of {target} with their eyes closed.", TaskType.TARGETED, False),
    ("Take a perfect photobomb selfie with {target} in the background completely unaware.", TaskType.TARGETED, False),
    ("Photograph {target} posing as a VIP, with two other people standing next to them as serious bodyguards.", TaskType.TARGETED, False),

    # ---- Type 3: PAIRED ----
    ("You and {target}: take a joint photo posing like epic gods.", TaskType.PAIRED, False),
    ("You and {target}: drink Brüderschaft (arms intertwined) and take a photo.", TaskType.PAIRED, True),
    ("You and {target}: record a joint dance — minimum 10 seconds.", TaskType.PAIRED, False),
    ("You and {target}: recreate the Titanic pose and take a photo.", TaskType.PAIRED, False),
    ("You and {target}: play Rock Paper Scissors on video — loser does 3 squats.", TaskType.PAIRED, False),
    ("You and {target}: joint mirror selfie looking as gangsta as possible.", TaskType.PAIRED, False),
    ("You and {target}: create a secret handshake (min 3 moves) — record on video.", TaskType.PAIRED, False),
    ("You and {target}: forced perspective photo — one holds the other in their palm.", TaskType.PAIRED, False),
    ("You and {target}: swap one shoe and take a joint photo of your feet.", TaskType.PAIRED, False),
    ("You and {target}: one delivers a toast to 5 people — the other photographs their confused faces.", TaskType.PAIRED, True),
]


def seed_tasks_if_empty(db: Session) -> None:
    if db.query(Task).count() > 0:
        return
    for desc, ttype, alco in SEED_TASKS:
        db.add(Task(description=desc, type=ttype, is_alcoholic=alco))
    db.commit()

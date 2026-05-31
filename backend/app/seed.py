from sqlalchemy.orm import Session
from .models import Task, TaskType

# (description, type, is_alcoholic)
SEED_TASKS = [
    # ---- Type 1: SOLO ----
    ("Find the hidden Perry the Platypus and take a photo with him.", TaskType.SOLO, False),
    ("Take a selfie wearing the Birthday Person's party hat.", TaskType.SOLO, False),
    ("Try to chug a can of any beverage in under 30 seconds. The task is about the attempt itself, it's not that easy! (Record the process on video).", TaskType.SOLO, True),
    ("Take a cool selfie with the birthday person.", TaskType.SOLO, False),
    ("Balance a glass (water is fine) on your head for 10 seconds and record it on video.", TaskType.SOLO, False),
    ("Take a sip of your drink without touching the can or glass with your hands (record on video).", TaskType.SOLO, True),
    ("Make the goofiest face into the camera and upload this photo (Warning: everyone will see this on the big screen at the end!).", TaskType.SOLO, False),
    ("Record a short video toast/wish (minimum 15 seconds).", TaskType.SOLO, False),
    ("Eat a full spoonful of ketchup and mustard (if allergic, replace with BBQ sauce or relish) and record your reaction on video/photo.", TaskType.SOLO, False),
    ("Climb under the table and take an epic photo/selfie from there.", TaskType.SOLO, False),
    ("Take a selfie where you are trying to touch the camera lens with your nose.", TaskType.SOLO, False),
    ("Take a photo of yourself holding 5 completely different random objects in your hands at the same time.", TaskType.SOLO, False),
    ("Post a Story from the party (you can film anything). As proof, upload a screenshot of the published story.", TaskType.SOLO, False),

    # ---- Type 2: TARGETED ----
    ("Beat {target} in Mortal Kombat (take a photo of the victory screen).", TaskType.TARGETED, False),
    ("Secretly take a photo of {target} laughing.", TaskType.TARGETED, False),
    ("Get {target} to say \"Hakuna Matata\" on video without telling them why.", TaskType.TARGETED, False),
    ("Sneakily stick a note/sticker saying \"I didn't even notice\" on {target}'s back and take a photo of the sticker on their back.", TaskType.TARGETED, False),
    ("Swap one piece of clothing (hat, glasses, jacket) with {target} and take a group photo.", TaskType.TARGETED, False),
    ("Walk up to {target}, clink glasses, give them an unexpected compliment, and take a drink (record on video).", TaskType.TARGETED, True),
    ("Record a video of yourself doing a blitz interview with {target} asking one question: \"What do you think of this party?\".", TaskType.TARGETED, False),
    ("Find something blue in the room and take a photo of {target} in front of it or holding it.", TaskType.TARGETED, False),
    ("Catch the perfect moment and take a photo of {target} with their eyes closed.", TaskType.TARGETED, False),
    ("Take a selfie where {target} is in the background and has no idea they are being photographed (the perfect photobomb).", TaskType.TARGETED, False),
    ("Take a photo where {target} poses like a boss/VIP and two other people (doesn't matter who) stand next to them with serious faces as their bodyguards.", TaskType.TARGETED, False),

    # ---- Type 3: PAIRED ----
    ("Take a joint photo posing like epic gods (Greek, Hindu, or just with maximum divine majesty).", TaskType.PAIRED, False),
    ("Drink together \"Brüderschaft\" style (with arms intertwined)! Find each other and take a joint photo during the process.", TaskType.PAIRED, True),
    ("Dance together! Record a joint dance for at least 10 seconds on video.", TaskType.PAIRED, False),
    ("Recreate the legendary pose from \"Titanic\" together and take a photo.", TaskType.PAIRED, False),
    ("Play \"Rock, Paper, Scissors\" on video (the loser must do 3 squats on camera).", TaskType.PAIRED, False),
    ("Take a joint mirror selfie, but both of you must look as gangsta/swag as possible (like 2000s rappers).", TaskType.PAIRED, False),
    ("Create a secret handshake (minimum 3 moves) and record it on video.", TaskType.PAIRED, False),
    ("Take a joint photo where one of you is \"holding\" the other in the palm of your hand (using forced perspective).", TaskType.PAIRED, False),
    ("Swap a shoe on one foot (each puts on one of the partner's sneakers) and take a joint photo of your feet. If the foot doesn't fit — at least take a photo of you trying to squeeze it in.", TaskType.PAIRED, False),
    ("Find each other and assign roles! One of you must gather at least 5 people and, with a completely serious face, deliver the toast. The other must take a photo of the confused and baffled faces of the listeners at that exact moment.", TaskType.PAIRED, True),
]


def seed_tasks_if_empty(db: Session) -> None:
    if db.query(Task).count() > 0:
        return
    for desc, ttype, alco in SEED_TASKS:
        db.add(Task(description=desc, type=ttype, is_alcoholic=alco))
    db.commit()

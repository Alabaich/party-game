"""Task packs a host can load into a game.

Each task: (description, type, is_alcoholic). Use {target} for the other
player in TARGETED / PAIRED tasks.
"""
from ..models import TaskType

S, T, P = TaskType.SOLO, TaskType.TARGETED, TaskType.PAIRED

HALLOWEEN = [
    # ---- SOLO ----
    ("Take a selfie in your costume next to the spookiest decoration you can find.", S, False),
    ("Snap a photo of the best pumpkin or jack-o'-lantern at the party.", S, False),
    ("Record a 5-second video of your best monster roar.", S, False),
    ("Find someone who lives in the OTHER building and take a selfie together.", S, False),
    ("Find a neighbour you have never talked to before, learn their name, and take a selfie together.", S, False),
    ("Find someone who has lived here longer than you. Ask for their favourite spot nearby and take a photo together.", S, False),
    ("Take a group photo with at least 5 people in costume.", S, False),
    ("Record a short hello video: your first name and your favourite Halloween candy.", S, False),
    ("Photograph the costume you think deserves first prize (ask permission first!).", S, False),
    ("Strike your scariest pose next to the candy table.", S, False),
    ("Find someone who loves the same candy as you and take a photo holding it together.", S, False),
    ("Get a high-five from a Prism team member on video.", S, False),
    ("Find someone whose costume matches a colour of yours and take a photo together.", S, False),
    # ---- TARGETED ----
    ("Find {target} and find out what they're dressed as. Take a photo of them in costume.", T, False),
    ("Ask {target} for their favourite scary movie and record them saying it.", T, False),
    ("Film {target} doing their best zombie walk.", T, False),
    ("Take a selfie with {target} where you both look absolutely terrified.", T, False),
    ("Ask {target} how long they've lived in the building and take a photo together.", T, False),
    ("Trade a piece of candy with {target} and photograph the trade.", T, False),
    ("Get {target} to teach you a dance move. Record it.", T, False),
    ("Introduce {target} to someone they haven't met yet. Photo of the three of you.", T, False),
    ("Ask {target} about their best Halloween memory and record 10 seconds of the story.", T, False),
    ("Pose with {target} as a vampire and their (willing) victim.", T, False),
    # ---- PAIRED ----
    ("You and {target}: recreate a famous horror movie poster.", P, False),
    ("You and {target}: tell a 10-second spooky story on video, one sentence each.", P, False),
    ("You and {target}: haunt the party as two ghosts. Photo proof.", P, False),
    ("You and {target}: find a third neighbour and make a monster trio photo.", P, False),
    ("You and {target}: slow-motion scream video.", P, False),
    ("You and {target}: rate each other's costumes from 1 to 10 on video.", P, False),
    ("You and {target}: make a spider with your hands (8 fingers!) and take a photo.", P, False),
    ("You and {target}: pretend to be terrified of something tiny. Photo.", P, False),
    ("You and {target}: find out one thing you have in common and announce it on video.", P, False),
]

DIWALI = [
    # ---- SOLO ----
    ("Take a selfie next to the most beautiful diya or light decoration.", S, False),
    ("Photograph the most colourful outfit at the party (ask permission first!).", S, False),
    ("Find someone who lives in the OTHER building and take a selfie together.", S, False),
    ("Find a neighbour you've never met, learn their name, and take a photo together.", S, False),
    ("Take a photo of your favourite sweet on the table before you eat it.", S, False),
    ("Record a 10-second video wishing everyone a Happy Diwali in any language.", S, False),
    ("Take a group photo with at least 5 people making a heart with their hands.", S, False),
    ("Find someone who has lived here longer than you and ask for their favourite spot nearby. Photo together.", S, False),
    ("Photograph a rangoli or the brightest light in the room.", S, False),
    ("Get a high-five from a Prism team member on video.", S, False),
    # ---- TARGETED ----
    ("Ask {target} how they celebrate Diwali or another favourite holiday. Record 10 seconds.", T, False),
    ("Take a selfie with {target} holding a light (phone flashlight counts!).", T, False),
    ("Ask {target} for their favourite festive sweet and photograph them with a sweet.", T, False),
    ("Learn a dance move from {target}. Record it.", T, False),
    ("Introduce {target} to someone they haven't met yet. Photo of the three of you.", T, False),
    ("Ask {target} how long they've lived in the building and take a photo together.", T, False),
    ("Take a photo of {target} with the best smile of the night.", T, False),
    ("Find out a wish {target} has for the new year and record them saying it.", T, False),
    # ---- PAIRED ----
    ("You and {target}: strike a Bollywood movie poster pose.", P, False),
    ("You and {target}: dance together for 10 seconds on video.", P, False),
    ("You and {target}: make a heart shape with a light and take a photo.", P, False),
    ("You and {target}: find a third neighbour and take a festive trio photo.", P, False),
    ("You and {target}: find one thing you have in common and announce it on video.", P, False),
    ("You and {target}: share a sweet and photograph the moment.", P, False),
    ("You and {target}: mirror selfie in your festive best.", P, False),
    ("You and {target}: record a joint wish for the building for the year ahead.", P, False),
]

BIRTHDAY = [
    # ---- Type 1: SOLO ----
    ("Find the hidden Perry the Platypus and take a photo with him.", S, False),
    ("Take a selfie wearing the Birthday Person's party hat.", S, False),
    ("Try to chug a beverage in under 30 seconds. Just try your best! (Record on video).", S, True),
    ("Take a cool selfie with the birthday person.", S, False),
    ("Record a video balancing a glass (water is fine) on your head for 10 seconds.", S, False),
    ("Video yourself taking a sip of your drink without using your hands.", S, True),
    ("Upload a photo of your goofiest face. Warning: everyone will see it on the big screen!", S, False),
    ("Record a short video toast/wish (minimum 15 seconds).", S, False),
    ("Record your reaction eating a spoonful of ketchup & mustard (use BBQ/relish if allergic).", S, False),
    ("Climb under the table and take an epic photo/selfie from there.", S, False),
    ("Take a selfie where you are trying to touch the camera lens with your nose.", S, False),
    ("Take a photo holding 5 completely different random objects at the same time.", S, False),
    ("Post a party Story (film anything) and upload a screenshot of it as proof.", S, False),

    # ---- Type 2: TARGETED ----
    ("Beat {target} in Mortal Kombat (take a photo of the victory screen).", T, False),
    ("Secretly take a photo of {target} laughing.", T, False),
    ("Get {target} to say \"Hakuna Matata\" on video without telling them why.", T, False),
    ("Sneakily stick an \"I didn't even notice\" note on {target}'s back and photograph it.", T, False),
    ("Swap a clothing item (hat, glasses, jacket) with {target} and take a photo together.", T, False),
    ("Record a video: walk up to {target}, clink glasses, give an unexpected compliment, and drink.", T, True),
    ("Record a blitz interview with {target} asking just one question: \"What do you think of this party?\".", T, False),
    ("Take a photo of {target} holding or standing in front of something blue.", T, False),
    ("Take a perfectly timed photo of {target} with their eyes closed.", T, False),
    ("Take a perfect photobomb selfie with {target} in the background completely unaware.", T, False),
    ("Photograph {target} posing as a VIP, with two other people standing next to them as serious bodyguards.", T, False),

    # ---- Type 3: PAIRED ----
    ("You and {target}: take a joint photo posing like epic gods.", P, False),
    ("You and {target}: drink Brüderschaft (arms intertwined) and take a photo.", P, True),
    ("You and {target}: record a joint dance — minimum 10 seconds.", P, False),
    ("You and {target}: recreate the Titanic pose and take a photo.", P, False),
    ("You and {target}: play Rock Paper Scissors on video — loser does 3 squats.", P, False),
    ("You and {target}: joint mirror selfie looking as gangsta as possible.", P, False),
    ("You and {target}: create a secret handshake (min 3 moves) — record on video.", P, False),
    ("You and {target}: forced perspective photo — one holds the other in their palm.", P, False),
    ("You and {target}: swap one shoe and take a joint photo of your feet.", P, False),
    ("You and {target}: one delivers a toast to 5 people — the other photographs their confused faces.", P, True),
]

PACKS = {
    "halloween": ("🎃 Halloween — meet your neighbours", HALLOWEEN),
    "diwali": ("🪔 Diwali — festival of lights", DIWALI),
    "party": ("🎉 House party (original birthday set)", BIRTHDAY),
}

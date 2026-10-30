"""Host-configurable game settings (stored as JSON on Game.settings)."""
from typing import Literal
from pydantic import BaseModel, Field

Theme = Literal["party", "halloween", "diwali"]

# alcohol: yes/no; "no" means the player gets no alcoholic tasks
# choice:  pick one of `options` (e.g. building); shown to people looking for you
#          unless `private`
# yesno / text: just collected
# email: optional contact, always host-only
QuestionKind = Literal["alcohol", "choice", "yesno", "text", "email"]


class Question(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=500)
    kind: QuestionKind
    required: bool = True
    options: list[str] = []
    numeric: bool = False      # text answers: digits only (e.g. unit number)
    private: bool = False      # only the host sees the answer


class Prize(BaseModel):
    place: str = Field(max_length=20)   # "1", "2", "3" or a label like "Best photo"
    title: str = Field(max_length=200)


DEFAULT_CONSENT_BODY = """PHOTO, VIDEO AND MEDIA RELEASE

By checking "I agree" and joining this game, you confirm the following.

1. What we collect
To run the game we collect the name you enter, the answers to the questions on the sign-up screen (for example your building and unit number), and the photos and videos you upload. If you choose to give your email address, it is used only to send you photos from the event. We also record the time you gave this consent, your IP address and your browser type, as a record of your agreement.

2. How your photos and videos are used
Photos and videos you upload, and photos or videos of you uploaded by other players, may be:
  a) shown on screens at this event and visible to other players during and after the game;
  b) published by the organizer on its social media accounts (for example Instagram, Facebook, LinkedIn, TikTok);
  c) used by the organizer in marketing, advertising and promotional materials, in print and online, including its websites, newsletters and leasing materials.
Your first name may appear together with your photos. Your unit number and email are never published.

3. No payment
You grant the organizer a free, non-exclusive, worldwide, perpetual licence to use, copy, edit and publish this content for the purposes above. You will not receive any payment or royalty for this use.

4. Your content
Only upload photos and videos you took yourself or have the right to share. Before photographing someone, ask them. Do not upload anything offensive, unsafe or illegal. The organizer may remove any content at any time.

5. Children
Do not photograph children without their parent's or guardian's permission. If a person under 18 appears in content you upload, you confirm that you are their parent or guardian or that you have their guardian's permission.

6. Your choices
Participation is voluntary. You can ask the organizer at any time to remove your photos from the game gallery and to stop using them in new materials. Materials that were already printed or published before your request may not be possible to recall.

7. Storage
Your information and media are stored securely with our service providers and kept only as long as needed for the purposes above.

8. Contact
For questions or removal requests, contact the property management office.
"""


class ConsentSettings(BaseModel):
    enabled: bool = True
    title: str = Field(default="Photo & Media Release", max_length=200)
    summary: str = Field(
        default="Photos and videos you upload will be shown on the big screen during the "
                "event, and may be shared on social media and used in marketing and advertising.",
        max_length=1000)
    body: str = Field(default=DEFAULT_CONSENT_BODY, max_length=30000)
    checkbox_label: str = Field(
        default="I have read the Photo & Media Release and I agree to it.", max_length=300)


class GameSettings(BaseModel):
    theme: Theme = "party"
    welcome: str = Field(default="", max_length=1000)
    consent: ConsentSettings = ConsentSettings()
    questions: list[Question] = []
    allow_late_join: bool = True
    alcohol_tasks: bool = False
    # how many wildcard tasks a player may use instead of tasks they can't do
    max_wildcards: int = Field(default=2, ge=0, le=20)
    # public: anyone with the code sees the slideshow/gallery
    # host_only: only the host's logged-in browser (TV); players see their own uploads
    gallery: Literal["public", "host_only"] = "public"
    prizes: list[Prize] = []


def default_settings(theme: Theme = "party") -> GameSettings:
    return GameSettings(theme=theme, gallery="host_only")


def load_settings(raw: dict | None) -> GameSettings:
    raw = dict(raw or {})
    # pre-release games (birthday) had no consent step
    raw.setdefault("consent", {"enabled": False})
    return GameSettings.model_validate(raw)

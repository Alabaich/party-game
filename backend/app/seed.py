"""Пул тасок. Запускається один раз при старті, якщо таблиця порожня.
Редагуй описи під свою вечірку. Тримай баланс: достатньо НЕ-алкогольних
тасок кожного типу, щоб алко-ліміт для непитущих завжди можна було задовольнити.
"""
from sqlalchemy.orm import Session
from .models import Task, TaskType

# (description, type, is_alcoholic)
SEED_TASKS = [
    # ---- Type 1: SOLO ----
    ("Зроби 10 присідань і зніми це на відео", TaskType.SOLO, False),
    ("Заспівай приспів улюбленої пісні на камеру", TaskType.SOLO, False),
    ("Зроби смішне селфі з гримасою", TaskType.SOLO, False),
    ("Станцюй 15 секунд під будь-яку музику", TaskType.SOLO, False),
    ("Розкажи анекдот на камеру", TaskType.SOLO, False),
    ("Покажи свій найкращий 'дикий' танцювальний рух", TaskType.SOLO, False),
    ("Зобрази улюблену тварину 10 секунд", TaskType.SOLO, False),
    ("Зроби фото свого взуття під смішним кутом", TaskType.SOLO, False),
    ("Випий шот і покажи порожню чарку", TaskType.SOLO, True),
    ("Зроби 'cheers' у камеру зі своїм напоєм", TaskType.SOLO, True),

    # ---- Type 2: TARGETED ----
    ("Зроби комплімент гравцю {target} на камеру", TaskType.TARGETED, False),
    ("Обійми гравця {target} і зробіть фото", TaskType.TARGETED, False),
    ("Намалюй портрет гравця {target} за 1 хвилину", TaskType.TARGETED, False),
    ("Влаштуй армрестлінг з гравцем {target}", TaskType.TARGETED, False),
    ("Навчи гравця {target} будь-якого танцювального руху", TaskType.TARGETED, False),
    ("Зроби спільне фото-гримасу з гравцем {target}", TaskType.TARGETED, False),
    ("Розкажи гравцю {target} смішну історію на камеру", TaskType.TARGETED, False),
    ("Запропонуй гравцю {target} тост і випийте разом", TaskType.TARGETED, True),
    ("Чокнись напоями з гравцем {target}", TaskType.TARGETED, True),

    # ---- Type 3: PAIRED ----
    ("Зробіть смішне спільне селфі", TaskType.PAIRED, False),
    ("Зніміть відео, де ви разом співаєте куплет пісні", TaskType.PAIRED, False),
    ("Зробіть фото 'до і після' одного смішного образу", TaskType.PAIRED, False),
    ("Станцюйте парний танець 15 секунд", TaskType.PAIRED, False),
    ("Побудуйте вежу з будь-яких предметів удвох", TaskType.PAIRED, False),
    ("Зобразіть удвох відому сцену з фільму", TaskType.PAIRED, False),
    ("Випийте по чарці одночасно і зніміть це", TaskType.PAIRED, True),
    ("Зробіть спільний тост на камеру з напоями", TaskType.PAIRED, True),
]


def seed_tasks_if_empty(db: Session) -> None:
    if db.query(Task).count() > 0:
        return
    for desc, ttype, alco in SEED_TASKS:
        db.add(Task(description=desc, type=ttype, is_alcoholic=alco))
    db.commit()

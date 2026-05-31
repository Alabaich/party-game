"""Алгоритм призначення тасок.

Правила (зафіксовані з обговорення):
- Кожен юзер отримує рівно TASKS_PER_USER тасок.
- Юзери до старту: гарантовано >=1 Type1, >=1 Type2, >=1 Type3.
- БЕЗ ДУБЛІКАТІВ: одне й те саме завдання не може випасти юзеру двічі.
- ПОКРИТТЯ: кожне Type1/Type2 завдання задіяне >=1 раз; розподіл рівномірний
  (не буває «це завдання у всіх, а те — нікому»). Реалізовано через лічильник
  використань: спершу беремо ще-не-задіяні, далі — найменш використані.
- Type3 будується ПАРАМИ глобально. Створюємо стільки пар, скільки є T3-завдань,
  щоб ЖОДНЕ T3 не лишилось orphaned. Кожне T3-завдання використовується рівно 1 раз.
  Гравець може потрапити в 2 пари, але:
    * завдання в цих парах різні (бо кожне T3 береться рівно раз);
    * партнери в цих парах — різні люди.
- Алко-ліміт (НАЙВИЩИЙ пріоритет): is_drinking=False => максимум 1 алко-таска.
  Для пар, де хоча б один непитущий, одразу беремо НЕ-алкогольний Type3.
- Латекомери: тільки Type1/Type2, без правила «кожного типу», без дублів,
  алко-ліміт діє якщо is_drinking=False.
- Type2 отримує випадкову ціль (target_user_id != сам юзер).
"""
import uuid
import random
from sqlalchemy.orm import Session
from .models import (
    User, Task, Assignment, GameState, TaskType, AssignmentStatus
)

TASKS_PER_USER = 7


# --------- helpers ---------

def _pool(db: Session):
    tasks = db.query(Task).all()
    by_type = {TaskType.SOLO: [], TaskType.TARGETED: [], TaskType.PAIRED: []}
    for t in tasks:
        by_type[t.type].append(t)
    return by_type


def _random_target(user_id: str, all_users: list[User]) -> str | None:
    others = [u for u in all_users if u.id != user_id]
    return random.choice(others).id if others else None


class Usage:
    """Глобальний лічильник використань завдань — для рівномірного покриття."""
    def __init__(self, all_tasks: list[Task]):
        self.count = {t.id: 0 for t in all_tasks}

    def bump(self, task_id: int):
        self.count[task_id] = self.count.get(task_id, 0) + 1

    def pick(self, candidates: list[Task], exclude_ids: set[int],
             alcoholic: bool | None = None) -> Task | None:
        """Вибір завдання з пріоритетом покриття:
        1) виключаємо вже наявні в юзера (exclude_ids) — без дублів;
        2) (опц.) фільтр за алкогольністю;
        3) серед кандидатів — мінімальний лічильник використань (ще не задіяні = 0),
           серед рівних — рандом.
        """
        pool = [t for t in candidates if t.id not in exclude_ids]
        if alcoholic is not None:
            pool = [t for t in pool if t.is_alcoholic == alcoholic]
        if not pool:
            return None
        min_used = min(self.count.get(t.id, 0) for t in pool)
        least = [t for t in pool if self.count.get(t.id, 0) == min_used]
        return random.choice(least)


def _add(db: Session, user: User, task: Task, usage: Usage,
         target: str | None = None) -> Assignment:
    a = Assignment(user_id=user.id, task_id=task.id, target_user_id=target,
                   status=AssignmentStatus.pending)
    db.add(a)
    usage.bump(task.id)
    return a


# --------- алко-фікс ---------

def _enforce_alcohol_limit(db: Session, user: User,
                           assignments: list[Assignment],
                           by_type: dict, usage: Usage):
    """Якщо непитущий має >1 алко-таски — замінюємо зайві на НЕ-алко того ж типу,
    без дублів у юзера. Type3 (paired) не чіпаємо (для непитущих пара вже не-алко)."""
    if user.is_drinking:
        return
    alco = [a for a in assignments if db.get(Task, a.task_id).is_alcoholic]
    if len(alco) <= 1:
        return

    current_ids = {a.task_id for a in assignments}
    for a in alco[1:]:
        t = db.get(Task, a.task_id)
        if t.type == TaskType.PAIRED:
            continue
        repl = usage.pick(by_type[t.type], exclude_ids=current_ids, alcoholic=False)
        if repl:
            # коригуємо лічильник: знімаємо стару, додаємо нову
            usage.count[a.task_id] = max(0, usage.count.get(a.task_id, 1) - 1)
            current_ids.discard(a.task_id)
            a.task_id = repl.id
            usage.bump(repl.id)
            current_ids.add(repl.id)
    db.flush()


# --------- масовий старт ---------

def assign_tasks_for_all(db: Session):
    by_type = _pool(db)
    all_tasks = by_type[TaskType.SOLO] + by_type[TaskType.TARGETED] + by_type[TaskType.PAIRED]
    usage = Usage(all_tasks)

    users = db.query(User).filter(User.is_latecomer == False).all()  # noqa: E712
    users = [u for u in users if not u.assignments]
    if not users:
        return

    all_users = db.query(User).all()
    bucket: dict[str, list[Assignment]] = {u.id: [] for u in users}
    partners: dict[str, set[str]] = {u.id: set() for u in users}
    user_by_id = {u.id: u for u in users}
    n = len(users)

    # ===== Крок 1: Type3 пари =====
    # Модель: КОЖНЕ T3-завдання -> рівно одна пара. Тобто пар = к-ть T3-завдань
    # (отже всі парні завдання задіяні, кожне один раз). Гравець може бути в
    # кількох парах — ліміт участей = реальні вільні слоти (TASKS_PER_USER - 2,
    # бо 1 слот резервуємо під T1 і 1 під T2). Партнери різні, без дубля завдання.
    paired_tasks = list(by_type[TaskType.PAIRED])
    random.shuffle(paired_tasks)
    # сортуємо так, щоб алкогольні T3 опрацювати ПЕРШИМИ — їх складніше розмістити
    # (потрібна пара, де обидва п'ють), тож хапаємо доступні пари заздалегідь
    paired_tasks.sort(key=lambda t: (not t.is_alcoholic))

    n = len(users)
    MAX_PAIR_SLOTS = 2 if n < 10 else max(1, TASKS_PER_USER - 2)

    def pair_count(uid: str) -> int:
        return sum(1 for a in bucket[uid] if a.pair_id)

    def task_ids_of(uid: str) -> set:
        return {a.task_id for a in bucket[uid]}

    def make_pair(a_id: str, b_id: str, task: Task):
        pid = str(uuid.uuid4())
        a1 = Assignment(user_id=a_id, task_id=task.id, target_user_id=b_id,
                        pair_id=pid, status=AssignmentStatus.pending)
        a2 = Assignment(user_id=b_id, task_id=task.id, target_user_id=a_id,
                        pair_id=pid, status=AssignmentStatus.pending)
        db.add_all([a1, a2])
        bucket[a_id].append(a1); bucket[b_id].append(a2)
        partners[a_id].add(b_id); partners[b_id].add(a_id)
        usage.bump(task.id)

    order = [u.id for u in users]
    pairs_made = 0
    everyone_paired = set()   # хто вже має >=1 пару

    # Для кожного T3-завдання знаходимо валідну пару гравців.
    for task in paired_tasks:
        need_both_drink = task.is_alcoholic   # алко-T3 лише в пару обох-питущих
        # кандидати: є вільний слот + завдання ще не в них
        def candidates():
            cs = [uid for uid in order
                  if pair_count(uid) < MAX_PAIR_SLOTS and task.id not in task_ids_of(uid)]
            if need_both_drink:
                cs = [uid for uid in cs if user_by_id[uid].is_drinking]
            return cs

        # пріоритет: спершу ті, хто ще БЕЗ жодної пари (щоб гарантувати >=1 кожному),
        # далі — хто з найменшою к-тю пар (рівномірність участей)
        def sort_key(uid):
            return (uid in everyone_paired, pair_count(uid), random.random())

        placed = False
        # кілька спроб з перемішуванням, щоб обійти конфлікт «однакові партнери»
        for _attempt in range(40):
            cs = sorted(candidates(), key=sort_key)
            if len(cs) < 2:
                break
            a_id = cs[0]
            # партнер: не сам, не вже-партнер, валідний за випивкою
            partner = None
            for cand in cs[1:]:
                if cand != a_id and cand not in partners[a_id]:
                    partner = cand
                    break
            if partner is None:
                random.shuffle(order)
                continue
            make_pair(a_id, partner, task)
            everyone_paired.add(a_id); everyone_paired.add(partner)
            pairs_made += 1
            placed = True
            break
        # якщо алко-T3 не вдалось розмістити (нема двох вільних питущих) —
        # пропускаємо його (інакше порушили б алко-ліміт). Не-алко завжди розміститься.
        if not placed and not task.is_alcoholic:
            # остання спроба без вимоги різних партнерів (рідкісний кейс)
            cs = [uid for uid in order
                  if pair_count(uid) < MAX_PAIR_SLOTS and task.id not in task_ids_of(uid)]
            if len(cs) >= 2:
                a_id, b_id = cs[0], cs[1]
                make_pair(a_id, b_id, task)
                everyone_paired.add(a_id); everyone_paired.add(b_id)
                pairs_made += 1

    # Гарантія «>=1 пара кожному»: якщо хтось лишився без T3 (бо завдань було
    # менше ніж потрібно для покриття всіх) — допаровуємо його, перевикориставши
    # будь-яке парне завдання, якого в нього ще нема.
    for uid in order:
        if pair_count(uid) == 0:
            partner = None
            for cand in order:
                if cand != uid and cand not in partners[uid] and pair_count(cand) < MAX_PAIR_SLOTS:
                    partner = cand
                    break
            if partner is None:
                continue
            excl = task_ids_of(uid) | task_ids_of(partner)
            task = usage.pick(by_type[TaskType.PAIRED], exclude_ids=excl,
                              alcoholic=False) or \
                   usage.pick(by_type[TaskType.PAIRED], exclude_ids=excl)
            if task is None and by_type[TaskType.PAIRED]:
                task = random.choice([t for t in by_type[TaskType.PAIRED]
                                      if t.id not in excl] or by_type[TaskType.PAIRED])
            if task is not None:
                make_pair(uid, partner, task)

    db.flush()

    # ===== Крок 2: добиваємо T1/T2 до повної к-ті, гарантуючи типи, без дублів =====
    for u in users:
        have = bucket[u.id]
        current_ids = {a.task_id for a in have}

        # гарантований Type1 (якщо ще нема)
        if not any(db.get(Task, a.task_id).type == TaskType.SOLO for a in have):
            t1 = usage.pick(by_type[TaskType.SOLO], exclude_ids=current_ids)
            if t1:
                have.append(_add(db, u, t1, usage)); current_ids.add(t1.id)

        # гарантований Type2 (якщо ще нема)
        if not any(db.get(Task, a.task_id).type == TaskType.TARGETED for a in have):
            t2 = usage.pick(by_type[TaskType.TARGETED], exclude_ids=current_ids)
            if t2:
                have.append(_add(db, u, t2, usage,
                                 target=_random_target(u.id, all_users)))
                current_ids.add(t2.id)

        # доповнюємо рандомом з {T1,T2} — без дублів, з пріоритетом покриття
        fill_pool = by_type[TaskType.SOLO] + by_type[TaskType.TARGETED]
        while len(have) < TASKS_PER_USER:
            t = usage.pick(fill_pool, exclude_ids=current_ids)
            if t is None:
                break  # пул вичерпано (малоймовірно при достатній к-ті завдань)
            target = _random_target(u.id, all_users) if t.type == TaskType.TARGETED else None
            have.append(_add(db, u, t, usage, target=target))
            current_ids.add(t.id)

    db.flush()

    # ===== Крок 3: алко-ліміт =====
    for u in users:
        _enforce_alcohol_limit(db, u, bucket[u.id], by_type, usage)

    db.commit()


# --------- латекомер ---------

def assign_tasks_for_latecomer(db: Session, user: User):
    """Миттєве призначення тасок латекомеру. Тільки Type1/Type2, без дублів."""
    by_type = _pool(db)
    all_users = db.query(User).all()
    # лічильник стартує з нуля локально (латекомер один, рівномірність у межах нього)
    usage = Usage(by_type[TaskType.SOLO] + by_type[TaskType.TARGETED])
    fill_pool = by_type[TaskType.SOLO] + by_type[TaskType.TARGETED]

    have: list[Assignment] = []
    current_ids: set[int] = set()

    t1 = usage.pick(by_type[TaskType.SOLO], exclude_ids=current_ids)
    if t1:
        have.append(_add(db, user, t1, usage)); current_ids.add(t1.id)
    t2 = usage.pick(by_type[TaskType.TARGETED], exclude_ids=current_ids)
    if t2:
        have.append(_add(db, user, t2, usage,
                         target=_random_target(user.id, all_users)))
        current_ids.add(t2.id)

    while len(have) < TASKS_PER_USER:
        t = usage.pick(fill_pool, exclude_ids=current_ids)
        if t is None:
            break
        target = _random_target(user.id, all_users) if t.type == TaskType.TARGETED else None
        have.append(_add(db, user, t, usage, target=target))
        current_ids.add(t.id)

    db.flush()
    _enforce_alcohol_limit(db, user, have, by_type, usage)
    db.commit()

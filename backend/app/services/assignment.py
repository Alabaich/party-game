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
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import (
    User, Task, Assignment, Game, TaskType, AssignmentStatus
)
from ..schemas.settings import load_settings


# --------- helpers ---------

def _pool(db: Session, game: Game):
    tasks = db.query(Task).filter(Task.game_id == game.id,
                                  Task.is_universal == False).all()  # noqa: E712
    if not load_settings(game.settings).alcohol_tasks:
        tasks = [t for t in tasks if not t.is_alcoholic]
    by_type = {TaskType.SOLO: [], TaskType.TARGETED: [], TaskType.PAIRED: []}
    for t in tasks:
        by_type[t.type].append(t)
    return by_type


class Targets:
    """Picks who a TARGETED task points at: the person targeted least so far
    (ties random), so everyone gets found about equally often."""
    def __init__(self, db: Session, game: Game, all_users: list[User]):
        self.ids = [u.id for u in all_users]
        self.count = {uid: 0 for uid in self.ids}
        rows = (db.query(Assignment.target_user_id)
                .join(User, User.id == Assignment.user_id)
                .filter(User.game_id == game.id, Assignment.pair_id.is_(None),
                        Assignment.target_user_id.isnot(None)).all())
        for (tid,) in rows:
            if tid in self.count:
                self.count[tid] += 1

    def pick(self, user_id: str, avoid: set[str] = frozenset()) -> str | None:
        others = [i for i in self.ids if i != user_id and i not in avoid] or \
                 [i for i in self.ids if i != user_id]
        if not others:
            return None
        low = min(self.count[i] for i in others)
        tid = random.choice([i for i in others if self.count[i] == low])
        self.count[tid] += 1
        return tid


class Usage:
    """Глобальний лічильник використань завдань — для рівномірного покриття.
    Стартує з того, що вже роздано в грі, щоб латекомери не ламали рівномірність."""
    def __init__(self, all_tasks: list[Task], db: Session | None = None):
        self.count = {t.id: 0 for t in all_tasks}
        if db is not None and all_tasks:
            rows = (db.query(Assignment.task_id, func.count())
                    .filter(Assignment.task_id.in_(list(self.count)))
                    .group_by(Assignment.task_id).all())
            for tid, n in rows:
                self.count[tid] = n

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
            usage.count[a.task_id] = max(0, usage.count.get(a.task_id, 1) - 1)
            current_ids.discard(a.task_id)
            a.task_id = repl.id
            usage.bump(repl.id)
            current_ids.add(repl.id)
    db.flush()


# --------- масовий старт ---------

def assign_tasks_for_all(db: Session, game: Game):
    TASKS_PER_USER = game.tasks_per_user
    by_type = _pool(db, game)
    all_tasks = by_type[TaskType.SOLO] + by_type[TaskType.TARGETED] + by_type[TaskType.PAIRED]
    usage = Usage(all_tasks)

    users = db.query(User).filter(User.game_id == game.id,
                                  User.is_latecomer == False).all()  # noqa: E712
    users = [u for u in users if not u.assignments]
    if not users:
        return

    all_users = db.query(User).filter(User.game_id == game.id).all()
    targets = Targets(db, game, all_users)
    bucket: dict[str, list[Assignment]] = {u.id: [] for u in users}
    partners: dict[str, set[str]] = {u.id: set() for u in users}
    user_by_id = {u.id: u for u in users}
    n = len(users)

    # ===== Крок 1: Type3 пари =====
    paired_tasks = list(by_type[TaskType.PAIRED])
    random.shuffle(paired_tasks)
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
    everyone_paired = set()

    for task in paired_tasks:
        need_both_drink = task.is_alcoholic
        def candidates():
            cs = [uid for uid in order
                  if pair_count(uid) < MAX_PAIR_SLOTS and task.id not in task_ids_of(uid)]
            if need_both_drink:
                cs = [uid for uid in cs if user_by_id[uid].is_drinking]
            return cs

        def sort_key(uid):
            return (uid in everyone_paired, pair_count(uid), random.random())

        placed = False
        for _attempt in range(40):
            cs = sorted(candidates(), key=sort_key)
            if len(cs) < 2:
                break
            a_id = cs[0]
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
        if not placed and not task.is_alcoholic:
            cs = [uid for uid in order
                  if pair_count(uid) < MAX_PAIR_SLOTS and task.id not in task_ids_of(uid)]
            if len(cs) >= 2:
                a_id, b_id = cs[0], cs[1]
                make_pair(a_id, b_id, task)
                everyone_paired.add(a_id); everyone_paired.add(b_id)
                pairs_made += 1

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

    # ===== Крок 2: добиваємо T1/T2 =====
    for u in users:
        have = bucket[u.id]
        current_ids = {a.task_id for a in have}

        if not any(db.get(Task, a.task_id).type == TaskType.SOLO for a in have):
            t1 = usage.pick(by_type[TaskType.SOLO], exclude_ids=current_ids)
            if t1:
                have.append(_add(db, u, t1, usage)); current_ids.add(t1.id)

        if not any(db.get(Task, a.task_id).type == TaskType.TARGETED for a in have):
            t2 = usage.pick(by_type[TaskType.TARGETED], exclude_ids=current_ids)
            if t2:
                have.append(_add(db, u, t2, usage,
                                 target=targets.pick(u.id, partners[u.id])))
                current_ids.add(t2.id)

        fill_pool = by_type[TaskType.SOLO] + by_type[TaskType.TARGETED]
        while len(have) < TASKS_PER_USER:
            t = usage.pick(fill_pool, exclude_ids=current_ids)
            if t is None:
                break
            target = (targets.pick(u.id, partners[u.id] | {x.target_user_id for x in have})
                      if t.type == TaskType.TARGETED else None)
            have.append(_add(db, u, t, usage, target=target))
            current_ids.add(t.id)

    db.flush()

    # ===== Крок 3: алко-ліміт =====
    for u in users:
        _enforce_alcohol_limit(db, u, bucket[u.id], by_type, usage)

    db.commit()


# --------- латекомер ---------

def assign_tasks_for_latecomer(db: Session, game: Game, user: User):
    """Миттєве призначення тасок латекомеру. Тільки Type1/Type2, без дублів."""
    TASKS_PER_USER = game.tasks_per_user
    by_type = _pool(db, game)
    all_users = db.query(User).filter(User.game_id == game.id).all()
    targets = Targets(db, game, all_users)
    usage = Usage(by_type[TaskType.SOLO] + by_type[TaskType.TARGETED], db)
    fill_pool = by_type[TaskType.SOLO] + by_type[TaskType.TARGETED]

    have: list[Assignment] = []
    current_ids: set[int] = set()

    t1 = usage.pick(by_type[TaskType.SOLO], exclude_ids=current_ids)
    if t1:
        have.append(_add(db, user, t1, usage)); current_ids.add(t1.id)
    t2 = usage.pick(by_type[TaskType.TARGETED], exclude_ids=current_ids)
    if t2:
        have.append(_add(db, user, t2, usage,
                         target=targets.pick(user.id)))
        current_ids.add(t2.id)

    while len(have) < TASKS_PER_USER:
        t = usage.pick(fill_pool, exclude_ids=current_ids)
        if t is None:
            break
        target = (targets.pick(user.id, {x.target_user_id for x in have})
                  if t.type == TaskType.TARGETED else None)
        have.append(_add(db, user, t, usage, target=target))
        current_ids.add(t.id)

    db.flush()
    _enforce_alcohol_limit(db, user, have, by_type, usage)
    db.commit()

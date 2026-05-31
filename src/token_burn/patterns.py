from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from .classifier import Activity, classify
from .types import Turn


def _normalize_cmd(cmd: str) -> str:
    parts = cmd.split()
    if not parts:
        return ''
    return f'{parts[0]} {parts[1]}' if len(parts) >= 2 else parts[0]


_STOPWORDS = frozenset({
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
    'should', 'may', 'might', 'must', 'can', 'could', 'to', 'of', 'in',
    'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 'into',
    'this', 'that', 'these', 'those', 'i', 'you', 'me', 'my', 'your',
    'we', 'our', 'they', 'them', 'their', 'it', 'its', 'and', 'or',
    'but', 'if', 'as', 'not', 'no', 'so', 'also', 'just', 'please',
    'let', 'get', 'make', 'want', 'need', 'help', 'now', 'what', 'how',
    'when', 'where', 'why', 'which', 'who', 'then', 'than', 'very',
    'all', 'each', 'some', 'any', 'more', 'here', 'there',
})

_FILLER_LEAD = frozenset({
    'please', 'can', 'could', 'would', 'should', 'i', 'we', 'you',
    'let', 'help', 'now', 'just', 'go', 'ok', 'okay', 'yeah', 'yes',
})


_PATH_TOKEN_RE = re.compile(r'\S*/\S+')  # any token containing /


def _normalize_prompt(text: str) -> str:
    text = _PATH_TOKEN_RE.sub(' ', text)   # strip path tokens before lowering
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def repeated_prompts(
    turns: Iterable[Turn],
    min_count: int = 2,
    min_words: int = 3,
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for turn in turns:
        text = turn.user_text.strip()
        if not text:
            continue
        norm = _normalize_prompt(text)
        if len(norm.split()) >= min_words:
            counts[norm] += 1
    return [(t, c) for t, c in counts.most_common() if c >= min_count]


def prompt_action_verbs(
    turns: Iterable[Turn],
    top_n: int = 15,
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for turn in turns:
        text = turn.user_text.strip()
        if not text:
            continue
        words = _normalize_prompt(text).split()
        for word in words:
            if word not in _FILLER_LEAD and word not in _STOPWORDS and len(word) > 2:
                counts[word] += 1
                break
    return counts.most_common(top_n)


def prompt_bigrams(
    turns: Iterable[Turn],
    top_n: int = 20,
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for turn in turns:
        text = turn.user_text.strip()
        if not text:
            continue
        words = [
            w for w in _normalize_prompt(text).split()
            if w not in _STOPWORDS and len(w) > 2
        ]
        for i in range(len(words) - 1):
            counts[f'{words[i]} {words[i + 1]}'] += 1
    return counts.most_common(top_n)


@dataclass
class ShellPattern:
    command: str
    count: int
    projects: list[str]
    examples: list[str]


@dataclass
class ActivityTransition:
    from_activity: str
    to_activity: str
    count: int
    total_from: int

    @property
    def pct(self) -> float:
        return self.count / self.total_from if self.total_from else 0.0


@dataclass
class RampStats:
    mean: float
    p90: float
    session_count: int


@dataclass
class GrowthSignal:
    kind: str
    description: str
    value: float
    project: str = ''


@dataclass
class ModelActivityStats:
    model: str
    total_turns: int
    total_tokens: int
    by_activity: dict[str, int]

    @property
    def avg_tokens(self) -> float:
        return self.total_tokens / self.total_turns if self.total_turns else 0.0

    def top_activities(self, n: int = 3) -> list[tuple[str, float]]:
        total = sum(self.by_activity.values()) or 1
        return sorted(
            [(a, c / total) for a, c in self.by_activity.items()],
            key=lambda x: -x[1],
        )[:n]


@dataclass
class ModelSignal:
    model: str
    kind: str
    description: str


_CHEAP_ACTIVITIES = frozenset({'Conversation', 'Git Ops', 'General', 'Delegation'})


def shell_automation_candidates(
    turns: Iterable[Turn],
    min_count: int = 3,
) -> list[ShellPattern]:
    norm_counts: Counter[str] = Counter()
    norm_projects: defaultdict[str, set[str]] = defaultdict(set)
    norm_examples: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for turn in turns:
        for cmd in turn.bash_inputs:
            norm = _normalize_cmd(cmd)
            if not norm:
                continue
            norm_counts[norm] += 1
            norm_projects[norm].add(turn.project)
            norm_examples[norm][cmd] += 1

    return [
        ShellPattern(
            command=norm,
            count=count,
            projects=sorted(norm_projects[norm]),
            examples=[ex for ex, _ in norm_examples[norm].most_common(3)],
        )
        for norm, count in norm_counts.most_common()
        if count >= min_count
    ]


def file_edit_frequency(
    turns: Iterable[Turn],
    top_n: int = 20,
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for turn in turns:
        for f in turn.edited_files:
            counts[f] += 1
    return counts.most_common(top_n)


def activity_transitions(
    sessions: Iterable[list[Turn]],
    top_n: int = 15,
) -> list[ActivityTransition]:
    bigrams: Counter[tuple[str, str]] = Counter()
    from_counts: Counter[str] = Counter()

    for session in sessions:
        activities = [classify(t, t.bash_inputs).value for t in session]
        for i in range(len(activities) - 1):
            a, b = activities[i], activities[i + 1]
            bigrams[(a, b)] += 1
            from_counts[a] += 1

    return [
        ActivityTransition(
            from_activity=a,
            to_activity=b,
            count=count,
            total_from=from_counts[a],
        )
        for (a, b), count in bigrams.most_common(top_n + 20)
        if a != b
    ][:top_n]


def session_ramp_stats(sessions: Iterable[list[Turn]]) -> RampStats:
    ramps: list[int] = []
    session_count = 0
    for session in sessions:
        session_count += 1
        for i, turn in enumerate(session):
            if 'Edit' in turn.tools_used or 'Write' in turn.tools_used:
                ramps.append(i)
                break

    if not ramps:
        return RampStats(mean=0.0, p90=0.0, session_count=session_count)

    mean = statistics.mean(ramps)
    p90_idx = min(int(len(ramps) * 0.9), len(ramps) - 1)
    p90 = float(sorted(ramps)[p90_idx])
    return RampStats(mean=mean, p90=p90, session_count=session_count)


def growth_signals(turns: Iterable[Turn]) -> list[GrowthSignal]:
    by_project: defaultdict[str, list[Turn]] = defaultdict(list)
    for turn in turns:
        by_project[turn.project].append(turn)

    signals: list[GrowthSignal] = []
    for project, project_turns in by_project.items():
        activities = [classify(t, t.bash_inputs).value for t in project_turns]
        total = len(activities)
        if total < 5:
            continue

        debug_count = activities.count(Activity.DEBUGGING.value)
        test_count = activities.count(Activity.TESTING.value)
        convo_count = activities.count(Activity.CONVERSATION.value)

        if test_count == 0 and debug_count >= 5:
            signals.append(GrowthSignal(
                kind='no_tests',
                description=f'{debug_count} debug turns, 0 test turns',
                value=float(debug_count),
                project=project,
            ))
        elif test_count > 0 and debug_count / test_count > 3.0:
            ratio = debug_count / test_count
            signals.append(GrowthSignal(
                kind='debug_test_ratio',
                description=f'{debug_count} debug, {test_count} test turns ({ratio:.1f}x)',
                value=ratio,
                project=project,
            ))

        convo_ratio = convo_count / total
        if convo_ratio > 0.40:
            signals.append(GrowthSignal(
                kind='high_conversation',
                description=f'{convo_ratio:.0%} conversation ({convo_count}/{total} turns)',
                value=convo_ratio,
                project=project,
            ))

    return sorted(signals, key=lambda s: s.value, reverse=True)


def model_activity_breakdown(turns: Iterable[Turn]) -> list[ModelActivityStats]:
    by_model: defaultdict[str, list[Turn]] = defaultdict(list)
    for turn in turns:
        by_model[turn.model].append(turn)

    result = []
    for model, model_turns in by_model.items():
        by_activity: Counter[str] = Counter()
        total_tokens = 0
        for t in model_turns:
            by_activity[classify(t, t.bash_inputs).value] += 1
            total_tokens += t.usage.total
        result.append(ModelActivityStats(
            model=model,
            total_turns=len(model_turns),
            total_tokens=total_tokens,
            by_activity=dict(by_activity),
        ))

    return sorted(result, key=lambda s: -s.total_tokens)


def project_model_breakdown(turns: Iterable[Turn]) -> dict[str, list[ModelActivityStats]]:
    by_project: defaultdict[str, list[Turn]] = defaultdict(list)
    for turn in turns:
        by_project[turn.project].append(turn)
    return {
        proj: model_activity_breakdown(proj_turns)
        for proj, proj_turns in sorted(by_project.items())
    }


def model_efficiency_signals(stats: list[ModelActivityStats]) -> list[ModelSignal]:
    signals = []
    for s in stats:
        if s.total_turns < 5:
            continue
        cheap_turns = sum(c for a, c in s.by_activity.items() if a in _CHEAP_ACTIVITIES)
        cheap_pct = cheap_turns / s.total_turns
        if cheap_pct > 0.30:
            cheap_names = ', '.join(
                sorted(a for a in _CHEAP_ACTIVITIES if s.by_activity.get(a, 0) > 0)
            )
            signals.append(ModelSignal(
                model=s.model,
                kind='cheap activity overhead',
                description=f'{cheap_pct:.0%} of turns in low-value activities ({cheap_names})',
            ))
    return signals

from __future__ import annotations

import re
from enum import Enum

from .types import Turn

_EDIT_TOOLS = {'Edit', 'Write', 'apply_patch', 'write_file', 'patch_apply', 'NotebookEdit'}
_EXPLORE_TOOLS = {'Read', 'Grep', 'Glob', 'WebSearch', 'WebFetch', 'read_file', 'search_files'}
_PLAN_TOOLS = {'EnterPlanMode', 'TaskCreate'}
_DELEGATE_TOOLS = {'Agent', 'Task'}


class Activity(str, Enum):
    CODING = 'Coding'
    DEBUGGING = 'Debugging'
    FEATURE_DEV = 'Feature Dev'
    REFACTORING = 'Refactoring'
    TESTING = 'Testing'
    EXPLORATION = 'Exploration'
    PLANNING = 'Planning'
    DELEGATION = 'Delegation'
    GIT_OPS = 'Git Ops'
    BUILD_DEPLOY = 'Build/Deploy'
    BRAINSTORMING = 'Brainstorming'
    CONVERSATION = 'Conversation'
    GENERAL = 'General'


_DEBUG_KW = re.compile(r'\b(error|fix|bug|exception|traceback|fail|crash|broken)\b', re.I)
_FEATURE_KW = re.compile(r'\b(add|create|implement|build|new feature)\b', re.I)
_REFACTOR_KW = re.compile(r'\b(refactor|rename|simplify|restructure|clean up)\b', re.I)
_BRAINSTORM_KW = re.compile(r'\b(brainstorm|what if|design|idea|approach|think about)\b', re.I)

_TEST_CMDS = re.compile(r'\b(pytest|vitest|jest|go test|npm test|yarn test|pnpm test)\b')
_GIT_CMDS = re.compile(r'\bgit (push|commit|merge|rebase|cherry-pick)\b')
_BUILD_CMDS = re.compile(r'\b(npm (run )?build|docker|pm2|pip install|uv (pip )?install|make|cargo build)\b')


def _has_edit(tools: list[str]) -> bool:
    return bool(set(tools) & _EDIT_TOOLS)


def _bash_cmds(tools: list[str], turn_bash_inputs: list[str]) -> str:
    return ' '.join(turn_bash_inputs)


def classify(turn: Turn, bash_inputs: list[str] | None = None) -> Activity:
    tools = set(turn.tools_used)
    bash_text = ' '.join(bash_inputs or [])
    text = (turn.user_text or '').lower()
    has_edit = bool(tools & _EDIT_TOOLS)

    if 'Skill' in tools:
        return Activity.GENERAL
    if tools & _DELEGATE_TOOLS:
        return Activity.DELEGATION
    if tools & _PLAN_TOOLS:
        return Activity.PLANNING
    if _TEST_CMDS.search(bash_text):
        return Activity.TESTING
    if _GIT_CMDS.search(bash_text):
        return Activity.GIT_OPS
    if _BUILD_CMDS.search(bash_text):
        return Activity.BUILD_DEPLOY
    if has_edit and _REFACTOR_KW.search(text):
        return Activity.REFACTORING
    if has_edit and _FEATURE_KW.search(text):
        return Activity.FEATURE_DEV
    if has_edit and _DEBUG_KW.search(text):
        return Activity.DEBUGGING
    if has_edit:
        return Activity.CODING
    if tools <= _EXPLORE_TOOLS and tools:
        return Activity.EXPLORATION
    if _BRAINSTORM_KW.search(text) and not has_edit:
        return Activity.BRAINSTORMING
    if not tools:
        return Activity.CONVERSATION
    return Activity.GENERAL

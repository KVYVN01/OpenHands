"""Tests for the host-side skills bridge.

The bridge loads skills from host paths (``OpenHands/skills/`` and the user's
home dir) and merges them into the agent context.  Without it, host-side
skills appear in the Settings UI list but never reach the agent-server.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.app_server.app_conversation import app_conversation_service_base
from openhands.app_server.app_conversation.app_conversation_service_base import (
    AppConversationServiceBase,
    _global_skills_dir,
    _load_host_side_skills,
)
from openhands.sdk import Agent
from openhands.sdk.llm import LLM
from openhands.sdk.skills import KeywordTrigger, Skill

SKILL_GLOBAL = """---
name: bridge-global-skill
type: knowledge
triggers:
  - bridge-global
---

global content
"""

SKILL_USER = """---
name: bridge-user-skill
type: knowledge
triggers:
  - bridge-user
---

user content
"""

SKILL_OVERRIDE = """---
name: bridge-global-skill
type: knowledge
triggers:
  - user-override
---

user override content
"""


def _write_skill(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding='utf-8')


def test_global_skills_dir_resolves_to_repo_root() -> None:
    """The global dir must be the ``OpenHands/skills`` folder shipped with the repo."""
    global_dir = _global_skills_dir()
    assert global_dir.name == 'skills'
    # Sanity: the directory exists in this checkout (it ships ``github.md`` etc.)
    assert global_dir.is_dir(), f'Expected {global_dir} to exist in the repo checkout'


def test_load_host_side_skills_returns_global_and_user_skills(
    tmp_path: Path,
) -> None:
    """Global + user dirs are both loaded and merged by name."""
    global_dir = tmp_path / 'skills'
    user_home = tmp_path / 'home'
    user_skills_dir = user_home / '.openhands' / 'skills'

    _write_skill(global_dir / 'global.md', SKILL_GLOBAL)
    _write_skill(user_skills_dir / 'user.md', SKILL_USER)

    with (
        patch.object(
            app_conversation_service_base,
            '_global_skills_dir',
            return_value=global_dir,
        ),
        patch.object(Path, 'home', return_value=user_home),
    ):
        skills = _load_host_side_skills()

    by_name = {s.name: s for s in skills}
    assert 'bridge-global-skill' in by_name, list(by_name)
    assert 'bridge-user-skill' in by_name, list(by_name)


def test_load_host_side_skills_user_overrides_global(tmp_path: Path) -> None:
    """If a user skill shares a name with a global one, the user copy wins."""
    global_dir = tmp_path / 'skills'
    user_home = tmp_path / 'home'
    user_skills_dir = user_home / '.openhands' / 'skills'

    _write_skill(global_dir / 'global.md', SKILL_GLOBAL)
    _write_skill(user_skills_dir / 'override.md', SKILL_OVERRIDE)

    with (
        patch.object(
            app_conversation_service_base,
            '_global_skills_dir',
            return_value=global_dir,
        ),
        patch.object(Path, 'home', return_value=user_home),
    ):
        skills = _load_host_side_skills()

    by_name = {s.name: s for s in skills}
    skill = by_name['bridge-global-skill']
    assert isinstance(skill, Skill)
    assert 'user override content' in skill.content


def test_load_host_side_skills_handles_missing_dirs(tmp_path: Path) -> None:
    """Missing host paths are not fatal — we return whatever is available."""
    with (
        patch.object(
            app_conversation_service_base,
            '_global_skills_dir',
            return_value=tmp_path / 'does-not-exist',
        ),
        patch.object(Path, 'home', return_value=tmp_path / 'no-home'),
    ):
        skills = _load_host_side_skills()

    assert skills == []


@pytest.mark.parametrize(
    'legacy_subdir',
    ['microagents', 'skills'],
)
def test_load_host_side_skills_legacy_user_paths(
    tmp_path: Path, legacy_subdir: str
) -> None:
    """Both legacy ``.openhands/microagents`` and modern ``.openhands/skills`` work."""
    user_home = tmp_path / 'home'
    _write_skill(user_home / '.openhands' / legacy_subdir / 'legacy.md', SKILL_USER)

    with (
        patch.object(
            app_conversation_service_base,
            '_global_skills_dir',
            return_value=tmp_path / 'no-global',
        ),
        patch.object(Path, 'home', return_value=user_home),
    ):
        skills = _load_host_side_skills()

    assert any(s.name == 'bridge-user-skill' for s in skills), [s.name for s in skills]


def _make_agent_with_no_context() -> Agent:
    """Construct a minimal Agent suitable for ``_create_agent_with_skills``."""
    return Agent(llm=LLM(usage_id='test', model='test-model'))


@pytest.mark.asyncio
async def test_load_skills_and_update_agent_includes_host_skills(
    tmp_path: Path,
) -> None:
    """End-to-end: host-side skills are merged into the agent context."""
    # Arrange: build a service mock so we don't need to fully construct one.
    mock_cls = type('AppConversationServiceMock', (MagicMock,), {})
    AppConversationServiceBase.register(mock_cls)
    service = mock_cls()

    agent_server_skill = Skill(
        name='agent-server-only',
        content='from agent server',
        trigger=KeywordTrigger(keywords=['srv']),
    )
    service.load_and_merge_all_skills = AsyncMock(return_value=[agent_server_skill])
    service._merge_skills = AppConversationServiceBase._merge_skills.__get__(service)
    service._create_agent_with_skills = (
        AppConversationServiceBase._create_agent_with_skills.__get__(service)
    )

    host_skill = Skill(
        name='host-only-skill',
        content='from host',
        trigger=KeywordTrigger(keywords=['host']),
    )

    # Wire up a fake remote workspace just enough for ``_load_skills_and_update_agent``
    remote_workspace = MagicMock()
    remote_workspace.host = 'http://agent-server'
    sandbox = MagicMock()

    agent = _make_agent_with_no_context()

    with patch.object(
        app_conversation_service_base,
        '_load_host_side_skills',
        return_value=[host_skill],
    ):
        updated_agent = await AppConversationServiceBase._load_skills_and_update_agent(
            service,
            sandbox,
            agent,
            remote_workspace,
            selected_repository=None,
            project_dir='/workspace',
            disabled_skills=None,
        )

    # Act + Assert: both skills are in the agent's context.
    assert updated_agent.agent_context is not None
    names = {s.name for s in updated_agent.agent_context.skills}
    assert names == {'agent-server-only', 'host-only-skill'}


@pytest.mark.asyncio
async def test_load_skills_and_update_agent_disables_host_skill(
    tmp_path: Path,
) -> None:
    """Disabling a host-side skill by name actually keeps it out of the agent."""
    mock_cls = type('AppConversationServiceMock', (MagicMock,), {})
    AppConversationServiceBase.register(mock_cls)
    service = mock_cls()

    service.load_and_merge_all_skills = AsyncMock(return_value=[])
    service._merge_skills = AppConversationServiceBase._merge_skills.__get__(service)
    service._create_agent_with_skills = (
        AppConversationServiceBase._create_agent_with_skills.__get__(service)
    )

    host_skill = Skill(name='banned-skill', content='x', trigger=None)

    with patch.object(
        app_conversation_service_base,
        '_load_host_side_skills',
        return_value=[host_skill],
    ):
        updated_agent = await AppConversationServiceBase._load_skills_and_update_agent(
            service,
            MagicMock(),
            _make_agent_with_no_context(),
            MagicMock(host='http://agent-server'),
            selected_repository=None,
            project_dir='/workspace',
            disabled_skills=['banned-skill'],
        )

    if updated_agent.agent_context is None:
        names = set()
    else:
        names = {s.name for s in updated_agent.agent_context.skills}
    assert 'banned-skill' not in names

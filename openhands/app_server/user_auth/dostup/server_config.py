"""Server config that wires the application server into DOSTUP_CRS auth mode."""

from __future__ import annotations

from openhands.app_server.server_config.server_config import ServerConfig
from openhands.app_server.types import AppMode


class DostupServerConfig(ServerConfig):
    """Multi-user variant of :class:`ServerConfig`.

    Activate by setting

        OPENHANDS_CONFIG_CLS=openhands.app_server.user_auth.dostup.server_config.DostupServerConfig

    which causes:

    * the user-auth implementation to resolve to ``DostupUserAuth``
      (JWT cookie / Bearer header → ``user_id``),
    * the frontend to receive ``app_mode = "dostup"`` so the login UI
      switches to the local email/password form,
    * settings, secrets and conversation storage to be keyed per user id
      because of the existing ``UserAuth.get_user_id()`` contract.
    """

    app_mode = AppMode.DOSTUP  # type: ignore[attr-defined]
    user_auth_class: str = (
        'openhands.app_server.user_auth.dostup.dostup_user_auth.DostupUserAuth'
    )

    def verify_config(self) -> None:
        # The base implementation rejects any explicit ``OPENHANDS_CONFIG_CLS``
        # because *it* is the default. Subclasses are expected to override this
        # to acknowledge that they are the intended config target.
        return None

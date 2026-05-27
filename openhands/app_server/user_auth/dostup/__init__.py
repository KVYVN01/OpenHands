"""Multi-user auth backend for the DOSTUP_CRS deployment of the application server.

This package adds a lightweight email/password + JWT auth layer on top of
the existing :class:`openhands.app_server.user_auth.user_auth.UserAuth`
abstraction. It is opt-in: import nothing from here in single-tenant
deployments, and they continue to use ``DefaultUserAuth``.

Enable it by pointing ``OPENHANDS_CONFIG_CLS`` at
``openhands.app_server.user_auth.dostup.server_config.DostupServerConfig``.
"""

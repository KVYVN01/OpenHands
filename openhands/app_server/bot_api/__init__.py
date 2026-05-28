"""Bot-facing API for DOSTUP_CRS.

This module provides a stable, narrowly-scoped REST surface intended for
bots, automation scripts, and other programmatic clients. It is layered
on top of (and re-uses) the existing app-server services and shares the
same authentication identities as the browser UI — the bot just presents
an API-key token instead of a session cookie.

See ``docs/dostup_crs/API.md`` for the full reference.
"""

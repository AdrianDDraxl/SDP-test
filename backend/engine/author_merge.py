"""Author identity canonicalization using .mailmap and manual groups."""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any

_EMAIL_RE = re.compile(r"<([^<>]+)>")


def _key(name: str, email: str) -> tuple[str, str]:
    return name.strip().casefold(), email.strip().casefold()


class AuthorMerger:
    """Resolve raw Git author identities to canonical identities."""

    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path)
        self._mailmap_exact: dict[tuple[str, str], tuple[str | None, str]] = {}
        self._mailmap_email: dict[str, tuple[str | None, str]] = {}
        self._groups: list[list[dict[str, str]]] = []
        self._manual_aliases: dict[tuple[str, str], tuple[str, str]] = {}
        self._parse_mailmap()

    def _parse_mailmap(self) -> None:
        mailmap = self.repo_path / ".mailmap"
        if not mailmap.is_file():
            return

        for raw_line in mailmap.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            matches = list(_EMAIL_RE.finditer(line))
            if not matches:
                continue

            canonical_email = matches[0].group(1).strip()
            canonical_name = line[: matches[0].start()].strip() or None

            if len(matches) == 1:
                self._mailmap_email[canonical_email.casefold()] = (
                    canonical_name,
                    canonical_email,
                )
                continue

            alias_email = matches[1].group(1).strip()
            alias_name = line[matches[0].end() : matches[1].start()].strip()
            target = (canonical_name, canonical_email)
            if alias_name:
                self._mailmap_exact[_key(alias_name, alias_email)] = target
            else:
                self._mailmap_email[alias_email.casefold()] = target

    def _resolve_mailmap(self, name: str, email: str) -> tuple[str, str]:
        target = self._mailmap_exact.get(_key(name, email))
        if target is None:
            target = self._mailmap_email.get(email.strip().casefold())
        if target is None:
            return name, email
        canonical_name, canonical_email = target
        return canonical_name or name, canonical_email

    def resolve(self, name: str, email: str) -> tuple[str, str]:
        """Resolve an identity through .mailmap, then manual merge groups."""
        mapped_name, mapped_email = self._resolve_mailmap(name.strip(), email.strip())
        return self._manual_aliases.get(
            _key(mapped_name, mapped_email),
            self._manual_aliases.get(_key(name, email), (mapped_name, mapped_email)),
        )

    def set_groups(self, groups: list[list[dict[str, Any]]]) -> None:
        """Replace manual groups, using each group's first identity as canonical."""
        if not isinstance(groups, list):
            raise ValueError("author groups must be a list")

        validated: list[list[dict[str, str]]] = []
        aliases: dict[tuple[str, str], tuple[str, str]] = {}
        for group in groups:
            if not isinstance(group, list) or not group:
                raise ValueError("each author group must be a non-empty list")

            clean_group: list[dict[str, str]] = []
            for identity in group:
                if not isinstance(identity, dict):
                    raise ValueError("each author identity must be an object")
                name = identity.get("name")
                email = identity.get("email")
                if not isinstance(name, str) or not isinstance(email, str):
                    raise ValueError("each author identity requires string name and email")
                name, email = name.strip(), email.strip()
                if not email:
                    raise ValueError("author email cannot be empty")
                clean_group.append({"name": name, "email": email})

            canonical = (clean_group[0]["name"], clean_group[0]["email"])
            for identity in clean_group:
                raw = (identity["name"], identity["email"])
                aliases[_key(*raw)] = canonical
                aliases[_key(*self._resolve_mailmap(*raw))] = canonical
            validated.append(clean_group)

        self._groups = validated
        self._manual_aliases = aliases

    def get_groups(self) -> list[list[dict[str, str]]]:
        """Return a defensive copy of the configured manual groups."""
        return deepcopy(self._groups)

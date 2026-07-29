"""Signature image metadata."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4


class SignatureOwner(StrEnum):
    GUARDIAN_1 = "guardian_1"
    GUARDIAN_2 = "guardian_2"


@dataclass(frozen=True, slots=True)
class SignatureAsset:
    id: str
    name: str
    owner: SignatureOwner
    filename: str
    width: int
    height: int

    @classmethod
    def create(cls, name: str, owner: SignatureOwner, width: int, height: int) -> SignatureAsset:
        asset_id = str(uuid4())
        return cls(asset_id, name, owner, f"{asset_id}.png", width, height)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner.value,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignatureAsset:
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            owner=SignatureOwner(payload["owner"]),
            filename=str(payload["filename"]),
            width=int(payload["width"]),
            height=int(payload["height"]),
        )

# MtpltGraph/config_models/_coerce.py

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, TypeVar


T = TypeVar("T")

def coerce_configs(**items):
    output = {}

    for name, item in items.items():
        value, cls = item
        output[name] = config_to_dict(
            coerce_config(value, cls),
            drop_none=True,
        )

    return output

def coerce_config(value: Any, cls: type[T]) -> T:
    if value is None:
        return cls()

    if isinstance(value, cls):
        return value

    if isinstance(value, dict):
        allowed = {field.name for field in fields(cls)}
        unknown = set(value) - allowed

        if unknown:
            raise TypeError(
                f"Unknown keys for {cls.__name__}: {sorted(unknown)}. "
                f"Allowed keys are: {sorted(allowed)}"
            )

        return cls(**value)

    raise TypeError(
        f"Expected None, dict, or {cls.__name__}; "
        f"got {type(value).__name__}."
    )


def config_to_dict(value: Any, *, drop_none: bool = False) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        out = value.copy()

    elif is_dataclass(value):
        out = {
            field.name: getattr(value, field.name)
            for field in fields(value)
        }

    else:
        raise TypeError(
            f"Expected dict or dataclass config; got {type(value).__name__}."
        )

    if drop_none:
        out = {
            key: val
            for key, val in out.items()
            if val is not None
        }

    return out


def clean_none(config: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in config.items()
        if value is not None
    }
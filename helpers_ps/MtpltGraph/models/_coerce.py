from __future__ import annotations

from dataclasses import asdict
from dataclasses import fields
from dataclasses import is_dataclass

from typing import Any
from typing import TypeVar

T = TypeVar("T")


# ============================================================
# Basic helpers
# ============================================================

def clean_none(
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove keys whose value is None.

    Useful before sending kwargs into matplotlib.
    """

    return {
        key: value
        for key, value in config.items()
        if value is not None
    }


def config_to_dict(
    value: Any,
    *,
    drop_none: bool = False,
) -> dict[str, Any]:
    """
    Convert dataclass -> dict.

    Parameters
    ----------
    value
        Dataclass instance.

    drop_none
        Whether to remove None values.

    Returns
    -------
    dict
    """

    if value is None:
        return {}

    if isinstance(value, dict):

        result = value.copy()

    elif is_dataclass(value):

        result = asdict(value)

    else:

        raise TypeError(
            f"Expected dataclass or dict, got {type(value).__name__}"
        )

    if drop_none:
        result = clean_none(result)

    return result


# ============================================================
# Main coercion
# ============================================================

def coerce_config(
    value: Any,
    cls: type[T],
) -> T:
    """
    Normalize None | dict | dataclass
    into a dataclass instance.

    Examples
    --------

    None
        -> cls()

    {"fontsize": 10}
        -> cls(fontsize=10)

    cls(...)
        -> returned unchanged
    """

    if not is_dataclass(cls):
        raise TypeError(
            f"{cls.__name__} must be a dataclass type."
        )

    # ------------------------------------------
    # None -> empty config
    # ------------------------------------------
    if value is None:
        return cls()

    # ------------------------------------------
    # Already dataclass
    # ------------------------------------------
    if isinstance(value, cls):
        return value

    # ------------------------------------------
    # Dict -> dataclass
    # ------------------------------------------
    if isinstance(value, dict):

        valid_fields = {
            field.name
            for field in fields(cls)
        }

        filtered = {
            key: val
            for key, val in value.items()
            if key in valid_fields
        }

        return cls(**filtered)

    raise TypeError(
        f"{cls.__name__} must be None, dict, or {cls.__name__}"
    )


# ============================================================
# Multi coercion
# ============================================================

def coerce_configs(
    **items,
) -> dict[str, Any]:
    """
    Coerce multiple configs at once.

    Example
    -------

    configs = coerce_configs(
        title=(title, FigureTitle),
        subtitle=(subtitle, FigureSubtitle),
        source=(source, FigureSource),
    )

    title = configs["title"]
    """

    output: dict[str, Any] = {}

    for name, item in items.items():

        if (
            not isinstance(item, tuple)
            or len(item) != 2
        ):
            raise ValueError(
                f"{name} must be provided as "
                "(value, config_class)"
            )

        value, cls = item

        output[name] = coerce_config(
            value=value,
            cls=cls,
        )

    return output
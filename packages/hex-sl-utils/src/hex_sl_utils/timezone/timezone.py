from hex_sl.utils import UserFacingError

from .windows_zones import IANA_TO_WINDOWS


def get_windows_zone(iana_zone: str) -> str:
    if iana_zone not in IANA_TO_WINDOWS:
        msg = f"Unknown IANA timezone: {iana_zone}"
        raise UserFacingError(msg)
    return IANA_TO_WINDOWS[iana_zone]

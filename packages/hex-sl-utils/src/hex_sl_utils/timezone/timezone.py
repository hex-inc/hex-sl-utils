from hex_sl_utils.exception import UserFacingError
from hex_sl_utils.timezone.iana_to_windows import IANA_TO_WINDOWS


def iana_to_windows(iana_zone: str) -> str:
    if iana_zone not in IANA_TO_WINDOWS:
        msg = f"Unknown IANA timezone: {iana_zone}"
        raise UserFacingError(msg)
    return IANA_TO_WINDOWS[iana_zone]

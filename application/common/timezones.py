import datetime
import pytz

from application.common import constants


# Check user properties and return the time format string which is appropriate.
def _apply_time_format_preference(properties: dict) -> str:
    if "USER_HOUR_FORMAT" in properties:
        value = properties["USER_HOUR_FORMAT"]
        time_format = (
            constants.TIMESTAMP_FORMAT_12_HR if value == "12" else constants.TIMESTAMP_FORMAT_24_HR
        )
    else:
        time_format = constants.DEFAULT_TIME_FORMAT_STR

    return time_format


def _apply_offset_to_datetime(dt: datetime.datetime, offset: int) -> datetime.datetime:
    return dt + datetime.timedelta(hours=offset)


def _offset_to_string(offset: int) -> str:
    if offset == 0:
        return "UTC+0h"
    elif offset > 0:
        return f"UTC+{offset}h"
    else:
        return f"UTC{offset}h"


def get_time_zone_dict() -> dict:
    count = 1
    time_zone_dict = {}

    for time_zone in pytz.common_timezones:
        tz_now = datetime.datetime.now(pytz.timezone(time_zone))
        offset = int(tz_now.utcoffset().total_seconds() / 60 / 60)
        offset_str = _offset_to_string(offset)

        time_zone_dict[time_zone] = {
            "time_zone_id": count,
            "time_zone": time_zone,
            "utcoffset": offset,
            "label": f"({offset_str}) {time_zone}",
        }
        count += 1

    return time_zone_dict


# A function that generates a list of hours of the day in 12-hour format with AM/PM
def get_hours_tuple_list() -> list:
    hours_list = []
    count = 1

    for i in range(1, 12):
        hours_list.append((f"{i}:00 AM", count))
        count += 1

    hours_list.append(("12:00 PM", count))
    count += 1

    for i in range(1, 12):
        hours_list.append((f"{i}:00 PM", count))
        count += 1

    hours_list.append(("12:00 AM", count))

    return hours_list

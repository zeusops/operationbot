from datetime import timedelta
from typing import Dict, List

import secret

VERSION = 10
# PURGE_ON_CONNECT = False
_test_channel = 530411066585382912
if secret.DEBUG:
    EVENT_CHANNEL = _test_channel
    EVENT_ARCHIVE_CHANNEL = _test_channel
    COMMAND_CHANNEL = _test_channel
    LOG_CHANNEL = _test_channel
    GAME = 'with bugs'
    EMOJI_GUILD = 219564389462704130
else:
    EVENT_CHANNEL = 502824760036818964
    EVENT_ARCHIVE_CHANNEL = 528914471700267029
    COMMAND_CHANNEL = 528980590930821131
    LOG_CHANNEL = 621066917339201547
    GAME = 'with events'
    # If set to 0, the bot uses Command Channel's guild
    EMOJI_GUILD = 0

JSON_FILEPATH = {
    "events":  "database/events.json",
    "archive": "database/archive.json",
}
ADDITIONAL_ROLE_EMOJIS = [
    "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FOUR}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FIVE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT SIX}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT SEVEN}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT EIGHT}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT NINE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{KEYCAP TEN}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER V}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER W}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER X}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Y}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Z}",
]

ADDITIONAL_ROLE_NAMES = [
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
]

# ATTENDANCE_EMOJI = "\N{HEAVY PLUS SIGN}"
ATTENDANCE_EMOJI = None

EXTRA_EMOJIS: List[str] = [
    # ATTENDANCE_EMOJI
]

PLATOON_SIZES = ['1PLT', '2PLT', 'sideop', 'WW2side']

# Dummy: an empty spacer. An embed can only have either one or three
# items on a line.
# Additional roles are automatically added at the end of the group list
DEFAULT_GROUPS = {
    "1PLT": [
        "Company",
        "1st Platoon",
        "Dummy",

        "Alpha",
        "Bravo",
        "Charlie"
    ],
    "2PLT": [
        "Battalion",
        "Company",
        "Dummy",

        "1st Platoon",
        "Alpha",
        "Bravo",

        "2nd Platoon",
        "Echo",
        "Foxtrot"
    ],
    "sideop": [
        "Company",
        "Alpha",
    ],
    "WW2side": [
        "Company",
        "1st Platoon",
    ],
}

# NOTE: role name equals emote name
DEFAULT_ROLES = {
    "1PLT": {
        "ZEUS": "Company",
        "1PLT": "1st Platoon",
        "FAC": "1st Platoon",
        "RTO": "1st Platoon",

        "ASL": "Alpha",
        "A1": "Alpha",
        "A2": "Alpha",
        "BSL": "Bravo",
        "B1": "Bravo",
        "B2": "Bravo",
        "CSL": "Charlie",
        "C1": "Charlie",
        "C2": "Charlie",
    },
    "2PLT": {
        "ZEUS": "Battalion",
        "CO": "Company",
        "FAC": "Company",
        "RTO": "Company",

        "1PLT": "1st Platoon",
        "ASL": "Alpha",
        "A1": "Alpha",
        "BSL": "Bravo",
        "B1": "Bravo",
        "CSL": "Charlie",
        "C1": "Charlie",
        "DSL": "Delta",
        "D1": "Delta",

        "2PLT": "2nd Platoon",
        "ESL": "Echo",
        "E1": "Echo",
        "FSL": "Foxtrot",
        "F1": "Foxtrot",
        "GSL": "Golf",
        "G1": "Golf",
        "HSL": "Hotel",
        "H1": "Hotel",
    },
    "sideop": {
        "ZEUS": "Company",
        "ASL": "Alpha",
        "A1": "Alpha",
        "A2": "Alpha",
    },
    "WW2side": {
        "ZEUS": "Company",
        "1PLT": "1st Platoon",
        "ASL": "1st Platoon",
        "BSL": "1st Platoon",
    },
}

EMOJI_ZEUS = "ZEUS"

# If a user signs off from a role listed in SIGNOFF_NOTIFY_ROLES when
# there is less than SIGNOFF_NOTIFY_TIME left until the operation start,
# a user defined in secrets.py gets notified about that.
SIGNOFF_NOTIFY_TIME = timedelta(days=1)
SIGNOFF_NOTIFY_ROLES: Dict[str, List] = {
    "1PLT": [
        "1PLT", "HQ", "ASL", "BSL", "CSL"
    ],
    "2PLT": [
        "CO", "HQ", "1PLT", "2PLT",
        "ASL", "BSL", "CSL", "DSL",
        "ESL", "FSL", "GSL", "HSL",
    ],
    "sideop": [],
    "WW2side": [],
}

TIME_ZONE = "CEST"
# Timezone location: has to be in following Format: Continent.Capital
TIME_ZONE_LOCATION = "Europe.Amsterdam"

PORT_DEFAULT = 2302
PORT_MODDED = 2402

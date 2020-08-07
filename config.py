from datetime import timedelta

import secret

VERSION = 7
# PURGE_ON_CONNECT = False
_test_channel = 530411066585382912
if secret.DEBUG:
    EVENT_CHANNEL = _test_channel
    EVENT_ARCHIVE_CHANNEL = _test_channel
    COMMAND_CHANNEL = _test_channel
    LOG_CHANNEL = _test_channel
    GAME = 'with bugs'
else:
    EVENT_CHANNEL = 502824760036818964
    EVENT_ARCHIVE_CHANNEL = 528914471700267029
    COMMAND_CHANNEL = 528980590930821131
    LOG_CHANNEL = 621066917339201547
    GAME = 'with events'

JSON_FILEPATH = {
    "events":  "database/events.json",
    "archive": "database/archive.json",
}
ADDITIONAL_ROLE_EMOJIS = [
    "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}",
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
]

PLATOON_SIZES = ['1PLT', '2PLT']

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
    ]
}

# NOTE: role name equals emote name
DEFAULT_ROLES = {
    "1PLT": {
        "ZEUS": "Company",
        "MOD": "Company",
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
    }
}

EMOJI_ZEUS = "ZEUS"

# If a user signs off from a role listed in SIGNOFF_NOTIFY_ROLES when
# there is less than SIGNOFF_NOTIFY_TIME left until the operation start,
# a user defined in secrets.py gets notified about that.
SIGNOFF_NOTIFY_TIME = timedelta(days=1)
SIGNOFF_NOTIFY_ROLES = {
    "1PLT": [
        "1PLT", "HQ", "ASL", "BSL", "CSL"
    ],
    "2PLT": [
        "CO", "HQ", "1PLT", "2PLT",
        "ASL", "BSL", "CSL", "DSL",
        "ESL", "FSL", "GSL", "HSL",
    ],
}

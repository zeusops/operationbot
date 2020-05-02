from datetime import timedelta

import secret

VERSION = 5
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

JSON_FILEPATH = "./eventDatabase.json"
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

# NOTE: role name equals emote name
DEFAULT_ROLES = {
    "Battalion": ["ZEUS", "MOD"],
    "Company": ["CO", "FAC", "RTO"],
    "Dummy": [],
    "1st Platoon": ["1PLT", "FAC", "RTO"],
    "Alpha": ["ASL", "A1"],
    "Bravo": ["BSL", "B1"],

    "Charlie": ["CSL", "C1"],
    "Delta": ["DSL", "D1"],

    "2nd Platoon": ["2PLT", "FAC", "RTO"],
    "Echo": ["ESL", "E1"],
    "Foxtrot": ["FSL", "F1"],

    "Golf": ["GSL", "G1"],
    "Hotel": ["HSL", "H1"],
}

# A list of groups to add to an event by default
DEFAULT_GROUPS = [
    # Dummy: an empty spacer. An embed can only have either one or three items
    # on a line
    "Battalion", "Company", "Dummy",
    "1st Platoon", "Alpha", "Bravo",
    "2nd Platoon", "Echo", "Foxtrot",
]

EMOJI_ZEUS = "ZEUS"

# If a user signs off from a role listed in SIGNOFF_NOTIFY_ROLES when
# there is less than SIGNOFF_NOTIFY_TIME left until the operation start,
# a user defined in secrets.py gets notified about that.
SIGNOFF_NOTIFY_TIME = timedelta(days=1)
SIGNOFF_NOTIFY_ROLES = [
    "HQ", "ASL", "BSL", "CSL", "DSL", "ESL", "FSL", "GSL", "HSL",
]

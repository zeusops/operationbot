import secret

VERSION = 5
_test_channel = 530411066585382912
if secret.DEBUG:
    EVENT_CHANNEL = _test_channel
    EVENT_ARCHIVE_CHANNEL = _test_channel
    COMMAND_CHANNEL = _test_channel
    PURGE_ON_CONNECT = False
    GAME = 'with bugs'
else:
    EVENT_CHANNEL = 530411066585382912
    EVENT_ARCHIVE_CHANNEL = 530411066585382912
    COMMAND_CHANNEL = 530411066585382912
    PURGE_ON_CONNECT = True
    GAME = 'with events'

JSON_FILEPATH = "./eventDatabase.json"
ADDITIONAL_ROLE_EMOJIS = [
    "\u0031\u20E3",
    "\u0032\u20E3",
    "\u0033\u20E3",
    "\u0034\u20E3",
    "\u0035\u20E3",
    "\u0036\u20E3",
    "\u0037\u20E3",
    "\u0038\u20E3",
    "\u0039\u20E3",
    "\u0030\u20E3",
]
DEFAULT_ROLES = {  # NOTE: role name equals emote name
    "ZEUS": "Company",
    "MOD": "Company",
    "HQ": "Platoon",
    "FAC": "Platoon",
    "RTO": "Platoon",
    "ASL": "Alpha",
    "A1": "Alpha",
    "A2": "Alpha",
    "BSL": "Bravo",
    "B1": "Bravo",
    "B2": "Bravo",
}

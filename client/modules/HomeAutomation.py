# -*- coding: utf-8-*-
import logging
import re
import paho.mqtt.publish as publish

LOCATIONS = ["bedroom-mark", "bedroom", "study", "kitchen", "lounge",
             "library", "hall", "ballroom"]

# regex matches
DEFAULT_STATES = r''
BINARY_STATES = r'\b(on|off)\b'
INTEGER_STATES = r'\b([0-9]+)\b'

ITEM_MAP = {
    'lights': {
        'name': 'lights',
        'topic': "/lights",
        'need-action': False,
        'states': BINARY_STATES,
    },
    'dimmers': {
        'name': 'dimmers',
        'topic': "/dimmers",
        'need-action': False,
        'states': INTEGER_STATES,
    },
    'temperature': {  # "set"
        'name': 'temperature',
        'topic': "/setpoint",
        'need-action': False,
        'states': INTEGER_STATES,
    },
    'thermostat': {  # "set"
        'name': 'thermostat',
        'topic': "/setpoint",
        'need-action': False,
        'states': INTEGER_STATES,
    },
    'media': {
        'name': 'media',
        'topic': None,  # absolutely require an action
        'need-action': True,
        'states': None,
    },
    'music': {
        'name': 'media',
        'topic': None,
        'need-action': True,
        'states': None,
    },
    'volume': {  # also an action
        'name': 'volume',
        'topic': "/media/volume",
        'need-action': False,
        'states': BINARY_STATES + '|' + INTEGER_STATES,
    },
    'scene': {
        'name': 'scene',
        'topic': "/scene",
        'need-action': False,
        'states': INTEGER_STATES,
    },
    'mood': {
        'name': 'mood',
        'topic': "/scene",
        'need-action': False,
        'states': INTEGER_STATES,
    },
}

ITEMS_REGEX = r'\b(?:%s)\b' % '|'.join(ITEM_MAP.keys())


ACTION_MAP = {
    'play': {
        'topic': "/media/playpause",
        'states': None
    },
    'pause': {
        'topic': "/media/playpause",
        'states': None
    },
    'stop': {
        'topic': "/media/stop",
        'states': None
    },
    'volume': {  # also an item
        'topic': "/media/volume",
        'states': BINARY_STATES + '|' + INTEGER_STATES,
    },
    'off': {
        'topic': "/media/stop",
        'states': DEFAULT_STATES,
    },
}
ACTIONS_REGEX = r'\b(?:%s)\b' % '|'.join(ACTION_MAP.keys())

WORDS = ["room"] + LOCATIONS + ITEM_MAP.keys()

PRIORITY = 1

MQTTHOST = "pixie"
TOPIC_ROOT = "ha/"
DEFAULT_LOC = LOCATIONS[0]


def handle(text, mic, profile):
    """
        Handle garage events based on user input

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
        number)
    """
    def on_connect(client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(TOPIC_ROOT + DEFAULT_LOC + "/status")

    def on_message(client, userdata, msg):
        mic.say("The room status is " + str(msg.payload))
        client.disconnect()

    logger = logging.getLogger(__name__)
    logger.debug("mqtt: got text=" + text)

    lower_text = text.lower()

    location = DEFAULT_LOC

    for l in LOCATIONS:
        if l in text:
            location = l.lower()

    if location == "bedroom":
        location = "bedroom-mark"

    item = None
    topic = None
    states = None
    new_state = "ON"

    # Attempt to match items first
    #  e.g. "music volume 50"
    item_match = re.search(ITEMS_REGEX, lower_text, re.IGNORECASE)

    if item_match:
        item = ITEM_MAP[item_match.group(0)]
        topic = item['topic']
        states = item['states']

    # If we need further info try to extract an action
    #  e.g. "volume 50", "media OFF"
    if not item or item['need-action']:
        action_match = re.search(ACTIONS_REGEX, lower_text, re.IGNORECASE)
        if action_match:
            action = ACTION_MAP[action_match.group(0)]
            # override the item topic and states
            topic = action['topic']
            states = action['states']

    if states:
        state_match = re.search(states, lower_text, re.IGNORECASE)
        if state_match:
            new_state = state_match.group(0)

    if topic and new_state:
        logger.debug("mqtt: publishing to " + location + topic)
        publish.single(TOPIC_ROOT + location + topic, new_state.upper(),
                       hostname=MQTTHOST, client_id=DEFAULT_LOC)
        mic.say(location + topic.replace('/', ' ') + " " + new_state)


def isValid(text):
    """
        Returns True if input is HA-related

        Arguments:
        text -- user-input, typically transcribed speech
    """
    tl = text.lower()
    for w in WORDS:
        if w in tl:
            return True

    return False

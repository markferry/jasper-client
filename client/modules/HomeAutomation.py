# -*- coding: utf-8-*-
import logging
import re
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

WORDS = ["BEDROOM", "STUDY", "KITCHEN", "LOUNGE", "LIBRARY", "HALL",
         "BALLROOM"]

PRIORITY = 1

MQTTHOST = "pixie"
TOPIC_ROOT = "ha/"
DEFAULT_LOC = "bedroom-mark"

MEDIA_ACTION = ["PLAY", "PAUSE", "STOP", "NEXT", "PREVIOUS"]

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

    location = ""

    for l in WORDS:
        if l in text:
            location = l.lower()

    if location == "bedroom":
        location = "bedroom-mark"

    if len(location) > 0:
        if "PLAY" in text or "PAUSE" in text:
            logger.debug("mqtt: publishing to media/playpause")
            publish.single(TOPIC_ROOT + location + "/media/playpause", "ON",
                           hostname=MQTTHOST, client_id=DEFAULT_LOC)
            mic.say(location + " media pause")

        if "STOP" in text:
            logger.debug("mqtt: publishing to media/stop")
            publish.single(TOPIC_ROOT + location + "/media/stop", "ON",
                           hostname=MQTTHOST, client_id=DEFAULT_LOC)
            mic.say(location + " media stop")

        if re.search(r'\bstatus\b', text, re.IGNORECASE):
            logger.debug("mqtt: publishing status")
            publish.single(TOPIC_ROOT + location + "/media/playpause",
                           "status", hostname=MQTTHOST,
                           client_id=DEFAULT_LOC)
            client = mqtt.Client(client_id=DEFAULT_LOC)
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect(MQTTHOST, 1883)
            client.loop_forever()


def isValid(text):
    """
        Returns True if input is HA-related

        Arguments:
        text -- user-input, typically transcribed speech
    """
    for l in WORDS:
        if l in text:
            return True

    return False

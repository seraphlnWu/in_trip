#coding=utf-8

import json
import requests

from in_trip.lib.config import Config

cfg = Config()
emotion_address = cfg.get('emotion', 'main')

def get_emotion(text, keyword):
    headers = {'Content-Type': 'application/json'}
    r = requests.post(emotion_address, data=json.dumps({'text': text, 'target': keyword}), headers=headers)
    emotion = r.json().get("Result") or 0.0

    if emotion == 0.0: #TODO: is this compare way correct?
        return 0
    elif emotion > 0.0:
        return 1
    else:
        return -1

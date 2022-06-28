import mimetypes
import os
import time

from database import db
from playsound import playsound
import requests

user_id = None


def download_voice_message(url):
    print(f"Downloading voice message.")
    folder = './voice_messages'

    res = requests.get(url)
    content_type = res.headers.get('content-type')
    extension = mimetypes.guess_extension(content_type)
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = f'{folder}/{int(time.time())}{extension}'
    open(path, 'wb').write(res.content)

    print(f"Voice message downloaded.")
    return path


def on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        data = change.document.to_dict()
        if not data['played']:
            path = download_voice_message(data['url'])
            playsound(path)

            os.remove(path)

            voice_ref = db.collection(user_id).document('data').collection('Voice_note').document(change.document.id)
            batch = db.batch()
            batch.update(voice_ref, {"played": True})
            batch.commit()


def voice_message_module(uid):
    global user_id
    user_id = uid

    doc_ref = db.collection(user_id).document('data').collection('Voice_note')
    doc_watch = doc_ref.on_snapshot(on_snapshot)


# if __name__ == '__main__':
#     uid = 'Jl2eZMHRHJQtSKYLBfxJv5Ynrt93'
#     voice_message_module(uid)

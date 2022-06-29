import time
from threading import Thread

import face_recognition
import cv2 as cv
import numpy as np
from database import db

encodings_id = []
encodings = []
labels = []
notified = []
user_id = None


def set_timer(person):
    time.sleep(120)
    notified.remove(person)


def add_to_History(person):
    if person not in notified:
        notified.append(person)
        Thread(target=set_timer, args=(person,))
        doc_ref = db.collection(user_id).document('data').collection('History')
        doc_ref.add({
            'message': 'Door has been unlocked for ' + person + ' at ' + time.ctime() + '.',
            'name': person,
            'time': time.ctime()
        })


def send_notification(unknown):
    if unknown not in notified:
        notified.append(unknown)
        Thread(target=set_timer, args=(unknown,))
        doc_ref = db.collection(user_id).document('data').collection('Notification')
        doc_ref.add({
            'message': 'Unknown Person has been detected, do want to unlock the door?' + '.',
            'time': time.ctime()
        })


def recognition(frame, fr_encodings, fr_labels):
    if len(fr_encodings) > 0:
        scaleDown = 0.25
        processedFrame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        processedFrame = cv.resize(processedFrame, (0, 0), None, scaleDown, scaleDown)

        currentFacesInFrame = face_recognition.face_locations(processedFrame)
        encodedCurrentFrameFaces = face_recognition.face_encodings(processedFrame, currentFacesInFrame, model="large")

        for encodedFace, currentFace in zip(encodedCurrentFrameFaces, currentFacesInFrame):
            # distance = face_recognition.face_distance(fr_encodings, encodedFace)
            match = face_recognition.compare_faces(fr_encodings, encodedFace,  tolerance=0.45)

            if True in match:
                index = match.index(True)
                name = fr_labels[index]
                add_to_History(name)
                # print(f"{name} {distance[index]}")
            else:
                name = 'unknown'
                send_notification(name)

            y1, x2, y2, x1 = currentFace
            y1, x2, y2, x1 = int(y1 / scaleDown), int(x2 / scaleDown), int(y2 / scaleDown), int(x1 / scaleDown)
            cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv.rectangle(frame, (x1, y2 - 32), (x2, y2), (0, 255, 0), cv.FILLED)
            cv.putText(frame, name, (x1 + 5, y2 - 6), cv.FONT_HERSHEY_COMPLEX_SMALL, .5, (255, 255, 255), 1)


def on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "REMOVED":
            index = encodings_id.index(change.document.id)
            encodings_id.pop(index)
            encodings.pop(index)
            labels.pop(index)
        elif change.type.name == "ADDED" or change.type.name == "MODIFIED":
            data = change.document.to_dict()
            encodings_id.append(change.document.id)
            encodings.append(np.asarray(data['encode']))
            labels.append(data['label'])


def start_recognition(id):
    global user_id

    user_id = id
    camera_ip = 'rtsp://192.168.10.29/live/ch00_1'
    camera = cv.VideoCapture(camera_ip)
    doc_ref = db.collection(user_id).document('data').collection('Encodings')
    doc_watch = doc_ref.on_snapshot(on_snapshot)

    while True:
        success, img = camera.read()
        if success:
            recognition(img, encodings.copy(), labels.copy())
            # cv.imshow('camera', img)
            # cv.waitKey(1)


# if __name__ == '__main__':
#     start_recognition()

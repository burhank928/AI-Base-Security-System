import RPi.GPIO as GPIO
from time import sleep
from database import db


def on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "ADDED" or change.type.name == "MODIFIED":
            data = change.document.to_dict()
            if not data['lock']:
                print("Door is unlocked.")

                GPIO.output(18, 1)
                sleep(2)
                GPIO.output(18, 0)

                ref_for_lock = db.collection(user_id).document('data')
                batch = db.batch()
                batch.update(ref_for_lock, {"lock": True})
                batch.commit()

                print("Door is locked.")


def solenoid_lock_module(uid):
    global user_id
    user_id = uid

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)

    doc_ref = db.collection(user_id).document('data')
    doc_watch = doc_ref.on_snapshot(on_snapshot)

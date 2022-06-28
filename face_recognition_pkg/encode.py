import mimetypes
import os
import shutil
from threading import Thread

import cv2 as cv
import face_recognition
import requests
from database import db

user_id = None


def download_imgs(person_name, img_urls):
    print(f"Downloading images of {person_name}.")
    index = 0
    for url in img_urls:
        res = requests.get(url)
        content_type = res.headers.get('content-type')
        extension = mimetypes.guess_extension(content_type)
        if not os.path.exists(person_name):
            os.makedirs(person_name)
        open(f'{person_name}/{index}{extension}', 'wb').write(res.content)
        index += 1
    print(f"Downloaded images of {person_name}.")


def download_and_encode_images(person_id, person, img_urls):
    download_imgs(person, img_urls)
    person_imgs = os.listdir(person)

    print(f"Total Imgs of {person_imgs}: {len(person_imgs)}")
    for person_img in person_imgs:
        img = cv.imread(person + '/' + person_img)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        encoded = face_recognition.face_encodings(img, num_jitters=2, model="large")
        if len(encoded) > 0:
            doc_ref = db.collection(user_id).document('data').collection('Encodings')
            doc_ref.add({
                'id': person_id,
                'label': person,
                'encode': encoded[0].tolist()
            })
            print(f"{person} with {person_img} image encoded and pushed.")
        else:
            print(f"{person} with {person_img} image has no encodings.")

    shutil.rmtree(person)
    person_ref = db.collection(user_id).document('data').collection('Persons').document(person_id)
    batch = db.batch()
    batch.update(person_ref, {"train": True})
    batch.commit()
    print("Committed")


def delete_encodings_from_firebase(person_id):
    encodings = db.collection(user_id).document('data').collection("Encodings").where("id", "==", person_id).get()
    batch = db.batch()
    for encode in encodings:
        ref = db.collection(user_id).document('data').collection('Encodings').document(encode.id)
        batch.delete(ref)
        batch.commit()


def add_encodings_from_firebase(person_id, data, threads):
    if not data['train']:
        print("wait for download_and_encode_images join")
        thread = Thread(target=download_and_encode_images,
                        args=(person_id, data["name"], data["image_urls"]))
        thread.start()
        threads.append(thread)


def on_snapshot(doc_snapshot, changes, read_time):
    threads = []
    for change in changes:
        if change.type.name == "REMOVED":
            delete_encodings_from_firebase(change.document.id)
        elif change.type.name == "ADDED":
            add_encodings_from_firebase(change.document.id, change.document.to_dict(), threads)

    for thread in threads:
        thread.join()
        print("download_and_encode_images joined")


def start_encoding(id):
    global user_id

    user_id = id
    doc_ref = db.collection(user_id).document('data').collection('Persons')
    doc_watch = doc_ref.on_snapshot(on_snapshot)


# if __name__ == '__main__':
#     start_encoding()

# download_and_encode_images("3", "Burhan", "img_urls")
# download_and_encode_images("0", "ahmad", "img_urls")
# download_and_encode_images("1", "huzaifa", "img_urls")
# download_and_encode_images("2", "umer", "img_urls")

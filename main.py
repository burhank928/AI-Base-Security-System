import pickle
from os.path import exists
from firebase_admin import auth

from face_recognition_pkg.main import face_recognition_module
from license_number_extraction_pkg.main import license_number_extraction_module
from voice_message_pkg.main import voice_message_module
from threading import Thread


def save_object(obj):
    try:
        with open("data.pickle", "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error during pickling object (Possibly unsupported):", ex)


def load_object(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as ex:
        print("Error during unpickling object (Possibly unsupported):", ex)


def authenticate_user_exist(email):
    try:
        user_ref = auth.get_user_by_email(email)
        return user_ref.uid
    except:
        return None


if __name__ == '__main__':
    user_id = None

    if not exists("data.pickle"):
        user_found = False
        while not user_found:
            email = input("Enter Email: ")
            user_id = authenticate_user_exist(email)
            if user_id is not None:
                save_object(user_id)
                user_found = True
            else:
                print("User Not Exist.")
    else:
        user_id = load_object("data.pickle")
        print(user_id)

    face_recognition_thread = Thread(target=face_recognition_module, args=(user_id,))
    license_number_extraction_thread = Thread(target=license_number_extraction_module, args=(user_id,))
    voice_message_thread = Thread(target=voice_message_module, args=(user_id,))

    face_recognition_thread.start()
    license_number_extraction_thread.start()
    voice_message_thread.start()

    print("wait for face_recognition_module join")
    print("wait for license_number_extraction_module join")
    print("wait for voice_message_module join")

    face_recognition_thread.join()
    print("face_recognition_module joined")

    license_number_extraction_thread.join()
    print("license_number_extraction_module joined")

    voice_message_thread.start()
    print("voice_message_module joined")

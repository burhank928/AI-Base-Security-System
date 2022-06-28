from .encode import start_encoding
from .recognation import start_recognition


def face_recognition_module(user_id):
    start_encoding(user_id)
    start_recognition(user_id)


# if __name__ == '__main__':
#     face_recognition_module()

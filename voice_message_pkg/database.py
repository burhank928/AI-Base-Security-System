import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


cred = credentials.Certificate('aifyp-ecdf8-firebase-adminsdk-3u3jz-fc40c750d5.json')
firebase = firebase_admin.initialize_app(cred)
db = firestore.client()

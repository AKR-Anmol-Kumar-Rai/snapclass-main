import numpy as np
import dlib
import face_recognition_models 
from sklearn.svm import SVC
import streamlit as st

from src.screens.database.db import get_all_students

#  dlib provide 3 type of models:
#  1. a model to detect face
#  2. model that detects points on face(landmark)
#  3. a model to convert landmark into embeddings

@st.cache_resource  # model are loaded only one times dont need to load modle again and again
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()  #tells how many faces do we have in an image and their positions(in coordinates)

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()  #this model provides location of the landmark
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector ,sp, facerec


def get_face_embedings(image_np):
    detector, sp, facerec = load_dlib_models()

    faces = detector(image_np,3)  # here 3 means that the images would be processed 3 times to recognize faces

    encodings = []

    for face in faces:
        shape = sp(image_np, face)  # landmarks
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 3)  #128 numbers or embeddings

        encodings.append(np.array(face_descriptor))

    return encodings


# training our classifier
@st.cache_resource   # means this function will run only onetime no need to load this heavy function again and again
def get_trained_model():
    X=[]
    y=[]
    
    student_db = get_all_students()

    for student in student_db:
        embeddings = student.get("face_embedding")
        if embeddings:
            X.append(np.array(embeddings))
            y.append(student.get("student_id"))

    if len(X)==0:
        return 0

    classifier = SVC(kernel='linear', probability=True,class_weight='balanced')

    try:
        classifier.fit(X,y)
    except ValueError:
        pass  

    return {"clf": classifier,'X':X,'y':y}          


def train_classifier():
    st.cache_resource.clear()

    model_data = get_trained_model()
    return bool(model_data)

def predict_attendance(class_image_np):
    encodings = get_face_embedings(class_image_np)

    detected_students = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_students, [], len(encodings)
    
    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']


    all_students = sorted(list(set(y_train)))

    for encoding in encodings:
        if(len(all_students)>=2):
            predicted_id = int(clf.predict([encoding])[0])

        else:
            predicted_id = int(all_students[0])    

        student_embeddings = X_train[y_train.index(predicted_id)]

        best_match_score  = np.linalg.norm(student_embeddings - encoding)

        resembler_threshold = 0.6

        if best_match_score <= resembler_threshold:
            detected_students[predicted_id]  = True

    return detected_students, all_students, len(encodings)        




import streamlit as st
from src.screens.database.db import create_subject
from src.screens.database.config import supabase
from src.screens.database.db import enroll_student_to_subject
from src.screens.pipelines.voice_pipeline import process_bulk_audio
from src.screens.database.config import supabase
from datetime import datetime
import pandas as pd
from src.screens.components.dialog_attendance_to_result import show_attendance_result



@st.dialog("Voice Attentance")
def voice_attendance_dialog(selected_subject_id):
    st.write("Record Audio of students saying i am present , Then AI will recognize the students")
    
    audio_data = None
    audio_data = st.audio_input("Recod classroom audio")

    if st.button("Analyze Audio",type='primary',width='stretch'):
        with st.spinner("Processing Audio data"):
                enroll_response = supabase.table("subject_students").select("*, students(*)").eq('subject_id',selected_subject_id).execute()
                enroll_students = enroll_response.data

                if not enroll_students:
                    st.warning("No students enrolled in this course") 
                    return           

                candidate_dict = {
                     s['students']['student_id'] : s['students']['voice_embedding']
                     for s in enroll_students if s['students'].get('voice_embedding')
                }

                if not candidate_dict:
                     st.error('No enrolled students have voice profiles registerd')

                audio_bytes = audio_data.read()

                detected_scores = process_bulk_audio(audio_bytes,candidate_dict)

                results , attendance_to_log = [], []
                current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")   

                for node in enroll_students:
                    student = node['students']
                    score = detected_scores.get(student['student_id'],0.0)

                    is_present = bool(score>0)

                    results.append({
                        "Name": student['name'],
                        "ID": student['student_id'],
                        "Source": score if is_present else "-",
                        "Status": "✅Present" if is_present else "❌Absent"
                    })

                    attendance_to_log.append({
                        'student_id': student['student_id'],
                        'subject_id': selected_subject_id,
                        'timestamp' : current_timestamp,
                        "is_present" : bool(is_present)
                    }) 

                st.session_state.voice_attendance_results = (pd.DataFrame(results),attendance_to_log)

    if st.session_state.get("voice_attendance_results"):
         st.divider()
         df_results , logs =  st.session_state.voice_attendance_results
         show_attendance_result(df_results,logs)
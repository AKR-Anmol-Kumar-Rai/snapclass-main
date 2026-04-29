from src.screens.database.config import supabase
import bcrypt #fro hashing[to hide passwords]

# hashing
def hash_pass(pswrd):
    return bcrypt.hashpw(pswrd.encode(),bcrypt.gensalt()).decode()    # .encode converts pswrd in binary from bcoz haspw take input as binary


def check_pass(pswrd,hash_pswrd):
  return bcrypt.checkpw(pswrd.encode(),hash_pswrd.encode())



# making method that check if the useeid is already taken or not

def check_teacher_exist(username):
    # check unique username , returns false when username already taken
    response = supabase.table("teachers").select("username").eq("username",username).execute()
    return len(response.data) > 0

def create_teacher(username, password, name):

    data = {"username" : username, "password" : hash_pass(password), "name" : name}   #{column_name:value}
    response = supabase.table("teachers").insert(data).execute()
    return response.data

def teacher_login(username,password):

    response = supabase.table("teachers").select("*").eq("username",username).execute()
    if response.data:   # we get response in array => [[]]
        teacher = response.data[0]
        if check_pass(password,teacher['password']):
            return teacher
        return None
    
def get_all_students():
    response = supabase.table("students").select("*").execute()
    return response.data    

def create_student(new_name,face_embedding=None,voice_embedding=None):
    data = {'name':new_name, 'face_embedding':face_embedding, 'voice_embedding':voice_embedding}
    response = supabase.table('students').insert(data).execute()
    return response.data


def create_subject(subject_code, name, section, teacher_id):
    data = {'subject_code':subject_code , 'name':name, 'section':section, 'teacher_id':teacher_id}
    response = supabase.table('subjects').insert(data).execute()
    return response.data

def get_teacher_subject(teacher_id):
    response = supabase.table("subjects").select("*, subject_students(count), attendance_logs(timestamp)").eq('teacher_id',teacher_id).execute()
    subjects = response.data    # response.data are always list of dictionary

    for sub in subjects:
        sub['total_students'] = sub.get("subject_students", [{}])[0].get("count",0) if  sub.get("subject_students") else 0
        attendance = sub.get("attendance_logs",[])
        unique_sessions = len(set(log['timestamp'] for log in attendance))
        sub['total_classes']= unique_sessions

        sub.pop('subject_students',None)
        sub.pop('attendance_logs',None)

    return subjects    

def enroll_student_to_subject(student_id, subject_id):
    data = {'subject_id':subject_id, 'student_id':student_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
    data = {'subject_id':subject_id, 'student_id':student_id}
    response = supabase.table('subject_students').delete().eq('student_id',student_id).eq('subject_id',subject_id).execute()
    return response.data

def get_student_subjects(student_id):
    response = supabase.table("subject_students").select("*, subjects(*)").eq('student_id',student_id).execute()
    return response.data

def get_student_attendance(student_id):
    response = supabase.table("attendance_logs").select("*,subjects(*)").eq('student_id',student_id).execute()
    return response.data

def create_attendance(logs):
    response = supabase.table("attendance_logs").insert(logs).execute()
    return response.data

def  get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id',teacher_id).execute()
    return response.data
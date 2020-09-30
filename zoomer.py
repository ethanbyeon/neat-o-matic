import capture
import pandas as pd
import pyautogui as pug
import time
from tkinter import filedialog

class Zoomer:

    def __init__(self):
        self.name = 'Zoomer'

    
    def setup_df(self, input_file, output_file):
        
        student_df = pd.read_csv(input_file)
        student_df.fillna('NA', inplace=True)
        student = {'Student ID': [], 'Name': [], 'Status': [], 'Time': []}
        
        students = []
        for r in range(0, len(student_df.iloc[:, 1:])):
            for c in student_df.iloc[r, 1:]:
                if c != 'NA':
                    students.append(c)
        
        for s in sorted(students):
            info = s.replace(',', '').split(' ')

            student['Student ID'].append(info[2])
            student['Name'].append(info[1] + ' ' + info[0])
            student['Status'].append('NA')
            student['Time'].append('NA')

        output_df = pd.DataFrame(student)
        output_df.to_csv(output_file, index=False)
    

    def attendance(self, input_file, output_file, student_type):

        waiting_room_label = capture.find_img_coordinates('waiting_room_label.png', 'meeting')
        dot_btn = capture.find_img_coordinates('dot_btn.png', 'meeting')
        
        nonverbal_btns = capture.find_img_coordinates('nonverbal_btns.png', 'meeting')
        if waiting_room_label is not None:
            x1, y1 = waiting_room_label[0] - 35, waiting_room_label[1] + 10
            x2, y2 = dot_btn[0], dot_btn[1] - 10
            width = x2 - x1
            height = y2 - y1
            
            if nonverbal_btns is not None:
                x1, y1 = waiting_room_label[0] - 35, waiting_room_label[1] + 10
                x2, y2 = dot_btn[0], nonverbal_btns[1] - 20
                width = x2 - x1
                height = y2 - y1

            capture.part_screenshot(x1, y1, width, height, 'meeting')

            if student_type == 'Student':
                self.validate_students(x1, y1, output_file)
            if student_type == 'Leader':
                self.validate_leaders(x1, y1, input_file, output_file)
        else:
            return


    # CHECKS IF THE STUDENT'S NAME IN WAITING ROOM IS WRITTEN IN THE STUDENT ROSTER
    def validate_students(self, x, y, output_file):
       
        waiting_list = capture.get_text_coordinates('waiting_list.png', 'meeting')
        waiting_list_names = set(student['Text'] for student in waiting_list)
        df_pool = set()

        attendance_list = {'Present': [], 'Absent': [], 'Unknown': []}
        
        output_df = pd.read_csv(output_file)
        output_df.fillna('NA', inplace=True)
        for r in range(0, len(output_df.iloc[:, 1:])):
            for c in output_df.iloc[r, 1:]:
                if c != 'NA':
                    df_pool.add(c)

        present_students = waiting_list_names.intersection(df_pool)
        absent_students = df_pool.difference(waiting_list_names)
        unknown_students = waiting_list_names.difference(df_pool)
    
        for r in range(0, len(output_df.iloc[:, 1:2])):
            for c in output_df.iloc[r, 1:2]:
                if output_df.iat[r, 2] == "PRESENT":
                    continue
                if c in present_students or c in absent_students:
                    if c in present_students:
                        output_df.iat[r, 2] = "PRESENT"
                        self.admit_student(x, y, c, waiting_list)
                    if c in absent_students:
                        output_df.iat[r, 2] = "ABSENT"

                    output_df.iat[r, 3] = time.strftime('%H:%M:%S', time.localtime())
        
        output_df.to_csv(output_file, index=False)

        attendance_list['Present'].append(present_students)
        attendance_list['Absent'].append(absent_students)
        attendance_list['Unknown'].append(unknown_students)
        
        return attendance_list


    def validate_leaders(self, x, y, input_file, output_file):
        leaders = set()

        input_df = pd.read_csv(input_file)
        for r in input_df.iloc[:, 1]:
            info = r.replace(',', '').split(' ')
            name = info[1] + ' ' + info[0]
            leaders.add(name)

        output_df = pd.read_csv(output_file)
        output_df.fillna('NA', inplace=True)

        for name in leaders:
            parts = name.split(' ')
            # INSERT FILTER
            pug.click(capture.find_img_coordinates('participants_search.png', 'meeting'))
            pug.typewrite(name)

            waiting_list = capture.get_text_coordinates('waiting_list.png', 'meeting')
            waiting_name = set(waiting_list[0]['Text'])

            present_leaders = waiting_name.intersection(leaders)
            absent_leaders = leaders.difference(waiting_name)

        if waiting_list[0]['Text'] == name and len(waiting_list) == 1:
            pug.moveTo(x + waiting_list[0]['Coordinates']['x'], y + waiting_list[0]['Coordinates']['y'])
            pug.click(capture.find_img_coordinates('admit_btn.png', 'meeting'))
            pug.click(capture.find_img_coordinates('close_searchbar.png', 'meeting'))
        
        # output_df.to_csv(output_file, index=False)


    def admit_student(self, x, y, student, waiting_list):
        match = next(person for person in waiting_list if person['Text'] == student)
        pug.moveTo(x + match['Coordinates']['x'], y + match['Coordinates']['y'])
        pug.click(capture.find_img_coordinates('admit_btn.png', 'meeting'))
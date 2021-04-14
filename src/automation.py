import capture
import numpy as np
import pandas as pd
import pyautogui as pug
import time

from tkinter import filedialog
from collections import OrderedDict


def setup_df(input_file):
    global df
    
    student_df = pd.read_csv(input_file)
    student_df.fillna('NA', inplace=True)
    d = OrderedDict({'ID': [], 'Name': [], 'Status': [], 'Admit Time': []})
    
    students = []
    for r in range(0, len(student_df.iloc[:, 1:])):
        for c in student_df.iloc[r, 1:]:
            if c != "NA":
                students.append(c)

    for s in sorted(students):
        info = (s.replace(',','').replace('(','').replace(')','')).split(' ')
        if len(info) == 4:
            d['Name'].append(f'{info[0]}, {info[1]} {info[2]}')
            d['ID'].append(info[3])
        elif len(info) == 3:
            d['Name'].append(f'{info[0]}, {info[1]}')
            d['ID'].append(info[2])
        else:
            print(f"Format error in cell containing: {info}")
            return False
        d['Status'].append("NA")
        d['Admit Time'].append("NA")
    df = pd.DataFrame(d)
    # print(df)
    return True


def attendance(input_file, category):
    global df

    if check_screen():
        if category == "student":
            q = validate_students()
        elif category == "leader":
            q = validate_leaders(input_file)
        search(q)


search_bar = None
x, y, width = 0, 0, 0
def check_screen():
    global search_bar, x, y, width
    
    dot_btn = capture.find_img_coordinates("dot_btn.png", "meeting")
    if dot_btn:
        search_bar = capture.find_img_coordinates("participants_search.png", "meeting")
        if search_bar:
            x, y = search_bar[0] - 100, search_bar[1] + 20
            width = dot_btn[0] - x
            return True
        else:
            print("Please clear the search bar.")
            return False


def validate_students():
    print("Admitting STUDENTS . . .")
    students, present_students, absent_students = set(), set(), set()
    for r in range(0, len(df.iloc[:, 1:2])):
        for c in df.iloc[r, 1:2]:
            info = c.replace(',', '').split(' ')
            name = f'{info[1]} {info[0]}'

            if df.iat[r, 2] == "PRESENT":
                present_students.add(name)
            else:
                students.add(name)
                absent_students.add(name)

    search = {'DF': students, 'ABSENT': absent_students, 'PRESENT': present_students}
    print("SEARCH S:", search)
    return search


def validate_leaders(input_file):
    # print(df)
    in_df = pd.read_csv(input_file)
    print("Admitting LEADERS . . .")
    leaders, present_leaders, absent_leaders = set(), set(), set()
    for r in range(len(in_df.iloc[:, 1])):
        info = ((in_df.iloc[r, 1]).replace(',', '').replace('(', '').replace(')', '')).split(' ')

        if len(info) == 4:
            df_name = f'{info[0]}, {info[1]} {info[2]}'
        elif len(info) == 3:
            df_name = f'{info[0]}, {info[1]}'
        name = f'{info[1]} {info[0]}'

        name_pos = df.loc[(df_name == df['Name'])].index[0]
        if df.iat[name_pos, 2] == "PRESENT":
            present_leaders.add(name)
            print("P",name)
            continue
        else:
            print("e",name)
            leaders.add(name)
            absent_leaders.add(name)

    search = {'DF': leaders, 'ABSENT': absent_leaders, 'PRESENT': present_leaders}
    print("SEARCH L:", search)
    return search


def search(queue):
    global search_bar, width

    for df_name in queue['ABSENT']:
        print(f"[?] Searching  : {df_name}")
        pug.click(search_bar)
        pug.typewrite(df_name)

        wait_label = capture.find_img_coordinates("waiting_room_label.png", "meeting")
        in_meeting_label = capture.find_img_coordinates("in_the_meeting_label.png", "meeting")
        
        if wait_label and in_meeting_label:
            x, y = wait_label[0] - 20, wait_label[1] + 10
            height = in_meeting_label[1] - (wait_label[1] + 25)

            wait_list = capture.get_text_coordinates(x, y, width, height)
            wait_name = set(student['Text'] for student in wait_list)
            
            # MOVE TO NEXT STUDENT IF MORE THAN ONE NAME IS DETECTED
            # if len(wait_name) > 1:
            #     print(f"IMPOSTER DETECTED: {name}")
            #     continue

            print("P:", queue['PRESENT'])
            print("A:", queue['ABSENT'])

            for name in wait_name:
                if len(name) == len(df_name):
                    if spell_check({df_name : name}) <= 2:
                        present = set([df_name]).intersection(queue['DF'])
                        absent = queue['DF'].difference(set([df_name]))
                else:
                    present = set([name]).intersection(queue['DF'])
                    absent = queue['DF'].difference(set([name]))
            print("BEFORE", absent)
            if len(present) != 0:
                queue['PRESENT'] = present
            queue['ABSENT'] = absent

            print("P2:", queue['PRESENT'])
            print("A2:", queue['ABSENT'])

            record_student(queue['PRESENT'], queue['ABSENT'], wait_list)
            close_search()
        else:
            close_search()
            print("Could not locate labels.")
            break
    
    print(f"\nABSENT  ({len(queue['ABSENT'])}): {queue['ABSENT']}")
    print(f"PRESENT ({len(queue['PRESENT'])}): {queue['PRESENT']}")
    print("-------")
    return len(absent), len(present)


def record_student(present, absent, wait_list):

    for r in range(0, len(df.iloc[:, 1:2])):
        for c in df.iloc[r, 1:2]:
            info = (c.replace(',','')).split(' ')
            name = f'{info[1]} {info[0]}'

            if df.iat[r, 2] == "PRESENT":
                continue
            else:
                if name in present:
                    admit_student(name, wait_list)
                    df.iat[r, 2] = "PRESENT"
                    print("ADMITTED")
                elif name in absent:
                    df.iat[r, 2] = "ABSENT"
            df.iat[r, 3] = time.strftime('%H:%M:%S', time.localtime())
    print(df)


def admit_student(name, wait_list):
    global x, y
    match = None
    for wait_name in wait_list:
        if name == wait_name['Text']:
            match = wait_name
    if match:
        pug.moveTo(x + match['Coordinates']['x'], y + match['Coordinates']['y'])
        pug.click(pug.locateOnScreen('res/meeting/admit_btn.png', grayscale=True))
        print(f"[!] ADMITTED   : {match['Text']}")


def spell_check(name_dict):
    count = 0
    for key, value in name_dict.items():
        for i in range(len(value)):
            if(value[i] != key[i]):
                count+=1
    print(name_dict, count)
    return count


def close_search():
    blue_close_btn = capture.find_img_coordinates("blue_close_search.png", "meeting")
    if blue_close_btn:
        pug.click(blue_close_btn[0]-5, blue_close_btn[1])
    else:
        close_btn = capture.find_img_coordinates("close_search.png", "meeting")
        if close_btn:
            pug.click(close_btn[0]-5, close_btn[1])


def export(output_file):
    df.to_csv(output_file, index=False)
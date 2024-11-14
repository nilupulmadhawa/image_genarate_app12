import cv2
import os
import json
from PIL import Image, ImageDraw, ImageFont # type: ignore
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# set output date
date = datetime(2018, 6, 1)

A_presectage = 0.2
B_presectage = 0.8

# Folder paths
templates_path = './templates'
output_folder = './processed_images/' + date.strftime('%Y-%m-%d') 
resources_folder = './resources'
font_folder = './fonts'

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# If resources file is exist
if not os.path.exists(resources_folder + '/task.csv'):
    print('Resources file task.csv not found')
    exit()

if not os.path.exists(resources_folder + '/deposit_list_A.csv'):
    print('Resources file deposit_list_A.csv not found')
    exit()

if not os.path.exists(resources_folder + '/deposit_list_B.csv'):
    print('Resources file deposit_list_B.csv not found')
    exit()

def load_csv_array(csv_file):
    data = pd.read_csv(csv_file)
    array = data.iloc[:, 0].values  # `iloc[:, 0]` selects the first column
    return array

def can_fit_tasks(row):
    # Convert start_time and end_time to datetime objects
    start_time = datetime.strptime(row['from'], '%H:%M')
    end_time = datetime.strptime(row['to'], '%H:%M')
    total_duration = (end_time - start_time).seconds / 60
    required_duration = row['qty'] * row['gap']
    return required_duration > total_duration

def generate_random_time_slots(start_time, end_time, qty):
    random_times = []
    time_range = (end_time - start_time).seconds // 60  # Total available minutes

    for _ in range(qty):
        random_minutes = random.randint(0, time_range)
        random_time = start_time + timedelta(minutes=random_minutes)
        random_times.append(random_time)
    return random_times

def generate_time_slots(start_time, qty, gap):
    time_slots = []
    current_time = start_time
    
    for _ in range(qty):
        time_slots.append(current_time)
        current_time += timedelta(minutes=gap)
    
    return time_slots

def draw_image(draw, time_slot, amount, data):
    for item in data:
        attr_type = item['attr_type']
        x = item['x']
        y = item['y']
        font_path = item['font']
        align = item['align']
        size = item['size']
        color = item['color']
        format = item['format']
        underline = item['underline']

        # Choose the font
        font = ImageFont.truetype(font_folder+"/"+font_path, size)

        # Format the text based on the attribute
        if attr_type == 'number':
            text = f"{amount:0.2f}"
        elif attr_type == 'datetime':
            text = time_slot.strftime(format)
        else:
            text = ""

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]


        # Draw the text on the image
        y -= text_height+5

        if align == "center":
            x -= text_width // 2
        elif align == "right":
            x -= text_width
        # elif align == "left":
        #     x +=text_width

        # Draw the text on the image at the specified position
        draw.text((x, y), text, font=font, fill=color)
        if underline:
            draw.line((x, y + text_height+13, x + text_width, y + text_height+13), fill=color, width=2)

    return draw


# Load resources
task = pd.read_csv(resources_folder + '/task.csv', delimiter='\t')
deposit_list_A = load_csv_array(resources_folder + '/deposit_list_A.csv')
deposit_list_B = load_csv_array(resources_folder + '/deposit_list_B.csv')
withdrwal_list = load_csv_array(resources_folder + '/withdrwal_list.csv')
bonus_list = load_csv_array(resources_folder + '/bonus.csv')

# Load processed_images.json file
processed_images_path = './processed_images.json'
if os.path.exists(processed_images_path):
    with open(processed_images_path, 'r') as f:
        processed_images = json.load(f)

# Load  templates folder image settinge json from if exist processed_images.json
images_list = []

for i in processed_images: 
    base_name = os.path.splitext(i)[0]
    tmp_ext = os.path.splitext(i)[1]
    json_name = base_name + ".json"
    with open(templates_path + '/' + json_name, 'r') as f:
        image_settings = json.load(f)
        image_settings['name'] = i
        images_list.append(image_settings)

# Loop task 
for index, row in task.iterrows():
    task_id = row['task_id']
    start_time = row['from']
    end_time = row['to']
    task_type = row['task_type']
    gap = row['gap']
    qty = row['qty']
    max_amount= row['max']
    print(f"Task ID: {task_id} is processing with {qty} images")

    tmp_task_type_template = list(filter(lambda x: x['type'] == task_type, images_list))
    tmp_used_template = []
    if len(tmp_task_type_template) < qty:
        print(f"{task_type} template not enough")
        exit()

    start_time = datetime.strptime(start_time, '%H:%M')
    end_time = datetime.strptime(end_time, '%H:%M')
    start_time = date.replace(hour=start_time.hour, minute=start_time.minute)
    end_time = date.replace(hour=end_time.hour, minute=end_time.minute)

    is_random = can_fit_tasks(row)
    time_slots = []
    if is_random:
        # Generate random times for the given qty
        time_slots = generate_random_time_slots(start_time, end_time, qty)
    else:
        # Generate time slots based on the qty and gap
        time_slots = generate_time_slots(start_time, qty, gap)

    A_presectage_count = 0
    B_presectage_count = 0 
    # loop time_slots
    for time_slot in time_slots:
        print(f"Task ID: {task_id} is processing at {time_slot}")
        # Randomly select a template
        
        #if type is withdrwal chose from withdrwal_list A and B with presectage
        if task_type == 'deposit':
            if A_presectage_count < qty * A_presectage:
                amount = random.choice(deposit_list_A)
                A_presectage_count += 1
            else:
                amount = random.choice(deposit_list_B)
                B_presectage_count += 1
        elif task_type == 'withdrwal':
            amount = random.choice(withdrwal_list)
        elif task_type == 'bonus':
            amount = random.choice(bonus_list)
        else:
            print('Task type not found')
            exit()
        
        template = random.choice(tmp_task_type_template)
        atempt = 0
        while template['amount_digits_max'] < len(str(amount)) and template['amount_digits_min'] > len(str(amount)):
            template = random.choice(tmp_task_type_template)
            atempt += 1
            if atempt > 20:
                print('All template is not match with amount')
                exit()

        while template in tmp_used_template:
            atempt = 0
            template = random.choice(tmp_task_type_template)
            while template['amount_digits_max'] < len(str(amount)) and template['amount_digits_min'] > len(str(amount)):
                template = random.choice(tmp_task_type_template)
                atempt += 1
                if atempt > 20:
                    print('All template is not match with amount')
                    exit()
            if len(tmp_task_type_template) == len(tmp_used_template):
                print('All template is used for this task')
                exit()
            
                
        tmp_used_template.append(template)

        if max_amount == 0:
            image = Image.open(templates_path + '/' + template['name'])
            draw = ImageDraw.Draw(image)
            draw = draw_image(draw, time_slot, amount, template['data'])
            if not os.path.exists(output_folder+"/"+str(task_id)):
                os.makedirs(output_folder+"/"+str(task_id))
            image.save(output_folder+"/"+str(task_id)+"/"+template['name'])
        else:
            while amount >= max_amount:
                tmp_amount = max_amount
                amount -= max_amount
                image = Image.open(templates_path + '/' + template['name'])
                draw = ImageDraw.Draw(image)
                # add random minite to time_slot 0-5
                time_slot = time_slot + timedelta(minutes=random.randint(0, 5))
                draw = draw_image(draw, time_slot, tmp_amount, template['data'])
                if not os.path.exists(output_folder+"/"+str(task_id)):
                    os.makedirs(output_folder+"/"+str(task_id))
                tmp_base_name = os.path.splitext(i)[0]
                tmp_ext = os.path.splitext(i)[1]
                image.save(output_folder+"/"+str(task_id)+"/"+tmp_base_name+"_"+str(amount)+tmp_ext)

        print(f"Task ID: {task_id} is completed")
exit()
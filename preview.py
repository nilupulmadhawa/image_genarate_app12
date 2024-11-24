import cv2
import os
import json
from PIL import Image, ImageDraw, ImageFont # type: ignore
import datetime
import numpy as np
from googletrans import Translator
import random
import locale

click_count = 0
positions = []
font_folder = './fonts'
time_slot = datetime.datetime(2024, 11, 14, 15, 30)  # Sample date and time


img ="Depo(8)"


processed_images_json_path = './processed_images.json'  # File to store names of processed images

# Load processed images from the previous run
if os.path.exists(processed_images_json_path):
    with open(processed_images_json_path, 'r') as f:
        processed_images = json.load(f)
else:
    processed_images = []

def draw_image(draw, time_slot, amount, data):
    for item in data:
        # attr=item['attr']
        attr_type = item['attr_type']
        x = item['x']
        y = item['y']
        font_path = item['font']
        align = item['align']
        size = item['size']
        color = item['color']
        format = item['format']
        underline = item['underline'] if 'underline' in item else False
        language = item['language'] if 'language' in item else 'en'
        underline_margin = item['underline_margin'] if 'underline_margin' in item else 10
        time_pre_language = item['time_pre_language'] if 'time_pre_language' in item else 'en'
        txt = item['text'] if 'text' in item else ''
        pre_text = item['pre_text'] if 'pre_text' in item else ''
        post_text = item['post_text'] if 'post_text' in item else ''

        # Choose the font
        font = ImageFont.truetype(font_folder+"/"+font_path, size)


        # Format the text based on the attribute
        if attr_type == 'number':
            text = format.format(amount)
        elif attr_type == 'datetime':
            text = time_slot.strftime(format)
        else:
            text = txt

        #language selection
        if language != "en" and text:  # Only translate if there's text to translate
            try:
                translator = Translator()
                print(f"Original text: {text}")
                translated_text = translator.translate(str(text), dest=language)
                text = translated_text.text
                print(f"Translated text: {text}")
                if time_pre_language == "ar":
                    am_pm_map = {"AM": "ص", "PM": "م"}
                    text = text.replace("AM", am_pm_map["AM"]).replace("PM", am_pm_map["PM"])
            except Exception as e:
                print(f"Error during translation: {e}")
                # Handle error, fallback to original text
                exit()
        
        if pre_text:
            text = pre_text + text
        if post_text:
            text = text + post_text

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        # Draw the text on the image
        y -= text_height +5

        if align == "center":
            x -= text_width // 2
        elif align == "right":
            x -= text_width
        # elif align == "left":
        #     x +=text_width

        # Draw the text on the image at the specified position
        draw.text((x, y), text, font=font, fill=color)

        if underline:
            draw.line((x, y + text_height+underline_margin, x + text_width, y + text_height+underline_margin), fill=color, width=2)

    return draw

def preview_positions(image_path, json_data):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    amount_digits_max =json_data['amount_digits_max']
    amount_digits_min =json_data['amount_digits_min']

    min_value = 10**(amount_digits_min - 1)
    max_value = 10**amount_digits_max - 1

    amount = random.randint(min_value, max_value)
    draw = draw_image(draw, time_slot, amount, json_data['data'])
    # preview_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    # cv2.imshow("Preview", preview_image)
    image.show(title="Preview")




# Main processing loop for images
templates_path = './templates/'
json_path = './templates/'+img+'.json'
with open(json_path, 'r') as f:
        json_data = json.load(f)
preview_positions(templates_path + '/'+img+'.png', json_data)


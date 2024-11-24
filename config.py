import cv2
import os
import json
from PIL import Image, ImageDraw, ImageFont # type: ignore
import datetime
import numpy as np
from googletrans import Translator
import random


click_count = 0
positions = []
font_folder = './fonts'
time_slot = datetime.datetime(2024, 11, 14, 15, 30)  # Sample date and time
# amount = 123.56  # Sample amount

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
        underline = item['underline']
        language = item['language']
        # Choose the font
        font = ImageFont.truetype(font_folder+"/"+font_path, size)


        # Format the text based on the attribute
        if attr_type == 'number':
            text = format.format(amount)
        elif attr_type == 'datetime':
            text = time_slot.strftime(format)
        else:
            text = ""

        #language selection
        if language != "en" and text:  # Only translate if there's text to translate
            try:
                translator = Translator()
                print(f"Original text: {text}")
                translated_text = translator.translate(str(text), dest=language)
                text = translated_text.text
                print(f"Translated text: {text}")
            except Exception as e:
                print(f"Error during translation: {e}")
                # Handle error, fallback to original text
                exit()

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
            draw.line((x, y + text_height+10, x + text_width, y + text_height+10), fill=color, width=2)

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

# Click event function
def click_event(event, x, y, flags, param):
    global click_count
    json_data = param  # Access json_data directly from the passed parameter
    # Check if Ctrl is held down and left mouse button is clicked
    if event == cv2.EVENT_LBUTTONDOWN:  # Only capture when mouse moves
        temp_img = img.copy()  # To keep the original image unmodified
        text = f"X: {x}, Y: {y}"
        #draw line x y remove old line
        cv2.line(temp_img, (0, y), (temp_img.shape[1], y), (0, 255, 0), 1)
        cv2.line(temp_img, (x, 0), (x, temp_img.shape[0]), (0, 255, 0), 1)
        cv2.putText(temp_img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("Select Positions", temp_img)
        
    if event == cv2.EVENT_LBUTTONDOWN and (flags & cv2.EVENT_FLAG_CTRLKEY):
        if click_count < len(json_data['data']):  # Ensure we only capture required clicks
            data = json_data['data'][click_count]
            data['x'] = x
            data['y'] = y
            print(f"Position selected for {data['attr']} at: ({x}, {y})")
            click_count += 1
            if click_count < len(json_data['data']):
                print(f"Please select the position for {json_data['data'][click_count]['attr']}.")
        else:
            print("Hold the Ctrl key and click to select the next position.")

# Function to process each image and get positions
def process_image(image_path, json_data):
    global click_count, img
    click_count = 0  # Reset click count for each image
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error loading image: {image_path}")
        return None  # Skip if image loading fails

    print(f"Please select the position for {json_data['data'][click_count]['attr']}.")
    cv2.imshow("Select Positions", img)
    cv2.setMouseCallback("Select Positions", click_event, param=json_data)

    while click_count < len(json_data['data']):
        key = cv2.waitKey(1)
        
        # Break if 'q' is pressed or if the window is closed
        if key == ord('q') or cv2.getWindowProperty("Select Positions", cv2.WND_PROP_VISIBLE) < 1:
            print("Exiting position selection early.")
            break
            
    cv2.destroyAllWindows()  # Close window once done or user exits
    
    if click_count == len(json_data['data']):
        preview_positions(image_path, json_data)
        confirm = input("Are the positions correct? (y/n): ").strip().lower()
        return json_data['data'] if confirm == 'y' else None
    return None

# Main processing loop for images
templates_path = './templates'
for filename in os.listdir(templates_path):
    if filename.endswith(('.png', '.jpg', '.jpeg')) and filename not in processed_images:
        image_path = os.path.join(templates_path, filename)
        print(f"Processing {filename}...")
        
        # Check for JSON file corresponding to the image
        file_base_name = os.path.splitext(filename)[0]
        json_path = os.path.join(templates_path, file_base_name + '.json')
        if not os.path.exists(json_path):
            print(f"Error: JSON file not found for {filename}")
            continue
        
        # Load the JSON file with positions
        with open(json_path, 'r') as f:
            json_data = json.load(f)

        while True:
            updated_positions = process_image(image_path, json_data)
            if updated_positions:
                # Save the updated JSON
                with open(json_path, 'w') as f:
                    json.dump(json_data, f, indent=4)
                print(f"Updated positions saved for {filename}")
                processed_images.append(filename)
                break
            else:
                print(f"Re-running selection for {filename}...")


# Update the processed images file to avoid repeat selections in future runs
with open(processed_images_json_path, 'w') as f:
    json.dump(processed_images, f, indent=4)

print("Processing complete. Positions saved individually for each image.")
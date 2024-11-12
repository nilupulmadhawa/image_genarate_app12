import cv2
import os
import json
from PIL import Image, ImageDraw, ImageFont # type: ignore
import numpy as np

# Folder paths
folder_path = './templates'  # Folder containing images
output_folder = './processed_images'  # Output folder for images with text

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Sample data to be added
amount_text = "9,200"  # Sample amount value
date_text = "04 JAN 2024 13:55 PM"  # Sample date value

# Function to add text based on JSON settings
def add_text_to_image(image_path, json_path):
    # Load JSON settings for the image
    with open(json_path, 'r') as f:
        positions = json.load(f)
    
    # Load the image with OpenCV, then convert it to a format compatible with PIL
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error loading image: {image_path}")
        return
    
    # Convert OpenCV image (BGR) to PIL image (RGB)
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)

    # Helper function to draw text on the image with Pillow
    def draw_text(text, settings):
        x = settings['x']
        y = settings['y']
        font_path = settings['font']
        font_size = settings['size']
        color = settings['color']
        alignment = settings['align']

        # Load the font file with Pillow
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Font file not found: {font_path}. Using default font.")
            font = ImageFont.load_default()
        
        # Get text size using textbbox for alignment purposes
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Adjust alignment if specified
        if alignment == "center":
            x -= text_width // 2
        elif alignment == "right":
            x -= text_width
        elif alignment == "left":
            x +=text_width

        # Draw the text
        draw.text((x, y), text, font=font, fill=color)

    # Draw amount text
    if 'amount' in positions:
        draw_text(amount_text, positions['amount'])

    # Draw date text
    if 'date' in positions:
        draw_text(date_text, positions['date'])

    output_path = os.path.join(output_folder, os.path.basename(image_path))
    image_pil.save(output_path)
    print(f"Image with text saved to: {output_path}")

# Process each image and its corresponding JSON file
for filename in os.listdir(folder_path):
    if filename.endswith(('.png', '.jpg', '.jpeg')):
        image_path = os.path.join(folder_path, filename)
        json_path = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}.json")
        
        if os.path.exists(json_path):
            print(f"Adding text to {filename} based on {json_path}...")
            add_text_to_image(image_path, json_path)

import cv2
import os
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Path to the folder containing images
folder_path = './templates'  # Folder containing images
processed_images_path = './processed_images.json'  # File to store names of processed images

font_align = "right"
font_path = "C:/Users/Acer/Desktop/font/ARIAL.TTF"
color = "#000000"
date_format = "%Y-%m-%d"
amount_font_size = 40  
date_font_size = 15

# Load processed images from the previous run
if os.path.exists(processed_images_path):
    with open(processed_images_path, 'r') as f:
        processed_images = json.load(f)
else:
    processed_images = []

def click_event(event, x, y, flags, param):
    global positions, click_count, image
    # Capture click event
    if event == cv2.EVENT_LBUTTONDOWN:
        if click_count == 0:
            print("Please select the 'Amount' position first.")
            positions['amount']['x'] = x
            positions['amount']['y'] = y
            print(f"Amount position selected at: ({x}, {y})")
            click_count += 1
        elif click_count == 1 and (flags & cv2.EVENT_FLAG_CTRLKEY):  # Allow only if Ctrl is held
            print("Now, please select the 'Date' position by holding Ctrl and clicking.")
            positions['date']['x'] = x
            positions['date']['y'] = y
            print(f"Date position selected at: ({x}, {y})")
            click_count += 1
            display_positions(image)  # Show preview after both positions are selected
        elif click_count == 1:
            print("Hold the Ctrl key and click to select the 'Date' position.")

def display_positions(image):
    # Function to display the image with the selected text preview
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))  # Convert to RGB for PIL
    draw = ImageDraw.Draw(pil_image)

    # Load fonts with specified sizes for amount and date
    amount_font = ImageFont.truetype(font_path, positions['amount']['size'])
    date_font = ImageFont.truetype(font_path, positions['date']['size'])
    x =positions['amount']['x']

    # Draw preview text at the selected positions with different font sizes
    draw.text((positions['amount']['x'], positions['amount']['y']), "1,200", font=amount_font, fill=color,align=font_align)
    draw.text((positions['date']['x'], positions['date']['y']), "07 Nov 2024 12:55 PM", font=date_font, fill=color,align=font_align)

    # Convert back to OpenCV format and show the preview
    preview_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    cv2.imshow("Preview", preview_image)
    
    # Add waitKey to hold the preview open until a key is pressed
    cv2.waitKey(1)

    # Ask user if the preview is correct
    response = input("Is the selection correct? (y/n): ")
    cv2.destroyWindow("Preview")  # Close the preview window after key press
    return response.strip().lower() == 'y'

def process_image(image_path):
    global positions, click_count, image
    while True:  # Loop until correct selection is confirmed
        click_count = 0

        # Initialize positions with default values and specific font sizes
        positions = {
            "amount": {
                "x": 0,
                "y": 0,
                "align": font_align,
                "font": font_path,
                "size": amount_font_size,  # Font size for amount
                "color": color
            },
            "date": {
                "x": 0,
                "y": 0,
                "align": font_align,
                "font": font_path,
                "size": date_font_size,    # Font size for date
                "color": color,
                "format": date_format
            }
        }
        
        # Display instructions to the user
        print("\nInstructions:")
        print("1. First, select the 'Amount' position by clicking once.")
        print("2. Then, hold the Ctrl key and click to select the 'Date' position.\n")
        
        # Load and display the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error loading image: {image_path}")
            return None  # Skip this image if loading fails

        cv2.imshow("Select Amount and Date Positions", image)
        cv2.setMouseCallback("Select Amount and Date Positions", click_event)

        # Wait until positions for amount and date are selected
        while click_count < 2:
            cv2.waitKey(1)

        cv2.destroyWindow("Select Amount and Date Positions")  # Close the selection window after finishing

        # Display the preview and ask for confirmation
        if display_positions(image):
            break  # Exit loop if selection is correct

    return positions

# Loop through all images in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(('.png', '.jpg', '.jpeg')) and filename not in processed_images:
        image_path = os.path.join(folder_path, filename)
        print(f"Processing {filename}...")

        # Get positions for the current image
        positions = process_image(image_path)
        if positions is None:
            continue  # Skip if the image could not be processed
        
        # Save the positions in a separate JSON file for each image
        output_file = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}.json")
        with open(output_file, 'w') as f:
            json.dump(positions, f, indent=4)
        print(f"Positions for {filename} saved to {output_file}")

        # Mark the image as processed
        processed_images.append(filename)

# Update the processed images file to avoid repeat selections in future runs
with open(processed_images_path, 'w') as f:
    json.dump(processed_images, f, indent=4)

print("Processing complete. Positions saved individually for each image.")

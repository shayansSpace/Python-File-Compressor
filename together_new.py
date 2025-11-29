import FreeSimpleGUI as sg              # pip install FreeSimpleGUI
import numpy as np                      # pip install numpy
from PIL import Image                   # pip install pillow
import os
import io
from timeit import default_timer as timer

def display_img(path, string):
    try:
        # Open the image with PIL
        img = Image.open(path).convert("RGB")

        # Resize if too large (optional, keeps window manageable)
        img.thumbnail((1280,720))

        # Convert to bytes for PySimpleGUI
        with io.BytesIO() as bio:
            img.save(bio, format="PNG")
            img_bytes = bio.getvalue()

        # Create a new window to display image
        img_layout = [[sg.Image(data=img_bytes)]]
        img_window = sg.Window(f'{string} Image', img_layout, modal=True)

        while True:
            img_event, img_values = img_window.read()
            if img_event == sg.WIN_CLOSED:
                break
        img_window.close()

    except Exception as e:
        window['-STATUS-'].update(f"❌ Error opening {string} image: {str(e)}", text_color='red')

BLOCK_SIZES = ['2', '4', '8', '16', '32']
DEFAULT_BLOCK_SIZE = '4'
COMPRESSION_MIN = 100
COMPRESSION_MAX = 2500
COMPRESSION_DEFAULT = 1000

# Define the common image formats
IMAGE_FILE_TYPES = (
    ("All Image Files", "*.jpg *.jpeg *.png *.gif *.bmp"),
    ("JPEG Files", "*.jpg *.jpeg"),
    ("PNG Files", "*.png"),
    ("GIF Files", "*.gif"),
    ("BMP Files", "*.bmp"),
    ("All Files", "."),
)


layout = [
    [sg.Text('Image to Compress:', size=(15,1)),
     sg.Input(key = '-INPUT-FILE-', size = (50,1)),
     sg.FileBrowse(file_types=(IMAGE_FILE_TYPES))],

     [sg.Text('Name of the\nCompressed Image:', size=(15,2)),
      sg.Input(key = '-OUTPUT-FILE-', size = (50,1))],

     [sg.Text('Save to Folder:', size=(15, 1)),
      sg.Input(key = '-OUTPUT-DIR-', size = (50,1), default_text= os.getcwd()),
      sg.FolderBrowse()],

      [sg.Text('\nVariance Threshold:', size=(15, 2)),
        sg.Slider(range=(COMPRESSION_MIN, COMPRESSION_MAX),
            default_value=COMPRESSION_DEFAULT,
            orientation='horizontal',
            size=(46, 15),
            key='-SLIDER-STRENGTH-',
            enable_events=True, 
            tooltip='Set the variance threshold for smart downsampling.')],
        
        [sg.Text('Block Size (N x N):', size=(15, 1)),
        sg.Combo(BLOCK_SIZES,
            default_value=DEFAULT_BLOCK_SIZE,
            key='-BLOCK-SIZE-',
            readonly=True,  # Prevents users from typing invalid values
            tooltip='Size of the pixel block for variance check (e.g., 4 means 4x4).'),
        sg.Text('(Pixels to average if similar)', size=(25, 1))],

       [sg.Button('Compress', size = (10,1), key= '-COMPRESS-', button_color = 'darkblue'),
        sg.Text('', size = (35,1), key = '-STATUS-')],

        [sg.ProgressBar(key='-PROGRESS-',
                        max_value=100,
                        orientation='horizontal',
                        size=(50,6),
                        bar_color='green',
                        visible=False)],
        [sg.Text('', size = (48,1), key = '-ORIGINAL-'), 
         sg.Button('View Original Image', key = '-ORIGINAL-BUTTON-', size=(18,1))],

        [sg.Text('', size = (48,1), key = '-COMPRESSED-'),
         sg.Button('View Compressed Image', size=(18,1), visible=False, key = '-COMP-BUTTON-')],

        [sg.Text('', key = '-TIME-', size = (61,1)), sg.Button('Exit', size = (5,1))]
]

window = sg.Window('Simple File Compressor', layout)

while True:
    event, values = window.read()
    
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    
    if event == '-ORIGINAL-BUTTON-':
        input_file = values['-INPUT-FILE-']

        if os.path.exists(input_file):
            display_img(input_file, 'Original')
        else:
            window['-STATUS-'].update('❌ Error: Please select a valid file first.', text_color='red')

    if event == '-COMP-BUTTON-':
        output_file = values['-OUTPUT-FILE-']
        output_folder = values['-OUTPUT-DIR-']
        output_path = os.path.join(output_folder, output_file + '.jpg')

        if os.path.exists(output_path):
            display_img(output_path, 'Compressed')
        else:
            window['-STATUS-'].update('❌ Error: Please compress a file first.', text_color='red')
            
    if event == '-COMPRESS-':
        input_file = values['-INPUT-FILE-']
        output_file = values['-OUTPUT-FILE-']
        output_folder = values['-OUTPUT-DIR-']
        #----------
        if not input_file:
            window['-STATUS-'].update('❌ Error: Please select a file first.', text_color='red')
            continue

        if not output_file:
            window['-STATUS-'].update('❌ Error: Please name the compressed file.', text_color='red')
            continue

        output_path = os.path.join(output_folder, output_file + '.jpg')
        # created a new alert window other than layout
        if os.path.exists(output_path):
            message_layout = [[sg.Text(f'{output_file}.jpg already exists.\nDo you want to overwrite this file?',
                                        size = (30,2), text_color= 'black', background_color='white')],
                            [sg.Button('Overwrite', size = (9,1)), sg.Text('', size = (8,1), background_color='white'), sg.Button('Cancel',
                                        size=(9,1))]]
            message_window = sg.Window('⚠️ Warning!', message_layout, background_color='white')
            overwrite = 0
            while True:
                message_event, message_values =  message_window.read()
                if message_event == sg.WIN_CLOSED or message_event == 'Cancel':
                    break #exit this while loop and implement the compression
                else:
                    overwrite = 1
                    break
            message_window.close()
            if not overwrite:
                continue #don't compress, start the main while loop again
        

        block_size = int(values['-BLOCK-SIZE-'])
        variance_threshold = int(values['-SLIDER-STRENGTH-'])

        #--------------------
        #For beautification
        window['-ORIGINAL-'].update('')
        window['-COMPRESSED-'].update('')
        window['-TIME-'].update('')
        window['-COMP-BUTTON-'].update(visible=False)
        window['-COMPRESS-'].update(button_color = 'grey')

        try:
            window['-STATUS-'].update(f'Compressing {os.path.basename(input_file)}...', text_color='yellow')
            window['-PROGRESS-'].update(visible=True)
            start_time = timer()
            img = Image.open(input_file).convert("RGB")
            img_array = np.array(img, dtype=np.float32)
            H, W, C = img_array.shape

            # Ensure dimensions are multiples of block_size for simpler processing (crop any edges)
            H = H - (H % block_size)
            W = W - (W % block_size)
            img_array = img_array[:H, :W, :]

            # Create an output array of the same shape to overwrite blocks
            output_array = np.copy(img_array)

            # 1. Iterate over the image in blocks
            for i in range(0, H, block_size):
                for j in range(0, W, block_size):
                    block = img_array[i:i+block_size, j:j+block_size, :]
                    color_variance = np.var(block) 

                    if color_variance < variance_threshold:
                        # Case 1: Low Variance (Compress the block)
                        # Calculate the average color of the block.
                        avg_pixel = np.mean(block, axis=(0, 1))
                    
                        # Fill the entire block in the output array with the single average color.
                        # This is quantization, not resolution change, but it simplifies the data for compression.
                        output_array[i:i+block_size, j:j+block_size, :] = avg_pixel
                
                    # Case 2 (High Variance): If variance is high, the block in output_array remains unchanged 
                    # (since output_array was a copy of img_array).
                progress = int(100 * i / H)
                window['-PROGRESS-'].update(progress)

            # 2. Convert back to image, cast to 8-bit, and save.
            output_array = output_array.astype(np.uint8)
            processed_img = Image.fromarray(output_array)
        
            # Save as JPEG with high compression (low quality) to leverage the simplified data
            processed_img.save(output_path, quality=50, optimize=True)
            window['-PROGRESS-'].update(100)

            #view original
            window['-ORIGINAL-'].update(f"Original size: {os.path.getsize(input_file) / 1024:.2f} KB", text_color='orange')
            


            # window['-COMPRESSED-']
            window['-COMPRESSED-'].update(f"Compressed size: {os.path.getsize(output_path) / 1024:.2f} KB", text_color='lightgreen')
            window['-COMP-BUTTON-'].update(visible=True)

            end_time = timer()
            total_time = round(end_time - start_time, 2)
        except Exception as e:
            print(f"An error occurred: {e}")
        #--------------------
        window['-COMPRESS-'].update(button_color = 'darkblue')
        window['-STATUS-'].update(f'✅ Compression of {os.path.basename(input_file)} Finished!', text_color='lightgreen')
        window['-TIME-'].update(f'Time elapsed: {total_time} seconds')

window.close()
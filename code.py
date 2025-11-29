from timeit import default_timer as timer   # module for timing the duration of compression processss
import FreeSimpleGUI as sg                  # module for creation of GUI (must be installed)
import numpy as np                          # module for quick calculations (must be installed)
from PIL import Image                       # module for image manipulation ("pillow" must be installed)
import os                                   # module for handling file paths
import io                                   # module for reading bytes of an image

def display_img(path, string):
    try:
        # Open the image with PIL
        img = Image.open(path).convert("RGB") #opens the image and converts it to RGB format

        # Resize if the image is too large
        img.thumbnail((1280,720))

        # Converts the image to bytes
        with io.BytesIO() as bio:       # converts all the pixels into bytes and saves them in an array so we can iterate over them and compress them
            img.save(bio, format="PNG")
            img_bytes = bio.getvalue()

        # Create a new window to display image
        img_layout = [[sg.Image(data=img_bytes)]]
        img_window = sg.Window(f'{string} Image', img_layout, modal=True)

        while True:
            img_event, img_values = img_window.read()
            if img_event == sg.WIN_CLOSED:  # if the user presses the windows clos button (cross on the top right) this loop breaks
                break
        img_window.close() #window closes

    except Exception as e:
        window['-STATUS-'].update(f"❌ Error opening {string} image: {str(e)}", text_color='red') # if image is corrupted this error msg is displayed

BLOCK_SIZES = ['2', '4', '8', '16', '32']   # set of block size choices provided to the user
DEFAULT_BLOCK_SIZE = '4'
COMPRESSION_MIN = 100
COMPRESSION_MAX = 2500
COMPRESSION_DEFAULT = 500

# The common image formats to be displayed in the file explorer
IMAGE_FILE_TYPES = (
    ("All Image Files", "*.jpg *.jpeg *.png *.gif *.bmp"),
    ("JPEG Files", "*.jpg *.jpeg"),
    ("PNG Files", "*.png"),
    ("GIF Files", "*.gif"),
    ("BMP Files", "*.bmp"),
    ("All Files", "*.*"),
)

# defines the layout of the main GUI window
# layout is a 2D list where each GUI elemnt is in a specific row and column
layout = [
    [sg.Text('Image to Compress:', size=(15,1)),
     sg.Input(key = '-INPUT-FILE-', size = (50,1)), # here the user will provide the path of the image to be compressesd
     sg.FileBrowse(file_types=(IMAGE_FILE_TYPES))],

     [sg.Text('Name of the\nCompressed Image:', size=(15,2)),
      sg.Input(key = '-OUTPUT-FILE-', size = (50,1))],  #here the user will enter a name for the compressed file

     [sg.Text('Save to Folder:', size=(15, 1)),
      sg.Input(key = '-OUTPUT-DIR-', size = (50,1), default_text= os.getcwd()), # here the user will provide the path of the compressed image
      sg.FolderBrowse()],

    # Here the user will define how similar the adjacent pixels must be to compress them
      [sg.Text('\nVariance Threshold:', size=(15, 2)),
        sg.Slider(range=(COMPRESSION_MIN, COMPRESSION_MAX), # A user-friendly way to select the variance
            default_value=COMPRESSION_DEFAULT,
            orientation='horizontal',
            size=(46, 15),
            key='-SLIDER-STRENGTH-',
            enable_events=True, 
            tooltip='Set the variance threshold for smart downsampling.')],

        # here the user will define how many pixels must be checked and compressed into single pixel, per iteration
        [sg.Text('Block Size (N x N):', size=(15, 1)),
        sg.Combo(BLOCK_SIZES,   # A user-friendly way of selecting block sizes
            default_value=DEFAULT_BLOCK_SIZE,
            key='-BLOCK-SIZE-',
            readonly=True,  # Prevents users from typing invalid values
            tooltip='Size of the pixel block for variance check (e.g., 4 means 4x4).'),
        sg.Text('(Pixels to average if similar)', size=(25, 1))],

       [sg.Button('Compress', size = (10,1), key= '-COMPRESS-', button_color = 'darkblue'),
        sg.Text('', size = (50,1), key = '-STATUS-')],  #this textbox shows the status of compression

        # A progress bar to indicate the compresssion is in progress
        # without a progress bar it may look like the program has stopped responding as our code cannot exit when compression is in progress
        [sg.ProgressBar(key='-PROGRESS-',
                        max_value=100,
                        orientation='horizontal',
                        size=(42,6),    # length of progress bar
                        bar_color='green',
                        visible=False)],    # This line ensures progress bar is only visible after compression begins
        [sg.Text('', size = (48,1), key = '-ORIGINAL-'),
         sg.Button('View Original Image', key = '-ORIGINAL-BUTTON-', size=(18,1))],     # the button for viewing the original image

        [sg.Text('', size = (48,1), key = '-COMPRESSED-'),
         sg.Button('View Compressed Image', size=(18,1), visible=False, key = '-COMP-BUTTON-')],    #the button for viewing the compressed image

        [sg.Text('', key = '-TIME-', size = (61,1)), sg.Button('Exit', size = (5,1))]   # time for the image to be compressed
]

window = sg.Window('Smart Image Compressor', layout)    #The main GUI window is created here

while True:
    event, values = window.read()   #this is the event listener of the GUI
                                    #each GUI element has a value and a unique key

    if event == sg.WIN_CLOSED or event == 'Exit':   # the way to close the program
        break
    
    if event == '-ORIGINAL-BUTTON-':    # button to display original image
        input_file = values['-INPUT-FILE-'] # read the name of the file

        if os.path.exists(input_file):   # checks if input file exists
            display_img(input_file, 'Original') #opens the image for the user to ssee
        else:
            window['-STATUS-'].update('❌ Error: Please select a valid file first.', text_color='red')

    if event == '-COMP-BUTTON-':    # button to display compressed image
        output_file = values['-OUTPUT-FILE-']   # read the name of the output image
        output_folder = values['-OUTPUT-DIR-']  # checks the selected folder
        output_path = os.path.join(output_folder, output_file + '.jpg') #creates the output path

        if os.path.exists(output_path):  # checks if output file exists
            display_img(output_path, 'Compressed') # opens the compressed image for the user to see
        else:
            window['-STATUS-'].update('❌ Error: Please compress a file first.', text_color='red')
            
    if event == '-COMPRESS-':   # when the user presses the compress button
        input_file = values['-INPUT-FILE-']
        output_file = values['-OUTPUT-FILE-']
        output_folder = values['-OUTPUT-DIR-']
        #----------
        if not input_file:  # checks if the user has selected a file to compress
            window['-STATUS-'].update('❌ Error: Please select a file first.', text_color='red')
            continue

        if not output_file: # checks if the user has named the compressed file
            window['-STATUS-'].update('❌ Error: Please name the compressed file.', text_color='red')
            continue

        output_path = os.path.join(output_folder, output_file + '.jpg')
        # the code to alert the user that a file with the same name exists (uses a new GUI window)
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
        

        block_size = int(values['-BLOCK-SIZE-'])    #reads the block size
        variance_threshold = int(values['-SLIDER-STRENGTH-'])   #reads the variance threshold

        #--------------------
        #flushes the previous image information if a new image begins compression
        window['-ORIGINAL-'].update('')
        window['-COMPRESSED-'].update('')
        window['-TIME-'].update('')
        window['-COMP-BUTTON-'].update(visible=False)
        window['-COMPRESS-'].update(button_color = 'grey')

        # MAIN COMMPRESSION
        try:
            window['-STATUS-'].update(f'Compressing {os.path.basename(input_file)}...', text_color='yellow')
            window['-PROGRESS-'].update(visible=True)   #as the image is being compressed the progress bar becomes visible
            start_time = timer()    #to calculate the time taken
            img = Image.open(input_file).convert("RGB") #opens the image and converts it to RGB format
            img_array = np.array(img, dtype=np.float32) #converts the image into a numpy array
            H, W, C = img_array.shape   #assigns the 3 dimensions of the 3D image array to 3 separate variables

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

            original_size = os.path.getsize(input_file)
            comp_size = os.path.getsize(output_path)
            comp_strength = round((1 - (comp_size/original_size)) * 100)    # percentage

            # view original image
            window['-ORIGINAL-'].update(f"Original size: {original_size / 1024:.2f} KB", text_color='orange')

            # view compressed image
            window['-COMPRESSED-'].update(f"Compressed size: {comp_size / 1024:.2f} KB (-{comp_strength}%)", text_color='lightgreen')
            window['-COMP-BUTTON-'].update(visible=True)    #makes the button visible once the compression is done

            end_time = timer()  # to calculate the time taken for the image to be compressed
            total_time = round(end_time - start_time, 2)    # calculates the time taken and rounds to 2 dp
        except Exception as e:
            print(f"An error occurred: {e}")    # this error msg is displayed if anything goes wrong
        #--------------------
        window['-COMPRESS-'].update(button_color = 'darkblue')
        window['-STATUS-'].update(f'✅ Compression of {os.path.basename(input_file)} Finished!', text_color='lightgreen')
        window['-TIME-'].update(f'Time elapsed: {total_time} seconds')  #displays the time taken by the compression

window.close()  #closses the window
#Hope you like it
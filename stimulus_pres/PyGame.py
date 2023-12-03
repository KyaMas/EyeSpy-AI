# PyGame

import UnicornPy
import pygame
import time
import os
import random
import numpy as np
import shutil
from pygame.locals import *

# Set up window, text, and font information
WINDOWWIDTH = 600
WINDOWHEIGHT = 600
TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (0, 0, 0)
FrameLength = 1

def waitForPlayerToPressKey():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                return

def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, TEXTCOLOR)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)


def limitConsoleUpdateRate():
    """
    """
    consoleUpdateRate = int((UnicornPy.SamplingRate / FrameLength) / 25.0)
    if consoleUpdateRate == 0:
        consoleUpdateRate = 1
    return consoleUpdateRate

# Function to get image filenames from a directory
def get_image_filenames(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg')]

# Set up pygame, screen, and clock
pygame.init()
clock = pygame.time.Clock()
windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), 0, 32)
pygame.display.set_caption('Combined Image Slideshow and Unicorn BCI')

# Set up fonts
font = pygame.font.SysFont(None, 48)

# Get image filenames for both "ai_images" and "real_images"
ai_image_filenames = get_image_filenames('ai_images')
real_image_filenames = get_image_filenames('real_images')

# Combine the two lists
image_filenames = ai_image_filenames + real_image_filenames

# Number of repetitions for image slideshow
num_repetitions = 4

# Show the "Start" screen for image slideshow
drawText('Welcome to the combined script!',
         font,
         windowSurface,
         (WINDOWWIDTH / 2),
         (WINDOWHEIGHT / 5))
drawText('Press any key to start the slideshow.',
         font,
         windowSurface,
         (WINDOWWIDTH / 2),
         (WINDOWHEIGHT / 2) + 50)

# Update display
pygame.display.update()
waitForPlayerToPressKey()

# Clear the screen for image slideshow
windowSurface.fill(BACKGROUNDCOLOR)
pygame.display.flip()

# Open device for Unicorn BCI
deviceList = UnicornPy.GetAvailableDevices(True)
device = UnicornPy.Unicorn(deviceList[0])
file = None  # Placeholder for the data file, will be opened later

# Acquisition must be started to create handle for GetNumberOfAcquiredChannels()
TestSignalEnabled = False
device.StartAcquisition(TestSignalEnabled)
numberOfAcquiredChannels = device.GetNumberOfAcquiredChannels()

# Create buffer for Unicorn BCI
receiveBufferBufferLength = FrameLength * numberOfAcquiredChannels * 4
receiveBuffer = bytearray(receiveBufferBufferLength)

# Main acquisition loop for Unicorn BCI
user_duration = 2  # image display duration (in seconds)

for i in range(0, int(user_duration * UnicornPy.SamplingRate / FrameLength)):
    #device.GetData(FrameLength, receiveBuffer, receiveBufferBufferLength)
    #data = np.frombuffer(receiveBuffer, dtype=np.float32, count=numberOfAcquiredChannels * FrameLength)
    #data = np.reshape(data, (FrameLength, numberOfAcquiredChannels))

    # Open the file if it's not opened yet
    if file is None:
        ts = time.time()
        dataFile = '../data/recordings/combined_recording_' + str(int(ts)) + '.csv'
        os.makedirs(os.path.dirname(dataFile), exist_ok=True)
        file = open(dataFile, "ab")

    # Save Unicorn BCI data to csv
    #np.savetxt(file, data, delimiter=',', fmt='%.3f', newline='\n')

    #if i % limitConsoleUpdateRate() == 0:
    #    print(str(i) + " samples so far for Unicorn BCI.")

# Image slideshow loop
device.GetData(FrameLength, receiveBuffer, receiveBufferBufferLength)
data = np.frombuffer(receiveBuffer, dtype=np.float32, count=numberOfAcquiredChannels * FrameLength)
data = np.reshape(data, (FrameLength, numberOfAcquiredChannels))
bci_time = time.perf_counter()
row_data = np.append(data, [[bci_time]], 1)
np.savetxt(file, row_data, delimiter=',', fmt='%s', newline='\n')

for repetition in range(num_repetitions):
    random.shuffle(image_filenames)

    for idx, image_filename in enumerate(image_filenames):
        image_path = os.path.join(image_filename)  # Assuming images are in a folder named 'images'
        image = pygame.image.load(image_path)
        image = pygame.transform.scale(image, (WINDOWWIDTH, WINDOWHEIGHT))

        device.GetData(FrameLength, receiveBuffer, receiveBufferBufferLength)
        data = np.frombuffer(receiveBuffer, dtype=np.float32, count=numberOfAcquiredChannels * FrameLength)
        data = np.reshape(data, (FrameLength, numberOfAcquiredChannels))

        windowSurface.blit(image, (0, 0))
        pygame.display.flip()

        picture_time = time.perf_counter()
        print(f"{picture_time} - Presented: {image_filename}")

        current_image_type = 0 if 'real' in image_filename else 1

        row_data = np.append(data, [[bci_time,current_image_type, image_filename, picture_time]], 1)
        np.savetxt(file, row_data, delimiter=',', fmt='%s', newline='\n')

        # Collect Unicorn BCI data for the duration of image presentation
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < 2:  # 2 seconds for image presentation
            device.GetData(FrameLength, receiveBuffer, receiveBufferBufferLength)
            data = np.frombuffer(receiveBuffer, dtype=np.float32, count=numberOfAcquiredChannels * FrameLength)
            data = np.reshape(data, (FrameLength, numberOfAcquiredChannels))

            bci_time = time.perf_counter()
            row_data = np.append(data, [[bci_time]], 1)
            np.savetxt(file, row_data, delimiter=',', fmt='%s', newline='\n')

        time.sleep(1)

        windowSurface.fill(BACKGROUNDCOLOR)
        pygame.display.flip()

        # Handle events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
    #pygame.quit()


# Stop data acquisition for Unicorn BCI
device.StopAcquisition()
print()
print("Unicorn BCI data acquisition stopped.")
del receiveBuffer
if file is not None:
    file.close()

# End of the script
drawText('Combined Script Complete. Press any key to quit.',
         font,
         windowSurface,
         (WINDOWWIDTH / 2),
         (WINDOWHEIGHT / 5))
pygame.display.update()
waitForPlayerToPressKey()
pygame.quit()

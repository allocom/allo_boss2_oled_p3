import smbus
import time
from PIL import Image
import traceback
from .SH1106FontLib import *
from .Line1SH1106FontLib import *
from .SH1106FontLib1 import *
from .SH1106FontLibNumbers import *
from .SH1106FontLibNumbers1 import *
import os


"""
  Class SH1106LCD()
  
  Interface to the SH1106 LCD that will be displaying the current
  gear selection.  The SH1106 LCD is a 132x64 pixel OLED display.
  Data is displayed on the LCD by alterting the data in the Display
  Data RAM.  The RAM contains a set of bits that correspond to the
  individual pixels of the LCD display. It holds the data in pages 
  and columns.  Their are 8 pages, each representing 8 rows (making up 
  the 64 bit height).  There are 132 columns in each page.  Each page
  is stored as a set of 132 bytes.  The 8 bits of each byte represent
  one of the 8 rows in that page as shown below. The least significant
  bit (D0) represents the top-most row of the page.  The most
  significant bit (D7) represents the bottom-most row of the page.
 
  Changes to the Display Data RAM are immediately reflected on the 
  actual LCD.  When writing bytes to the RAM, the column position is
  automatically incremented with each byte allowing continuous writing
  to memory. The cursor can also be manually set to any position in RAM.
 
     | Col 0 | Col 1 | Col 2 | ... | Col 131 |
   ---------------------------------------------------
     |  D0   |  D0   |               
   P |  D1   |  D1   |
   A |  D2   |  D2   |
   G |  D3   |  D3   |
   E |  D4   |  D4   |
     |  D5   |  D5   |
   0 |  D6   |  D6   | 
     |  D7   |  D7   |
   ----------------------------------------------------
     |  D0   |   
   P |  D1   |
   A |  D2   |
   G |  D3   |
   E |  D4   |
     |  D5   |
   1 |  D6   |
     |  D7   |
   ----------------------------------------------------
 
"""
class SH1106LCD():

    def __init__(self):
        #Default i2c bus
        self.bus = smbus.SMBus(1)
        self.OLED_Address = 0x3c
        self.OLED_Command_Mode = 0x80
        self.OLED_Data_Mode = 0x40
        
        #Initialize the screen.
        self.__initialize()
        self.clearScreen()
        
        #Set up internal image buffer
        self.imageBuffer = {}
        
        #Import font
        self.font = capFont
        self.font1 = capFont1
        self.fontLine1 = Line1
        self.fontNumber = Number1
        self.fontNumber1 = Number2

    """
     initialize()
     
     Initilizes the LCD.  Values are taken from the SH1106 datasheet.
    """
    def __initialize(self):
        time.sleep(0.25)
        self.__sendCommand(0xAE)
        self.__sendCommand(0x20)
        self.__sendCommand(0x10)
        self.__sendCommand(0xB0)
        self.__sendCommand(0xC0)

        self.__sendCommand(0x00)
        self.__sendCommand(0x10)
        self.__sendCommand(0x40)

        self.__sendCommand(0x81)
        self.__sendCommand(0x7F)
        self.__sendCommand(0xA1)
        self.__sendCommand(0xA6)
        self.__sendCommand(0xA0)
        self.__sendCommand(0x3F)
        self.__sendCommand(0xA4)
        self.__sendCommand(0xD3)
        self.__sendCommand(0x00)
        self.__sendCommand(0xD5)
        self.__sendCommand(0xF0)
        self.__sendCommand(0xD9)
        self.__sendCommand(0x22)
        self.__sendCommand(0xDA)
        self.__sendCommand(0x12)
        self.__sendCommand(0xDB)
        self.__sendCommand(0x20)
        self.__sendCommand(0x8D)
        self.__sendCommand(0x14)
        self.__sendCommand(0xAF)

        time.sleep(0.5)

    """
     powerUp()
     
      Turns on the lighting of the LCD.  Will display whatever
      is in the Display Data Ram.  Display Data Ram can be
      altered while the LCD is powered down.
    """
    def powerUp(self):
        self.__sendCommand(0xAF)

    """
     powerDown()
     
      Turns of the lighting of the LCD.  LCD will retain
      whatever is in the Display Data Ram.
    """
    def powerDown(self):
        self.__sendCommand(0xAE)	  #Power off display

    """
    clearRow(row)

        row - The row to blank (0 - 7)

      Writes 0x00 to every address in Display Data Ram
      for a given row.  This will blank the row.
    """
    def clearRow(self, row):
        page = 0xB0 + row
        self.__sendCommand(page)
        #Send 32 bytes at a time (max the bus can take) until we clear the first 128 columns.
        for i in range(4):
            self.__sendData([0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
        #Send the last 4 bytes to zero out all 132 columns
        self.__sendData([0x00,0x00,0x00,0x00])

    """
     clearScreen()
     
      Writes 0x00 to every address in the Display Data Ram
      effectively making the screen completely black.
      Should be called on first connection of the LCD as
      when uninitialized the LCD will display random pixels.
    """
    def clearScreen(self):
        for i in range(8):
                self.clearRow(i)
                self.__sendCommand(0x00)	 #reset column address
                self.__sendCommand(0x10)	 #reset column address

    """
     setCursorPosition(row,col)
     
         row - The row to place the cursor on (0 - 7)
         col - The column to place the cursor on (0 - 31)
     
    """
    def setCursorPosition(self, row, col):
        #Set row
        page = 0xB0 + row
        self.__sendCommand(page)
        #For some reason, the LCD does not seem to be correctly set up to display on the first two collumn addresses.
        #Therefor increase the column value by 2
        col = col + 2

        # Calculate the command bytes to set the column address
        # Column Address Offset: A7 A6 A5 A4 A3 A2 A1 A0
        # Upper Address Nibble Command: 0 0 0 0 A3 A2 A1 A0
        # Lower Address Nibble Command: 0 0 0 1 A7 A6 A5 A4
        lowerColumnOffsetByte = (col & 0x0F )
        upperColumnOffsetByte = (col >> 4) + 0x10
        #Set column
        self.__sendCommand(upperColumnOffsetByte)	 #Upper 4 bits
        self.__sendCommand(lowerColumnOffsetByte)    #Lower 4 bits



    """
     __sendCommand(command)
     
     	command - Hex data to send to the OLED as a command
     
     Used to send data to the OLED that should be interpreted as a command, and not display data.
     Commands are used to control the functions/configuration of the OLED.
     This method sends the control byte with the D/C Bit set LOW to tell the OLED that the next
     data sent will be a command
    """
    def __sendCommand(self, command):
        retries = 10
        error = None
        while retries > 0:
            try:
                self.bus.write_byte_data(self.OLED_Address, self.OLED_Command_Mode, command)
            except IOError as e:
                error = e
                retries -= 1
            else:
                break

    """
     __sendDataByte(dataByte)
     
     	dataByte - Single byte of data (in hex) to send to the OLED as display data.

    Sends a single display data byte to the Display Data RAM.
    """
    def __sendDataByte(self, dataByte):
        retries = 10
        error = None
        while retries > 0:
            try:
                self.bus.write_byte_data(self.OLED_Address, self.OLED_Data_Mode, dataByte)
            except IOError as e:
                error = e
                retries -= 1
            else:
                break

    def sendDataByte(self, dataByte):
        self.__sendDataByte(dataByte)

    """
    __sendData(data)
     
        data - Bytestream to send to the Display Data RAM.
    """
    def __sendData(self, data):
        retries = 10
        error = None
        while retries > 0:
            try:
                self.bus.write_i2c_block_data(self.OLED_Address, self.OLED_Data_Mode, data)
            except IOError as e:
                error = e
                retries -= 1
            else:
                break

    def sendData(self, data):
        self.__sendData(data)

    """
    chunks(array, chunkSize)

        array - Array to split.
        chuckSize - Size of chunks in which to split array.

    """
    def chunks(self, l, chunkSize):
        for i in range(0, len(l), chunkSize):
            yield l[i:i+chunkSize]


    """
    addImage(imageID, filename)

        imageID - String used to identify the stored image.
        filename - File to add.  Must be monochrome bit map

    Processes an image and adds it to the internal buffer.  This pre-processes the image
    before storing it and avoids unnecessary processing each time you wish to display it.

    """
    def addImage(self, imageID, filename):
        processedImage = self.LCDImage(filename)
        self.imageBuffer[imageID] = processedImage


    """
    displayBufferedImage(imageID, row, col)

        imageID - String identifying the pre-processed image in the internal buffer.
        row - row on which to start the upper left corner of the image (0-7)
        col - column on which to start the upper left corner of the image (0-31)

    Displays an image on the LCD that has already been pre-processed and placed into the
    internal buffer using the addImage method.
    """
    def displayBufferedImage(self, imageID, rowOffset, colOffset):
        try:
            if imageID not in self.imageBuffer.keys():
                raise ValueError(imageID + " not in the pre-processed image buffer.")
            else:
                image = self.imageBuffer.get(imageID)
            self.__displayProcessedImage(image, rowOffset, colOffset)

        except ValueError as e:
            print ("Value Error: ")
            traceback.print_exc()


    """
    displayImage(filename)

    """
    def displayImage(self, filename, rowOffset, colOffset):
        processedImage = self.LCDImage(filename)
        self.__displayProcessedImage(processedImage, rowOffset, colOffset)

    """
    displayString(inString, row, col)

    """
    def displayStringNumber(self, inString, row, col, wrap=None):
        if wrap is None:
            wrap = False
        displayStringNumber = inString
        #Set the row/column position
        self.setCursorPosition(row, col)
        for c in displayStringNumber:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            self.__sendData(self.fontNumber[fontIndex])
            self.__sendDataByte(0x00)
        self.setCursorPosition(row+1, col)
        for c in displayStringNumber:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            self.__sendData(self.fontNumber1[fontIndex])
            self.__sendDataByte(0x00)

    def displayStringLine1(self, inString, row, col, wrap=None):
        if wrap is None:
            wrap = False
        displayStringLine1 = inString
        #Set the row/column position
        self.setCursorPosition(row, col)
        for c in displayStringLine1:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            self.__sendData(self.fontLine1[fontIndex])
            self.__sendDataByte(0x00)

    def displayString(self, inString, row, col, wrap=None):
        if wrap is None:
            wrap = False
        #Convert string to all caps as lower case characters are not implemented in the font.
        #displayString = str(inString).upper()
        displayString = inString
        #Set the row/column position
        self.setCursorPosition(row, col)
        for c in displayString:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            self.__sendData(self.font[fontIndex])
            self.__sendDataByte(0x00)
        self.setCursorPosition(row+1, col)
        for c in displayString:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            self.__sendData(self.font1[fontIndex])
            self.__sendDataByte(0x00)
    
    """
    centerString(inString, row)

    """
    def centerString(self, inString, row):
        inString = str(inString)
        if len(inString) > 21:
            return
        startPosition = (131 - (6*len(inString)))/2
        self.displayString(inString, row, startPosition)

    """
    displayInvertedString(inString, row, col)

    """
    def displayInvertedString(self, inString, row, col):
        #Convert string to all caps as lower case characters are not implemented in the font.
        #displayString = str(inString).upper()
        displayString = inString
        #Set the row/column position
        self.setCursorPosition(row, col)
        for c in displayString:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            bytestream = self.font[fontIndex]
            for b in bytestream:
                #invert the byte and send it
                self.__sendDataByte(b ^ 0xff)
            self.__sendDataByte(0xff)
        self.setCursorPosition(row+1, col)
        for c in displayString:
            #Get the ascii value and then subtract 32 as the font does not have any characters before the 32nd implemented.
            fontIndex = ord(c) - 32
            bytestream = self.font1[fontIndex]
            for b in bytestream:
                #invert the byte and send it
                self.__sendDataByte(b ^ 0xff)
            self.__sendDataByte(0xff)

    """
    __displayProcessedImage(self, processedImage, row, col)

        processedImage - Pre-processed image.  Must be of type LCDImage below.
        row - Row (page) at which to start the upper left corner of the image
        col - Column at which to start the upper left corner of the image

    Takes an image that has already been processed and displays it on the LCD.  The upper left corner
    of the picture starts at the coordinates indicated by row and col.
    """
    def __displayProcessedImage(self, processedImage, row, col):
        try:
            #Ensure the picture will fit with the given column and row starting points.
            if (processedImage.width + col > 132) or (processedImage.height/8 + row > 8):
                raise ValueError("Picture is too large to fit on the screen with the supplied row/column: Width "
                                 + str(processedImage.width) + ", Height " + str(processedImage.height))
            #Get the raw data from the processed image
            imageData = processedImage.data

            #Display the image
            for i in range(row, 8):
                self.setCursorPosition(row, col)
                # Set column
                page = 0xB0 + i
                self.__sendCommand(page)
                #The i2c bus can only take a maximum of 32 bytes of data at a time.  If the image is more than 32 pixels
                # wide we need to break it into chunks.
                stream = imageData[i]
                if(len(stream) > 32):
                    splitStream = self.__chunks(list(stream), 32)
                    for chunk in splitStream:
                        self.__sendData(chunk)
                else:
                    self.__sendData(stream)

        except ValueError as e:
            print ("Value Error: ")
            traceback.print_exc()


    def __chunks(self, inList, chunkSize):
        for i in range(0, len(inList), chunkSize):
            yield inList[i:i+chunkSize]




#==============================================================================================
#        Internal Classes
#==============================================================================================

    """
    Class LCDImage
     
         filename - Bitmap file to parse
     
      Takes a monochrome bitmap image and represents it in a form
      that is more easily displayed on the LCD.
    """
    class LCDImage():

        def __init__(self, filename):
            self.width = 0
            self.height = 0
            self.data = self.processPicture(filename)


        """
         processPicture(filename)
         
             filename - The bitmap file to import.
         
          Imports a monocrhome bitmap file and converts it into a format
          that can be displayed on the LCD.  The black pixels of the
          bitmap will be read as "ON", and white as "OFF" effectively
          reversing the colors on the actual LCD.
          *The bitmap cannot be larger than 132 pixels wide or 64 pixels
           tall.
          *The bitmap's height must be divisible by 8.
         
             Returns - a (list of lists) that can be passed into
                 the displayImage(filename)
        """
        def processPicture(self, filename):
            output = []
            try:
                picture = Image.open(filename)
                width, height = picture.size
                #Ensure image file will fit within the limits of the LCD
                if(width>132 or height>64):
                    raise ValueError("Picture is larger than the allowable 132x64 pixels.")

                #Ensure image file height is divisible by 8
                #TODO - Should probably just change logic below to properly handle this case.  Don't need it for now.
                if(height % 8 != 0):
                    raise ValueError("Picture height is not divisible by 8.")

                #Properly set the width/height class variables
                self.width = width
                self.height = height

                #Read in the picture as a bitstream.
                bits = list(picture.getdata())

                #Convert stream of pixels to width x height array
                matrix = []
                for i in range(height):
                    temp = []
                    for j in range(width):
                        temp.append(bits[i*width + j])
                    matrix.append(temp)

                #Convert width x height array to


                for i in range(int(height/8)):
                    temp = []
                    for j in range(width):
                        bit0 = int(matrix[i*8][j] / 255)
                        bit1 = int(2 * (matrix[i*8 + 1][j] / 255))
                        bit2 = int(4 * (matrix[i*8 + 2][j] / 255))
                        bit3 = int(8 * (matrix[i*8 + 3][j] / 255))
                        bit4 = int(16 * (matrix[i*8 + 4][j] / 255))
                        bit5 = int(32 * (matrix[i*8 + 5][j] / 255))
                        bit6 = int(64 * (matrix[i*8 + 6][j] / 255))
                        bit7 = int(128 * (matrix[i*8 + 7][j] / 255))
                        temp.append(bit0 + bit1 + bit2 + bit3 + bit4 + bit5 + bit6 + bit7)
                    output.append(temp)

            except IOError as e:
                print ("I/O error: Could no open file: " + filename)
                traceback.print_exc()
            except ValueError as e:
                print ("Value Error: ")
                traceback.print_exc()

            return output




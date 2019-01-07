import time
import numpy as np
import lib.config as config

_GAMMA_TABLE = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
                1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5,
                5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 11,
                11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17,
                18, 18, 19, 19, 20, 20, 21, 21, 22, 23, 23, 24, 24, 25,
                26, 26, 27, 28, 28, 29, 30, 30, 31, 32, 32, 33, 34, 35,
                35, 36, 37, 38, 38, 39, 40, 41, 42, 42, 43, 44, 45, 46,
                47, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 56, 57, 58,
                59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 73,
                74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88,
                89, 91, 92, 93, 94, 95, 97, 98, 99, 100, 102, 103, 104,
                105, 107, 108, 109, 111, 112, 113, 115, 116, 117, 119,
                120, 121, 123, 124, 126, 127, 128, 130, 131, 133, 134,
                136, 137, 139, 140, 142, 143, 145, 146, 148, 149, 151,
                152, 154, 155, 157, 158, 160, 162, 163, 165, 166, 168,
                170, 171, 173, 175, 176, 178, 180, 181, 183, 185, 186,
                188, 190, 192, 193, 195, 197, 199, 200, 202, 204, 206,
                207, 209, 211, 213, 215, 217, 218, 220, 222, 224, 226,
                228, 230, 232, 233, 235, 237, 239, 241, 243, 245, 247,
                249, 251, 253, 255]
_GAMMA_TABLE = np.array(_GAMMA_TABLE)

class LEDController:
    """Base class for interfacing with hardware LED strip controllers
    To add support for another hardware device, simply inherit this class
    and implement the show() method.
    Example usage:
        import numpy as np
        N_pixels = 60
        pixels = np.random.random(size=(3, N_pixels))
        device = LEDController()
        device.show(pixels)
    """

    def __init__(self):
        pass

    def show(self, pixels):
        """Set LED pixels to the values given in the array
        This function accepts an array of RGB pixel values (pixels)
        and displays them on the LEDs. To add support for another
        hardware device, you should create a class that inherits from
        this class, and then implement this method.
        Parameters
        ----------
        pixels: numpy.ndarray
            2D array containing RGB pixel values for each of the LEDs.
            The shape of the array is (3, n_pixels), where n_pixels is the
            number of LEDs that the device has.
            The array is formatted as shown below. There are three rows
            (axis 0) which represent the red, green, and blue color channels.
            Each column (axis 1) contains the red, green, and blue color values
            for a single pixel:
                np.array([ [r0, ..., rN], [g0, ..., gN], [b0, ..., bN]])
            Each value brightness value is an integer between 0 and 255.
        Returns
        -------
        None
        """
        raise NotImplementedError('Show() was not implemented')

    def test(self, n_pixels):
        pixels = np.zeros((3, n_pixels))
        pixels[0][0] = 255
        pixels[1][1] = 255
        pixels[2][2] = 255
        print('Starting LED strip test.')
        print('Press CTRL+C to stop the test at any time.')
        print('You should see a scrolling red, green, and blue pixel.')
        while True:
            self.show(pixels)
            pixels = np.roll(pixels, 1, axis=1)
            time.sleep(0.2)


class ESP8266(LEDController):
    def __init__(self, auto_detect=False,
                 mac_addr="aa-bb-cc-dd-ee-ff",
                 ip='192.168.0.150',
                 port=7778):
        """Initialize object for communicating with as ESP8266
        Parameters
        ----------
        auto_detect: bool, optional
            Automatically search for and find devices on windows hotspot
            with given mac addresses. Windows hotspot resets the IP
            addresses of any devices on reset, meaning the IP of the 
            ESP8266 changes every time you turn on the hotspot. This
            will find the IP address of the devices for you.
        mac_addr: str, optional
            The MAC address of the ESP8266 on the network. Only used if
            auto-detect is used
        ip: str, optional
            The IP address of the ESP8266 on the network. This must exactly
            match the IP address of your ESP8266 device, unless using
            the auto-detect feature.
        port: int, optional
            The port number to use when sending data to the ESP8266. This
            must exactly match the port number in the ESP8266's firmware.
        """
        import socket
        self._mac_addr = mac_addr
        self._ip = ip
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if auto_detect:
            self.detect()

    def detect(self):
        from subprocess import check_output
        from time import sleep
        """ Uses "arp -a" to find esp8266 on windows hotspot"""
        # Find the audio strip automagically
        ip_addr = False
        while not ip_addr:
            arp_out = check_output(['arp', '-a']).splitlines()
            for i in arp_out:
                if self._mac_addr in str(i):
                    ip_addr = i.split()[0].decode("utf-8")
                    break
            else:
                print("Device not found at physical address {}, retrying in 1s".format(self._mac_addr))
                sleep(1)
        print("Found device {}, with IP address {}".format(self._mac_addr, ip_addr))
        self._ip = ip_addr

    def show(self, pixels):
        """Sends UDP packets to ESP8266 to update LED strip values
        The ESP8266 will receive and decode the packets to determine what values
        to display on the LED strip. The communication protocol supports LED strips
        with a maximum of 256 LEDs.
        The packet encoding scheme is:
            |i|r|g|b|
        where
            i (0 to 255): Index of LED to change (zero-based)
            r (0 to 255): Red value of LED
            g (0 to 255): Green value of LED
            b (0 to 255): Blue value of LED
        """
        message = pixels.T.clip(0, config.settings["configuration"]["MAX_BRIGHTNESS"]).astype(np.uint8).ravel().tostring()
        self._sock.sendto(message, (self._ip, self._port))
        # self._sock.sendto(message, ('192.168.0.155', 7777))


class FadeCandy(LEDController):
    def __init__(self, server='localhost:7890'):
        """Initializes object for communicating with a FadeCandy device
        Parameters
        ----------
        server: str, optional
            FadeCandy server used to communicate with the FadeCandy device.
        """
        try:
            import audioled.opc
        except ImportError as e:
            print('Unable to import audioled.opc library')
            print('You can install this library with `pip install opc`')
            raise e
        self.client = audioled.opc.Client(server)
        if self.client.can_connect():
            print('Successfully connected to FadeCandy server.')
        else:
            print('Could not connect to FadeCandy server.')
            print('Ensure that fcserver is running and try again.')

    def show(self, pixels):
        self.client.put_pixels(pixels.T.clip(0, 255).astype(int).tolist())


class BlinkStick(LEDController):
    def __init__(self):
        """Initializes a BlinkStick controller"""
        try:
            from blinkstick import blinkstick
        except ImportError as e:
            print('Unable to import the blinkstick library')
            print('You can install this library with `pip install blinkstick`')
            raise e
        self.stick = blinkstick.find_first()

    def show(self, pixels):
        """Writes new LED values to the Blinkstick.
        This function updates the LED strip with new values.
        """
        # Truncate values and cast to integer
        n_pixels = pixels.shape[1]
        pixels = pixels.clip(0, 255).astype(int)
        pixels = _GAMMA_TABLE[pixels]
        # Read the rgb values
        r = pixels[0][:].astype(int)
        g = pixels[1][:].astype(int)
        b = pixels[2][:].astype(int)

        # Create array in which we will store the led states
        newstrip = [None] * (n_pixels * 3)

        for i in range(n_pixels):
            # Blinkstick uses GRB format
            newstrip[i * 3] = g[i]
            newstrip[i * 3 + 1] = r[i]
            newstrip[i * 3 + 2] = b[i]
        # Send the data to the blinkstick
        self.stick.set_led_data(0, newstrip)


class RaspberryPi(LEDController):
    def __init__(self, n_pixels, pin=18, invert_logic=False,
                 freq=800000, dma=5):
        """Creates a Raspberry Pi output device
        Parameters
        ----------
        n_pixels: int
            Number of LED strip pixels
        pin: int, optional
            GPIO pin used to drive the LED strip (must be a PWM pin).
            Pin 18 can be used on the Raspberry Pi 2.
        invert_logic: bool, optional
            Whether or not to invert the driving logic.
            Set this to True if you are using an inverting logic level
            converter, otherwise set to False.
        freq: int, optional
            LED strip protocol frequency (Hz). For ws2812 this is 800000.
        dma: int, optional
            DMA (direct memory access) channel used to drive PWM signals.
            If you aren't sure, try 5.
        """
        try:
            import neopixel
        except ImportError as e:
            url = 'learn.adafruit.com/neopixels-on-raspberry-pi/software'
            print('Could not import the neopixel library')
            print('For installation instructions, see {}'.format(url))
            raise e
        self.strip = neopixel.Adafruit_NeoPixel(n_pixels, pin, freq, dma,
                                                invert_logic, 255)
        self.strip.begin()

    def show(self, pixels):
        """Writes new LED values to the Raspberry Pi's LED strip
        Raspberry Pi uses the rpi_ws281x to control the LED strip directly.
        This function updates the LED strip with new values.
        """
        # Truncate values and cast to integer
        n_pixels = pixels.shape[1]
        pixels = pixels.clip(0, 255).astype(int)
        # Optional gamma correction
        pixels = _GAMMA_TABLE[pixels]
        # Encode 24-bit LED values in 32 bit integers
        r = np.left_shift(pixels[0][:].astype(int), 8)
        g = np.left_shift(pixels[1][:].astype(int), 16)
        b = pixels[2][:].astype(int)
        rgb = np.bitwise_or(np.bitwise_or(r, g), b)
        # Update the pixels
        for i in range(n_pixels):
            self.strip._led_data[i] = rgb[i]
        self.strip.show()


class DotStar(LEDController):
    def __init__(self, pixels, brightness=31):
        """Creates an APA102-based output device
        Parameters
        ----------
        pixels: int
            Number of LED strip pixels
        brightness: int, optional
            Global brightness
        """
        try:
            import apa102
        except ImportError as e:
            url = 'https://github.com/tinue/APA102_Pi'
            print('Could not import the apa102 library')
            print('For installation instructions, see {}'.format(url))
            raise e
        self.strip = apa102.APA102(numLEDs=pixels, globalBrightness=brightness) # Initialize the strip
        led_data = np.array(self.strip.leds, dtype=np.uint8)
        # memoryview preserving the first 8 bits of LED frames (w/ global brightness)
        self.strip.leds = led_data.data
        # 2D view of led_data
        self.led_data = led_data.reshape((pixels, 4)) # or (-1, 4)

    def show(self, pixels):
        bgr = [2,1,0]
        self.led_data[0:,1:4] = pixels[bgr].T.clip(0,255)
        self.strip.show()
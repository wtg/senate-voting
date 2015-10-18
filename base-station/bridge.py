#!/usr/bin/env python

from __future__ import print_function

import array, time, threading

import usb, usb.core, usb.util

import MeteorClient


class Command(object):
    def __init__(self, byte_array=None):
        if byte_array is None:
            byte_array = []

        if type(byte_array) is str:
            # If we passed in a string, assume it is a string of hex characters and turn it into bytes
            byte_array = byte_array.replace(' ', '')
            byte_array = array.array('B', (int(byte_array[i:i + 2], 16) for i in range(0, len(byte_array), 2)))
        elif type(byte_array) is bytes:
            pass
        # Make sure we have a 64 byte packet by padding with zeros
        self.bytes = array.array('B', byte_array[:64])
        self.bytes.extend([0] * (64 - len(self.bytes)))

    def __getitem__(self, key):
        return self.bytes[key]

    def __setitem__(self, key, value):
        self.bytes[key] = value

    def __repr__(self):
        """
        Returns the command as a hex string.
        """

        SPLIT_BY_N_CHARS = 16
        hex_string = ''.join('%02X' % x for x in self.bytes)
        return ' '.join(hex_string[i:i + SPLIT_BY_N_CHARS] for i in range(0, len(hex_string), SPLIT_BY_N_CHARS)).lower()

    def __eq__(self, other):
        return self.bytes == other.bytes
    
    def __ne__(self, other):
        return self.bytes != other.bytes

    def as_bytes(self):
        return self.bytes.tostring()

    @staticmethod
    def clicker_id_from_bytes(byte_seq):
        """
        Given a sequence of three bytes, computes the last byte
        in the clicker id and returns it as hex.
        """

        # Make a copy since we'll be appending to it
        byte_seq = byte_seq[:]
        byte_seq.append(byte_seq[0] ^ byte_seq[1] ^ byte_seq[2])

        return ''.join('%02X' % b for b in byte_seq)

    def _process_alpha_clicker_response(self):
        """
        This method will return information about an alpha clicker response.
        """

        ret = {'type': 'ClickerResponse', 'poll_type': 'Alpha'}
        ret['clicker_id'] = self.clicker_id_from_bytes(self.bytes[3:6])
        if self.bytes[2] >= 0x81:
            # Responses start with 0x81 for A and work their way up, so ascii-recode them
            ret['response'] = chr(self.bytes[2] - 0x81 + 65)
        else:
            # For iClicker 1 responses are 1 == A, 2 == B, etc.
            ret['response'] = chr(self.bytes[2] - 0x1 + 65)
        ret['seq_num'] = self.bytes[6]

        return ret

    def info(self):
        """
        Returns all the information we know about the command.
        """

        byte0 = self.bytes[0]
        byte1 = self.bytes[1]
        ret = { 'type': 'unknown', 'raw_command': self.__repr__() }
        if byte0 == 0x01:
            if byte1 == 0x10:
                ret['type'] = 'SetFrequency'
                ret['freq1'] = self.bytes[2] - 0x21
                ret['freq2'] = self.bytes[3] - 0x41
            if byte1 == 0x11:
                ret['type'] = 'StartPolling'
            if byte1 == 0x12:
                ret['type'] = 'StopPolling'
            if byte1 == 0x18:
                if self.bytes[2] == 0x01 and self.bytes[3] == 0x00:
                    ret['type'] = 'ResetBase'
            if byte1 == 0x19:
                ret['type'] = 'SetPollType'
                ret['quiz_type'] = self.bytes[2] - 0x67
            if byte1 == 0x2d:
                ret['type'] = 'SetIClicker2Protocol'
        elif byte0 == 0x02:
            if byte1 == 0x13:
                ret.update(self._process_alpha_clicker_response())
            if byte1 == 0x1a:
                pass

        return ret

    def response_info(self):
        """
        Returns a list containing every response in this command.
        Since a 64 byte command can contain two 32 byte clicker responses,
        this separates them and returns a list with both their infos.
        """

        info1 = Command(self.bytes[:32]).info()
        info2 = Command(self.bytes[32:]).info()
        ret = []
        if info1['type'] == 'ClickerResponse':
            ret.append(info1)
        if info2['type'] == 'ClickerResponse':
            ret.append(info2)

        return ret


class IClickerBase(object):
    """
    This class handles all the hardware-related aspects of talking
    with the iClicker base unit.
    """

    VENDOR_ID = 0x1881
    PRODUCT_ID = 0x0150

    def __init__(self):
        self.device = None
        self.has_initialized = False
        # pyusb is not threadsafe, so we need to aquire a lock for all usb operations
        self.usb_lock = threading.RLock()
        self.screen_buffer = [' ' * 16, ' ' * 16]

    def _write(self, data):
        """
        Raw-write of data to self.device.
        """

        with self.usb_lock:
            self.device.ctrl_transfer(0x21, 0x09, 0x0200, 0x0000, data.as_bytes())

    def _read(self, timeout=100):
        """
        Read a packet of data from self.device.
        """

        with self.usb_lock:
            return Command(self.device.read(0x83, 64, timeout=timeout))

    def _syncronous_write(self, data, timeout=100):
        """
        Writes data to self.device expecting a response of "?? ?? aa"
        where "?? ??" are the first two bytes of data.
        """

        expected_response = Command([data[0], data[1], 0xaa])
        self._write(data)
        response = self._read(timeout=timeout)
        if response != expected_response:
            raise IOError("Attempted syncronuous write of {0} and got {1} (expecting {2})".format(data.__repr__(), response.__repr__(), expected_response.__repr__()))

    def _write_command_sequence(self, seq):
        """
        Write a sequence of commands to the usb device and read all the responses.
        """

        for cmd in seq:
            self._write(cmd)
            while True:
                try:
                    self._read()
                except usb.USBError, e:
                    # We ignore "Operation timed out" exception
                    if getattr(e, 'errno', None) == 110:
                        return
                    raise

    def read(self, timeout=100):
        try:
            return Command(self._read(timeout))
        except usb.USBError, e:
            # We ignore "Operation timed out" exception
            if getattr(e, 'errno', None) == 110:
                return None
            raise

    def get_base(self):
        """
        Looks on the USB bus for an iClicker device
        """

        with self.usb_lock:
            self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)

            if self.device is None:
                raise ValueError("Error: no iClicker device found")
            
            if self.device.is_kernel_driver_active(0):
                print("The iClicker seems to be in use by another device. Forcing reattach.")
                self.device.detach_kernel_driver(0)
        
            self.device.set_configuration()
            time.sleep(0.2)

    def set_base_frequency(self, code1='a', code2='a'):
        """
        Sets the operating frequency.
        """

        def code_to_number(code):
            if type(code) is str:
                # 'a' == 1, 'b' == 2, etc.
                return ord(code.lower()) - 97
            return code

        time.sleep(0.2)
        with self.usb_lock:
            cmd = Command([0x01, 0x10, 0x21 + code_to_number(code1), 0x41 + code_to_number(code2)])
            self._syncronous_write(cmd)
            time.sleep(0.2)
            cmd = Command([0x01, 0x16])
            self._syncronous_write(cmd)
            time.sleep(0.2)

    def set_version_two_protocol(self):
        """
        Sets the base unit to use the iClicker version 2 protocol.
        """

        with self.usb_lock:
            cmd = Command([0x01, 0x2d])
            self._write(cmd)
            time.sleep(0.2)

    def set_poll_type(self, poll_type='alpha'):
        """
        Sets the poll type to 'alpha', 'numeric', or 'alphanumeric'.
        """

        print("Setting poll type to {0}".format(poll_type))

        with self.usb_lock:
            poll_type = {'alpha': 0, 'numeric': 1, 'alphanumeric': 2}[poll_type]
            cmd = Command([0x01, 0x19, 0x66 + poll_type, 0x0a, 0x01])
            self._write(cmd)
            time.sleep(0.2)

    # TODO: There are still a lot of unknowns here... right now
    # It just repeats what was snooped from USB on Windows
    def initialize(self, freq1='a', freq2='a'):
        COMMAND_SEQUENCE_A = [
            Command('01 2a 21 41 05'),
            Command('01 12'),
            Command('01 15'),
            Command('01 16'),
        ]
        
        COMMAND_SEQUENCE_B = [
            Command('01 29 a1 8f 96 8d 99 97 8f'),
            Command('01 17 04'),
            Command('01 17 03'),
            Command('01 16'),
        ]

        if self.device is None:
            self.get_base()

        with self.usb_lock:
            self.set_base_frequency(freq1, freq2)
            self._write_command_sequence(COMMAND_SEQUENCE_A)
            time.sleep(0.2)
            self.set_version_two_protocol()
            self._write_command_sequence(COMMAND_SEQUENCE_B)
            time.sleep(0.2)
            self.has_initialized = True

    def start_poll(self, poll_type='alpha'):
        COMMAND_SEQUENCE_A = [
            Command('01 17 03'),
            Command('01 17 05'),
        ]
        COMMAND_START_POLL = Command('01 11')

        with self.usb_lock:
            self._write_command_sequence(COMMAND_SEQUENCE_A)
            time.sleep(0.2)
            self.set_poll_type(poll_type)
            self._write(COMMAND_START_POLL)
            time.sleep(0.2)

    def stop_poll(self):
        COMMAND_SEQUENCE_A = [
            Command('01 12'),
            Command('01 16'),
            Command('01 17 01'),
            Command('01 17 03'),
            Command('01 17 04'),
        ]

        with self.usb_lock:
            self._write_command_sequence(COMMAND_SEQUENCE_A)
            time.sleep(0.2)

    def _set_screen(self, line=0):
        """
        Sets the line @line to the characters specified by self.screen_buffer[line].
        This command messes up the screen if it is sent too frequently.
        """

        if not self.has_initialized:
            return

        if line == 0:
            cmd = [0x01, 0x13]
        else:
            cmd = [0x01, 0x14]

        # Make sure we are writing only 16 characters to the screen
        string = self.screen_buffer[line]
        string = string[:16]
        string = string + ' ' * (16 - len(string))
        cmd.extend(ord(c) for c in string)
        cmd = Command(cmd)

        with self.usb_lock:
            self._write(cmd)
            time.sleep(0.05)

    def set_screen(self, string, line=0):
        """
        Sets the line @line to the characters specified by @string.
        This command messes up the screen if it is sent too frequently,
        so do not call it too often.
        """

        # If our buffer hasn't changed, just exit - we don't even need to update the screen
        if string == self.screen_buffer[line]:
            return

        # Set our buffer to the appropriate string
        self.screen_buffer[line] = string

        self._set_screen(line)

class Response(object):
    """
    Keeps track of all relevant information about an iClicker response.
    """

    def __init__(self, clicker_id=None, response=None, click_time=None, seq_num=None):
        if click_time is None:
            self.click_time = time.time()
        else:
            self.click_time = click_time

        self.clicker_id = clicker_id
        self.response = response
        self.seq_num = seq_num

    def __eq__(self, other):
        if type(other) is Response:
            return self.clicker_id == other.clicker_id and self.response == other.response and self.seq_num == other.seq_num
        else:
            return False

    def __ne__(self, other):
        if type(other) is Response:
            return self.clicker_id != other.clicker_id or self.response != other.response or self.seq_num != other.seq_num
        else:
            return True

    def __repr__(self):
        return "{0}: {1} ({2} at {3})".format(self.clicker_id, self.response, self.seq_num, self.click_time)


class IClickerPoll(object):
    def __init__(self, iclicker_base, meteor_client):
        self.base = iclicker_base
        self.client = meteor_client
        self.poll_stopped = False
        self.poll_start_time = 0
        self.responses = 0

    def update_display(self):
        """
        Updates the base display according to the poll results.
        """

        with self.base.usb_lock:
            try:
                print(self.client.find('display'))
                out_string = (self.client.find_one('display') or {}).get('line', '')[0:16]
                self.base.set_screen(out_string, line=1)
            except:
                # Because we restart inside USB lock, we know that another thread's while self.poll_stopped will not be false
                self.restart()
                assert self.poll_stopped == False
                return

        # Write the time and number of total votes to the first line of the display
        secs = int(time.time() - self.poll_start_time)
        mins = secs // 60
        secs = secs % 60

        out_string_time = "{0}:{1:02}".format(mins, secs)
        out_string = "{0}{1:>{padding}}".format(out_string_time, self.responses, padding=(16 - len(out_string_time)))

        with self.base.usb_lock:
            try:
                self.base.set_screen(out_string, line=0)
            except:
                # Because we restart inside USB lock, we know that another thread's while self.poll_stopped will not be false
                self.restart()
                assert self.poll_stopped == False

    def restart(self):
        print("Restarting iClicker USB connection")

        try:
            self.stop_poll()
        except:
            # We just ignore any errors while stopping
            pass

        print("Initializing iClicker Base")
        self.base.initialize()
        print("Restarting poll")
        self.restart_poll('alpha')

    def start_poll(self, poll_type='alpha'):
        """
        Starts a poll and then starts watching input.
        """

        self.poll_start_time = time.time()
        self.responses = 0

        self.restart_poll(poll_type)

        self.display_update_loop()

        # This blocks until self.poll_stopped is set to true
        self.watch_input()

        # After watch input exits, we want to stop the poll
        self.stop_poll()

    def restart_poll(self, poll_type='alpha'):
        if not self.base.has_initialized:
            self.base.initialize()

        self.base.start_poll(poll_type)
        self.poll_stopped = False

    def stop_poll(self):
        self.poll_stopped = True
        self.base.stop_poll()

    def watch_input(self):
        """
        Constantly polls the USB device for iClicker responses.
        """

        while self.poll_stopped is False:
            with self.base.usb_lock:
                try:
                    response = self.base.read(50)
                except:
                    # Because we restart inside USB lock, we know that another thread's while self.poll_stopped will not be false
                    self.restart()
                    assert self.poll_stopped == False
                    continue
            # If there is no response, do nothing
            if response is None:
                # Sleep a bit so that USB lock is not locked all the time,
                # this makes display be updated regularly even on multi-core machines
                time.sleep(0.01)
                continue
            for info in response.response_info():
                self.response(Response(info['clicker_id'], info['response'], time.time(), info['seq_num']))

    def display_update_loop(self, interval=1):
        """
        Spawns a new thread and updates the display every @interval
        number of seconds.
        """

        def update():
            while self.poll_stopped is False:
                self.update_display()
                time.sleep(interval)

        display_thread = threading.Thread(target=update)
        display_thread.start()

    def response(self, response):
        self.responses += 1
        print(response)

        def callback_function(error, result):
            if error:
                print("[Meteor] iclicker-vote error {}".format(error))

        self.client.call('iclicker-vote', [response.clicker_id, response.response, response.click_time], callback_function)

# This is a callback that stops the poll, since start a poll is a blocking operation
def close_pole(poll):
    print("Stopping poll")
    poll.stop_poll()

if __name__ == '__main__':
    import argparse, signal, sys

    parser = argparse.ArgumentParser(description="Start an iClicker base station Meteor bridge.")
    parser.add_argument('url', metavar="<server URL>", type=str,
                        help="server URL to connect to (e.g., 'ws://127.0.0.1:3000/websocket')")
    parser.add_argument("--frequency", type=str, default='aa',
                        help="set base-station frequency, formatted as two letters (e.g., 'aa' or 'ab')")
    parser.add_argument("--username", type=str, default=None,
                        help="login to the server using provided username")
    parser.add_argument("--password", type=str, default=None,
                        help="login to the server using provided password")

    args = parser.parse_args()

    freq1 = args.frequency[0].lower()
    freq2 = args.frequency[1].lower()
    if freq1 not in ('a', 'b', 'c', 'd') or freq2 not in ('a', 'b', 'c', 'd'):
        raise ValueError("Frequency combination '{0}{1}' is not valid".format(freq1, freq2))

    if (args.username is not None and args.password is None) or (args.username is None and args.password is not None):
        raise ValueError("Both username and password have to be specified for server login.")

    onConnected = threading.Event()
    onReady = threading.Event()

    base = None
    poll = None
    client = None
    exit_code = None

    def subscribe():
        def subscription_callback(error):
            if error:
                print("[Meteor] display subscription error {}".format(error))
                exit(2)
            onReady.set()

        client.subscribe('display', callback=subscription_callback)

    def close(exit=0):
        global poll
        global client
        global exit_code

        if poll:
            close_pole(poll)
            poll = None

        if client:
            client.close()
            client = None

        if exit_code is None:
            exit_code = exit

        # To make sure we are not waiting anymore
        onConnected.set()
        onReady.set()

    signal.signal(signal.SIGINT, lambda *x: close(0))

    client = MeteorClient.MeteorClient(args.url)

    def connected():
        print("[Meteor] Connected")

    client.on('connected', connected)

    def closed(code, reason):
        print("[Meteor] Connection closed {} {}".format(code, reason))

    client.on('closed', closed)

    def failed(data):
        print("[Meteor] Failed {}".format(data))

    client.on('failed', failed)

    def reconnected():
        print("[Meteor] Reconnected")

    client.on('reconnected', reconnected)

    def logging_in():
        print("[Meteor] Logging in")

    client.on('logging_in', logging_in)

    def logged_in(data):
        print("[Meteor] Logged in {}".format(data))

    client.on('logged_in', logged_in)

    def logged_out():
        print("[Meteor] Logged out")

    client.on('logged_out', logged_out)

    client.connect()

    # We wait in a loop so that signals can be delivered
    while onConnected.wait(0.1) is None:
        pass

    if exit_code is None:
        def login_callback(error, data):
            if error:
                print("[Meteor] Login failed {}".format(error))
                close(1)
                onReady.set()
            else:
                print("[Meteor] Login succeeded {}".format(data))
                subscribe()

        if args.username is not None and args.password is not None:
            client.login(args.username, args.password, login_callback)
        else:
            subscribe()

        # We wait in a loop so that signals can be delivered
        while onReady.wait(0.1) is None:
            pass

    if exit_code is None:
        try:
            print("Finding iClicker Base")
            base = IClickerBase()
            base.get_base()
            print("Initializing iClicker Base")
            base.initialize(freq1, freq2)

            print("Starting poll")
            poll = IClickerPoll(base, client)
            poll.start_poll('alpha')
        finally:
            # On an exception we also want to close Meteor connection
            close(3)

    # Wait a bit to cleanup
    time.sleep(1)

    sys.exit(exit_code)

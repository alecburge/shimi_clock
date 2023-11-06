import wave
import time
import sys
import pdb
import threading
import numpy as np
import signal
import pyaudio
from queue import Queue

class Heartbeat:
    """ Heartbeat object takes in wav, tempo, the division of the beat, and the buffer size
        The object works by referencing the callback to determine the number of samples between each
        beat. Song, tempo, the division of the beat (1,.5,.25) and buffer size are arguments."""
    def __init__(self, song, tempo, beat_div, buffer_size):
        self.tempo = tempo
        self.genre = ''
        self.current_length = 0
        self.song = song
        self.buffer_size = buffer_size
        self.beat_division = beat_div # 1 is every beat, .5 is 1-and, ect.
        self.audio_rate = 44100
        self.samples_per_beat = ((self.audio_rate*60)/(self.tempo)*self.beat_division)
        self.count_cb = 0
        self.beat_no = 0
        self.message_send = 0
        self.playing = True

        self.heartbeat_rate = self.samples_per_beat/self.buffer_size # how many callbacks per beat
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_message)
        self.condition = threading.Condition()

    def callback(self, in_data, frame_count, time_info, status):
        
        data = self.audio_data.readframes(frame_count)
        with self.condition:
            self.count_cb +=1

            if round(self.heartbeat_rate) == self.count_cb:

                self.condition.notify()

        return (data, pyaudio.paContinue)

    def heartbeat_message(self):
        
        counter_beats = 0
        hb_rate_iter = self.heartbeat_rate

        while self.stream.is_active():
            with self.condition:
                counter_beats += self.beat_division
                self.heartbeat_rate += hb_rate_iter
                self.beat_no = counter_beats
                self.condition.wait()
        
    def play_song(self, out_q):
        with wave.open(self.song, 'rb') as wf:
            self.audio_data = wf
            
            audio_object = pyaudio.PyAudio()
            device_list = audio_object.get_device_count
            self.stream = audio_object.open(format=audio_object.get_format_from_width(self.audio_data.getsampwidth()),
                            channels=self.audio_data.getnchannels(),
                            rate=self.audio_data.getframerate(),
                            output=True,
                            frames_per_buffer = self.buffer_size,
                            stream_callback=self.callback)

            self.heartbeat_thread.start()
            message_value = self.beat_no

            while self.stream.is_active():
                if self.beat_no != message_value:
                    out_q.put(self.beat_no)
                    message_value = self.beat_no
                    out_q.task_done()
                
            with self.condition:
                self.condition.notify()
            self.playing = False
            out_q.put(False)
            out_q.task_done()
            self.stream.close()
            
            # Release PortAudio system resources (6)
            audio_object.terminate()



def main():
    if len(sys.argv) < 2:
        print(f'Plays a wave file. Usage: {sys.argv[0]} filename.wav')
        sys.exit(-1)
    fdef signal_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    app = Heartbeat(sys.argv[1], 80, 1, 128)

    q = Queue() #Heartbeat messages are Queued 

    start_clock = threading.Thread(target= app.play_song, args =(q, ))
    start_clock.start()

    while True: #
        value = q.get() 
        print(value)
        if value is False:
            break
        
main()
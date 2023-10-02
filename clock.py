import wave
import time
import sys
import pdb
import threading
import numpy as np
import signal
import pyaudio

class Clock:
    def __init__(self, song, tempo, beat_div, buffer_size):
        # self.socket = socket.socket()
        # self.socket.bind(('0.0.0.0', 5050))
        # self.socket.listen(9)

        # print("Server bound on port 5050")

        # self.client_socket = ''

        self.tempo = tempo
        self.genre = ''
        self.current_length = 0
        self.song = song
        self.buffer_size = buffer_size
        self.beat_division = beat_div # 1 is every beat, .5 is 1-and, ect.
        self.audio_rate = 44100
        self.samples_per_beat = ((self.audio_rate*60)/(self.tempo)*self.beat_division)

        self.heartbeat_rate = self.samples_per_beat/self.buffer_size # how many callbacks per beat
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_message)
        self.condition = threading.Condition()

    def callback(self, in_data, frame_count, time_info, status):
        
        data = self.audio_data.readframes(frame_count)
        with self.condition:
            self.condition.notify()

        return (data, pyaudio.paContinue)

    def heartbeat_message(self):
        

        counter_cb = 0
        counter_beats = 0
        hb_rate_iter = self.heartbeat_rate

        while self.stream.is_active():
            with self.condition:

                counter_cb += 1

                if counter_cb == round(hb_rate_iter):
                    counter_beats += self.beat_division
                    hb_rate_iter += self.heartbeat_rate
                    
                    print(counter_beats)
                    
               
                
                self.condition.wait()
                
        
    def play_song(self):
        # pdb.set_trace()
        with wave.open(self.song, 'rb') as wf:
            self.audio_data = wf
            
            audio_object = pyaudio.PyAudio()
            
            self.stream = audio_object.open(format=audio_object.get_format_from_width(self.audio_data.getsampwidth()),
                            channels=self.audio_data.getnchannels(),
                            rate=self.audio_data.getframerate(),
                            output=True,
                            frames_per_buffer = self.buffer_size,
                            stream_callback=self.callback)

            self.heartbeat_thread.start()
           
            while self.stream.is_active():
                
                time.sleep(.01)
            with self.condition:
                self.condition.notify()
            print('complete')
            self.stream.close()
            
            # Release PortAudio system resources (6)
            audio_object.terminate()

def main():
    if len(sys.argv) < 2:
        print(f'Plays a wave file. Usage: {sys.argv[0]} filename.wav')
        sys.exit(-1)
    app = Clock(sys.argv[1], 160, 1, 512)
    
    # app.play_song()
    # heartbeat_thread.start()
    app.play_song()

main()
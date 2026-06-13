import threading
import queue
import sounddevice as sd
import numpy as np


class NoiseDetector:
    def __init__(self):
        self.sensitivity = 1.0
        self.audio_queue = queue.Queue()
        # sd.default.device may be a tuple; choose first available input index
        try:
            self.current_device = sd.default.device[0]
        except Exception:
            # fallback to None which lets sounddevice pick default
            self.current_device = None
        self.running = False
        self.noise_min_baseline = 0.0
        self.noise_max_baseline = 100.0

    def calculate_db(self, audio_data):
        audio_data = np.clip(audio_data, -1.0, 1.0)
        rms = np.sqrt(np.mean(audio_data ** 2))
        if rms < 1e-10:
            rms = 1e-10
        db = 20 * np.log10(rms) + 94
        adjusted_db = (db - self.noise_min_baseline) / (self.noise_max_baseline - self.noise_min_baseline) * 60 + 10
        adjusted_db = max(10, min(70, adjusted_db))
        return adjusted_db

    def calibrate_min_baseline(self):
        print("正在校准最小基准线，请保持安静...")
        samplerate = 44100
        with sd.InputStream(device=self.current_device, channels=1, samplerate=samplerate) as stream:
            audio_data = stream.read(samplerate)[0]
            self.noise_min_baseline = self.calculate_db(audio_data[:, 0])
        print(f"最小基准线校准完成：{self.noise_min_baseline:.1f} dB")

    def calibrate_max_baseline(self):
        print("正在校准最大基准线，请保持安静...")
        duration = 2
        frequency = 1000
        samplerate = 44100
        t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
        tone = 0.8 * np.sin(2 * np.pi * frequency * t)

        def play_tone():
            sd.play(tone, samplerate)
            sd.wait()

        threading.Thread(target=play_tone, daemon=True).start()

        with sd.InputStream(device=self.current_device, channels=1, samplerate=samplerate) as stream:
            audio_data = stream.read(samplerate)[0]
            self.noise_max_baseline = self.calculate_db(audio_data[:, 0])
        print(f"最大基准线校准完成：{self.noise_max_baseline:.1f} dB")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"音频流状态: {status}")
        self.audio_queue.put(indata[:, 0])

    def start(self):
        self.running = True
        self.stream = sd.InputStream(
            device=self.current_device,
            channels=1,
            callback=self.audio_callback,
            samplerate=44100,
            blocksize=1024,
        )
        self.stream.start()
        print("音频流已启动")

    def stop(self):
        self.running = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

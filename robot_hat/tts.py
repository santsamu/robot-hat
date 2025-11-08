#!/usr/bin/env python3
from .basic import _Basic_class
from .utils import is_installed, run_command
from .music import Music
from distutils.spawn import find_executable
import time
import threading
import subprocess
import os


class TTS(_Basic_class):
    """Text to speech class"""
    _class_name = 'TTS'
    SUPPORTED_LANGUAUE = [
        'en-US',
        'en-GB',
        'de-DE',
        'es-ES',
        'fr-FR',
        'it-IT',
    ]
    """Supported TTS language for pico2wave"""

    ESPEAK = 'espeak'
    """espeak TTS engine"""
    ESPEAK_NG = 'espeak-ng'
    """espeak-ng TTS engine"""
    PICO2WAVE = 'pico2wave'
    """pico2wave TTS engine"""

    def __init__(self, engine=ESPEAK_NG, lang=None, *args, **kwargs):
        """
        Initialize TTS class.

        :param engine: TTS engine, TTS.PICO2WAVE, TTS.ESPEAK, or TTS.ESPEAK_NG
        :type engine: str
        """
        super().__init__()
        self.engine = engine
        self._is_speaking = False
        self._speech_start_time = None
        self._speech_duration = 0
        self._speech_queue = []
        self._speech_lock = threading.Lock()
        self._volume_gain = 2.0  # Volume multiplier for aplay (1.0 = normal, 2.0 = double volume)
        if (engine == self.ESPEAK or engine == self.ESPEAK_NG):
            if not is_installed(engine):
                raise Exception(f"TTS engine: {engine} is not installed.")
            self._amp = 150  # Increased default amplitude for louder speech
            self._speed = 175
            self._gap = 5
            self._pitch = 50
            if lang == None:
                self._lang = "en-us"
            else:
                self._lang = lang
            self._supported_lang = _get_supported_lang_espeak(engine)
        elif (engine == self.PICO2WAVE):
            if not is_installed("pico2wave"):
                raise Exception("TTS engine: pico2wave is not installed.")
            if lang == None:
                self._lang = "en-US"
            else:
                self._lang = lang
            self._supported_lang = self.SUPPORTED_LANGUAUE

    def _check_executable(self, executable):
        executable_path = find_executable(executable)
        found = executable_path is not None
        return found
    
    def _estimate_speech_duration(self, words):
        """
        Estimate speech duration based on word count and average speaking rate.
        
        :param words: text to be spoken
        :type words: str
        :return: estimated duration in seconds
        :rtype: float
        """
        # Average speaking rate is about 150-200 words per minute
        # We'll use 175 WPM as a reasonable estimate
        word_count = len(words.split())
        if word_count == 0:
            return 0.5  # Minimum duration for short sounds/punctuation
        
        # Add some buffer time for processing and audio playback
        estimated_seconds = (word_count / 175) * 60 + 0.5
        return estimated_seconds
    
    def is_speaking(self):
        """
        Check if TTS is currently speaking.
        
        :return: True if currently speaking, False otherwise
        :rtype: bool
        """
        return self._is_speaking
    
    def get_speech_duration(self):
        """
        Get the duration of current speech session.
        
        :return: duration in seconds since speech started, 0 if not speaking
        :rtype: float
        """
        if self._is_speaking and self._speech_start_time:
            return time.time() - self._speech_start_time
        return 0
    
    def get_queue_length(self):
        """
        Get the number of speech items in the queue.
        
        :return: number of pending speech items
        :rtype: int
        """
        return len(self._speech_queue)
    
    def wait_for_completion(self, timeout=None):
        """
        Wait for all speech to complete.
        
        :param timeout: maximum time to wait in seconds, None for no timeout
        :type timeout: float or None
        :return: True if completed, False if timed out
        :rtype: bool
        """
        start_wait = time.time()
        while self._is_speaking:
            if timeout and (time.time() - start_wait) > timeout:
                return False
            time.sleep(0.1)
        return True
    
    def stop_speech(self):
        """
        Stop current speech and clear queue.
        """
        with self._speech_lock:
            self._is_speaking = False
            self._speech_queue.clear()
            # Kill any running audio processes
            try:
                subprocess.run(['pkill', '-f', 'aplay'], check=False)
                subprocess.run(['pkill', '-f', 'pico2wave'], check=False)
                subprocess.run(['pkill', '-f', 'espeak'], check=False)
            except Exception:
                pass
    
    def _track_speech_completion(self, cmd, estimated_duration):
        """
        Track speech completion and update status.
        
        :param cmd: the command that was executed
        :type cmd: str
        :param estimated_duration: estimated speech duration
        :type estimated_duration: float
        """
        # Wait for the estimated duration plus a small buffer
        time.sleep(estimated_duration + 0.5)
        
        with self._speech_lock:
            # Remove completed speech from queue
            if self._speech_queue:
                completed = self._speech_queue.pop(0)
                self._debug(f"Completed speech: {completed['words'][:50]}...")
            
            # Check if we're done speaking
            if len(self._speech_queue) == 0:
                self._is_speaking = False
                self._speech_start_time = None

    def say(self, words, blocking=False):
        """
        Say words.

        :param words: words to say.
        :type words: str
        :param blocking: if True, wait for the speech to complete before returning
        :type blocking: bool
        :return: estimated duration of speech in seconds (if available)
        :rtype: float
        """
        with self._speech_lock:
            # Add to speech queue
            speech_info = {
                'words': words,
                'start_time': time.time(),
                'estimated_duration': self._estimate_speech_duration(words)
            }
            self._speech_queue.append(speech_info)
            
            # Mark as speaking
            if not self._is_speaking:
                self._is_speaking = True
                self._speech_start_time = time.time()
        
        # Execute the TTS
        if self.engine == self.PICO2WAVE:
            duration = self.pico2wave(words, blocking)
        elif self.engine == self.ESPEAK:
            duration = self.espeak(words, blocking)
        elif self.engine == self.ESPEAK_NG:
            duration = self.espeak_ng(words, blocking)
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")
        
        # If blocking, wait for completion
        if blocking:
            self.wait_for_completion()
            
        return speech_info['estimated_duration']

    def _espeak(self, engine, words, blocking=False):
        """
        Say words with espeak.

        :param words: words to say.
        :type words: str
        :param blocking: if True, wait for speech to complete
        :type blocking: bool
        :return: estimated duration
        :rtype: float
        """
        self._debug(f'{engine}: [{words}]')
        if not self._check_executable(engine):
            self._debug(f'{engine} is busy. Pass')
            return 0

        # Escape quotes in the words to prevent command injection
        escaped_words = words.replace('"', '\\"')
        
        # Calculate effective amplitude with volume gain
        effective_amp = min(200, int(self._amp * self._volume_gain))
        
        if blocking:
            cmd = f'{engine} -v{self._lang} -a{effective_amp} -s{self._speed} -g{self._gap} -p{self._pitch} "{escaped_words}" --stdout | aplay 2>/dev/null'
        else:
            cmd = f'{engine} -v{self._lang} -a{effective_amp} -s{self._speed} -g{self._gap} -p{self._pitch} "{escaped_words}" --stdout | aplay 2>/dev/null &'
        
        # Start a thread to track completion
        threading.Thread(target=self._track_speech_completion, 
                        args=(cmd, self._estimate_speech_duration(words)), 
                        daemon=True).start()
        
        status, result = run_command(cmd)
        if len(result) != 0:
            raise Exception(f'tts-espeak:\n\t{result}')
        self._debug(f'command: {cmd}')
        
        return self._estimate_speech_duration(words)

    def espeak(self, words, blocking=False):
        return self._espeak('espeak', words, blocking)

    def espeak_ng(self, words, blocking=False):
        return self._espeak('espeak-ng', words, blocking)

    def pico2wave(self, words, blocking=False):
        """
        Say words with pico2wave.

        :param words: words to say.
        :type words: str
        :param blocking: if True, wait for speech to complete
        :type blocking: bool
        :return: estimated duration
        :rtype: float
        """
        import tempfile
        
        self._debug(f'pico2wave: [{words}]')
        if not self._check_executable('pico2wave'):
            self._debug('pico2wave is busy. Pass')
            return 0

        # Create a unique temporary file for this TTS call to avoid race conditions
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', prefix='tts_')
        os.close(temp_fd)  # Close the file descriptor, we only need the path
        
        try:
            # Escape quotes in the words to prevent command injection
            escaped_words = words.replace('"', '\\"')
            
            # Apply volume gain using sox if not 1.0
            if self._volume_gain != 1.0:
                temp_loud_path = f"{temp_path}.loud.wav"
                if blocking:
                    cmd = f'pico2wave -l {self._lang} -w "{temp_path}" "{escaped_words}" && sox "{temp_path}" "{temp_loud_path}" vol {self._volume_gain} 2>/dev/null && aplay "{temp_loud_path}" 2>/dev/null && rm -f "{temp_path}" "{temp_loud_path}"'
                else:
                    cmd = f'pico2wave -l {self._lang} -w "{temp_path}" "{escaped_words}" && sox "{temp_path}" "{temp_loud_path}" vol {self._volume_gain} 2>/dev/null && aplay "{temp_loud_path}" 2>/dev/null && rm -f "{temp_path}" "{temp_loud_path}" &'
            else:
                if blocking:
                    cmd = f'pico2wave -l {self._lang} -w "{temp_path}" "{escaped_words}" && aplay "{temp_path}" 2>/dev/null && rm -f "{temp_path}"'
                else:
                    cmd = f'pico2wave -l {self._lang} -w "{temp_path}" "{escaped_words}" && aplay "{temp_path}" 2>/dev/null && rm -f "{temp_path}" &'
            
            # Start a thread to track completion
            duration = self._estimate_speech_duration(words)
            threading.Thread(target=self._track_speech_completion, 
                            args=(cmd, duration), 
                            daemon=True).start()
            
            status, result = run_command(cmd)
            if len(result) != 0:
                raise Exception(f'tts-pico2wave:\n\t{result}')
            self._debug(f'command: {cmd}')
            
            return duration
            
        except Exception as e:
            # Clean up temp file if there's an error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise e

    def lang(self, *value):
        """
        Set/get language. leave empty to get current language.

        :param value: language.
        :type value: str
        """
        if len(value) == 0:
            return self._lang
        elif len(value) == 1:
            v = value[0]
            if v in self._supported_lang:
                self._lang = v
                return self._lang
        raise ValueError(
            f'Arguement "{value}" is not supported. run tts.supported_lang to get supported language type.'
        )

    def supported_lang(self):
        """
        Get supported language.

        :return: supported language.
        :rtype: list
        """
        return self._supported_lang

    def espeak_params(self, amp=None, speed=None, gap=None, pitch=None):
        """
        Set espeak parameters.

        :param amp: amplitude.
        :type amp: int
        :param speed: speed.
        :type speed: int
        :param gap: gap.
        :type gap: int
        :param pitch: pitch.
        :type pitch: int
        """
        if amp == None:
            amp = self._amp
        if speed == None:
            speed = self._speed
        if gap == None:
            gap = self._gap
        if pitch == None:
            pitch = self._pitch

        if amp not in range(0, 200):
            raise ValueError(f'Amp should be in 0 to 200, not "{amp}"')
        if speed not in range(80, 260):
            raise ValueError(f'speed should be in 80 to 260, not "{speed}"')
        if pitch not in range(0, 99):
            raise ValueError(f'pitch should be in 0 to 99, not "{pitch}"')
        self._amp = amp
        self._speed = speed
        self._gap = gap
        self._pitch = pitch

    def volume(self, gain=None):
        """
        Set/get volume gain multiplier.

        :param gain: volume gain multiplier (1.0 = normal, 2.0 = double volume, 0.5 = half volume)
        :type gain: float
        :return: current volume gain if no parameter given
        :rtype: float
        """
        if gain is None:
            return self._volume_gain
        
        if gain <= 0:
            raise ValueError(f'Volume gain should be greater than 0, not "{gain}"')
        if gain > 5.0:
            raise ValueError(f'Volume gain should not exceed 5.0 to prevent audio distortion, not "{gain}"')
        
        self._volume_gain = gain
        return self._volume_gain
    
    def system_volume(self, volume_percent=None):
        """
        Set/get system audio volume using amixer.
        
        :param volume_percent: system volume percentage (0-100)
        :type volume_percent: int
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if volume_percent is None:
            # Get current volume
            try:
                status, result = run_command("amixer get PCM | grep -o '[0-9]*%' | head -1")
                if status == 0 and result:
                    return int(result.strip().replace('%', ''))
            except:
                pass
            return None
        
        # Set volume
        if not (0 <= volume_percent <= 100):
            raise ValueError(f'System volume should be between 0-100, not "{volume_percent}"')
        
        try:
            status, result = run_command(f"amixer sset PCM {volume_percent}%")
            return status == 0
        except:
            return False

def _get_supported_lang_espeak(name):
    """
    Get supported language for espeak.

    :param name: espeak command name.
    :return: supported language.
    :rtype: list
    """
    status, result = run_command(f"{name} --voices")
    supported_lang = []
    if not status:
        first = True
        for line in result.split('\n'):
            if first or not line:
                first = False
                continue
            lang = [v for v in line.split() if v][1]
            supported_lang.append(lang)
    return supported_lang

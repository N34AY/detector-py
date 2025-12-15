#!/usr/bin/env python3
"""
Generate simple audio alert sounds for detection system
Creates beep sounds for motion and person detection
"""

import numpy as np
import wave
import struct
import os

def create_beep_sound(filename, frequency, duration, sample_rate=44100):
    """Create a simple beep sound and save as WAV file"""
    
    # Generate sine wave
    frames = int(duration * sample_rate)
    arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
    
    # Apply envelope to avoid clicks
    envelope = np.ones(frames)
    fade_frames = int(0.1 * sample_rate)  # 0.1 second fade
    envelope[:fade_frames] = np.linspace(0, 1, fade_frames)
    envelope[-fade_frames:] = np.linspace(1, 0, fade_frames)
    
    arr *= envelope
    
    # Convert to 16-bit integers
    arr = np.clip(arr * 32767, -32768, 32767)
    arr = arr.astype(np.int16)
    
    # Save as WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(arr.tobytes())
    
    print(f"Created {filename}: {frequency}Hz beep for {duration}s")

def create_multi_tone_beep(filename, frequencies, duration, sample_rate=44100):
    """Create a beep with multiple frequencies (chord)"""
    
    frames = int(duration * sample_rate)
    arr = np.zeros(frames)
    
    # Add each frequency
    for freq in frequencies:
        wave_data = np.sin(2 * np.pi * freq * np.linspace(0, duration, frames))
        arr += wave_data
    
    # Normalize
    arr /= len(frequencies)
    
    # Apply envelope
    envelope = np.ones(frames)
    fade_frames = int(0.05 * sample_rate)  # 0.05 second fade
    envelope[:fade_frames] = np.linspace(0, 1, fade_frames)
    envelope[-fade_frames:] = np.linspace(1, 0, fade_frames)
    
    arr *= envelope
    
    # Convert to 16-bit integers
    arr = np.clip(arr * 32767, -32768, 32767)
    arr = arr.astype(np.int16)
    
    # Save as WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(arr.tobytes())
    
    print(f"Created {filename}: {frequencies}Hz chord for {duration}s")

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    os.makedirs("web/static/sounds", exist_ok=True)
    
    # Create motion detection sound - single low tone
    create_beep_sound("web/static/sounds/motion.wav", 440, 0.3)  # A4 note, 0.3 seconds
    
    # Create person detection sound - higher pitched double beep
    create_multi_tone_beep("web/static/sounds/person.wav", [660, 880], 0.5)  # E5 + A5 chord, 0.5 seconds
    
    # Create test sound - pleasant chord
    create_multi_tone_beep("web/static/sounds/test.wav", [523, 659, 784], 0.4)  # C-E-G major chord
    
    print("\nSound files created successfully in web/static/sounds/")
    print("- motion.wav: Low tone for motion detection")
    print("- person.wav: Higher chord for person detection")
    print("- test.wav: Pleasant chord for testing")
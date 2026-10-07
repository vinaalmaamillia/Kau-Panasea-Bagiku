import math
import numpy as np
import wave
import struct

from mido import Message, MidiFile, MidiTrack

#1. PARAMETER GEOMETRI BANCHOFF
R, r = 2.0, 1.0
x_min, x_max = -(R + r), (R + r)

#2. TANGGA NADA PELOG SLENDRO

saron_pelog_dict = {
    '1': 60, '2': 62, '3': 64, '4': 65, '5': 67,
    '6': 69, '7': 71, '1!': 72, '2!': 74, '0': 0,
}

rek_ayo_rek_melody = [
    '3', '2', '1', '3', '0',
    '3', '2', '3', '2', '1', '3', '1', '2', '0',
    '2', '1', '1', '2', '0',
    '2', '1', '2', '1', '1', '2', '1', '3', '0',
]

rhythm_pattern = [
    0.7, 0.3, 0.5, 1.0, 1.0,
    0.5, 0.5, 0.5, 0.5, 0.55, 0.45, 0.45, 2.0, 2.0,
    0.7, 0.3, 0.5, 1.0, 1.0,
    0.5, 0.5, 0.5, 0.5, 0.55, 0.45, 0.45, 2.0, 2.0,
]
target_melody = rek_ayo_rek_melody * 2
target_rhythm = rhythm_pattern * 2
slendro_keys = list(saron_pelog_dict.keys())
N = len(target_melody)

#3. INVERSI BANCHOFF
def compute_exact_v(u_i, target_note):
    idx = slendro_keys.index(target_note)
    x_target = x_min + (idx / (len(slendro_keys) - 1)) * (x_max - x_min)
    cos_u = math.cos(u_i)
    if abs(cos_u) < 1e-6:
        cos_u = 1e-6 if cos_u >= 0 else -1e-6
    val = (x_target / cos_u - R) / r
    val_clamped = max(-1.0, min(1.0, val))
    return math.acos(val_clamped)

u_vals = np.linspace(0, 2 * np.pi, N, endpoint=False)
v_vals = [compute_exact_v(u_vals[i], target_melody[i]) for i in range(N)]

#4. PEMETAAN KE PARAMETER MUSIK
midi_notes = []
velocities = []
durations = []
w_vals = []

for i in range(N):
    u = u_vals[i]
    v = v_vals[i]

    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v) * np.cos(u / 2)
    w = r * np.sin(v) * np.sin(u / 2)

    idx = int(np.round((x - x_min) / (x_max - x_min) * (len(slendro_keys) - 1)))
    idx = max(0, min(len(slendro_keys) - 1, idx))
    note_key = slendro_keys[idx]
    midi_notes.append(saron_pelog_dict[note_key])

    vel = int(np.round(50 + (z - (-r)) / (2 * r) * 60))
    velocities.append(max(40, min(110, vel)))

    y_norm = (y - (-(R + r))) / (2 * (R + r))
    rhythm_index = int(np.floor(y_norm * 4))
    rhythm_index = max(0, min(3, rhythm_index))
    rhythm_map = [0.25, 0.375, 0.5, 0.75]

    base_duration = target_rhythm[i]
    y_variation = rhythm_map[rhythm_index]
    weighted_dur = 0.7 * base_duration + 0.3 * y_variation
    durations.append(weighted_dur)

    w_vals.append(w)

#5. EKSPOR MIDI
tick_per_beat = 480
tempo_bpm = 120

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)
track.append(Message('program_change', program=12, time=0))

def duration_to_ticks(dur_beat):
    return int(dur_beat * tick_per_beat)

for i in range(N):
    note = midi_notes[i]
    vel = velocities[i]
    dur_ticks = duration_to_ticks(durations[i])

    if note > 0:
        track.append(Message('note_on', note=note, velocity=vel, time=0))
        track.append(Message('note_off', note=note, velocity=0, time=dur_ticks))
    else:
        track.append(Message('note_on', note=60, velocity=0, time=dur_ticks))

mid.save('rek_ayo_rek_banchoff.mid')
print("✅ File MIDI berhasil dibuat: 'rek_ayo_rek_banchoff.mid'")

#6. SINTESIS AUDIO WAV (TANPA SCIPY)
sample_rate = 44100
seconds_per_beat = 60.0 / tempo_bpm

def synthesize_wave(freq, amp, duration, w_val, sr=44100):
    num_samples = int(sr * duration)
    t = np.linspace(0, duration, num_samples, False)

    #Gelombang dengan harmonik (suara saron)
    synth_wave = amp * (
        0.8 * np.sin(2 * np.pi * freq * t) +
        0.3 * np.sin(2 * np.pi * (2 * freq) * t) +
        0.15 * np.sin(2 * np.pi * (3 * freq) * t)
    )

    #Envelope ADSR
    attack_samples = int(0.01 * sr)
    decay_samples = int(0.02 * sr)
    release_samples = int(0.03 * sr)

    envelope = np.ones(len(t))
    if len(t) > attack_samples:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    if len(t) > attack_samples + decay_samples:
        decay_end = min(attack_samples + decay_samples, len(t))
        envelope[attack_samples:decay_end] = np.linspace(1, 0.7, decay_end - attack_samples)
    if len(t) > release_samples:
        envelope[-release_samples:] = np.linspace(0.7, 0, release_samples)

    synth_wave = synth_wave * envelope

    #Trigger Gong/Bonang dari koordinat w(u)
    w_threshold = 0.7 * r
    if w_val > w_threshold:
        gong_freq = 65.0
        gong_amp = 0.35 * amp
        gong_wave = gong_amp * np.sin(2 * np.pi * gong_freq * t) * np.exp(-1.5 * t)
        synth_wave = synth_wave + gong_wave
    elif w_val < -w_threshold:
        bonang_freq = 440.0 * (2 ** ((74 - 69) / 12.0))
        bonang_amp = 0.25 * amp
        bonang_wave = bonang_amp * np.sin(2 * np.pi * bonang_freq * t) * np.exp(-4 * t)
        synth_wave = synth_wave + bonang_wave

    max_val = np.max(np.abs(synth_wave))
    if max_val > 0:
        synth_wave = synth_wave / max_val

    return synth_wave

#Sintesis semua nada
audio_samples = []

for i in range(N):
    m = midi_notes[i]
    if m == 0:  # Rest
        duration = durations[i] * seconds_per_beat
        silence = np.zeros(int(sample_rate * duration), dtype=np.float32)
        audio_samples.extend(silence)
        continue

    freq = 440.0 * (2 ** ((m - 69) / 12.0))
    amp = velocities[i] / 127.0
    duration = durations[i] * seconds_per_beat
    w_val = w_vals[i]

    synth_wave = synthesize_wave(freq, amp, duration, w_val)
    audio_samples.extend(synth_wave)

    #Jeda antar nada
    rest_duration = 0.015 * seconds_per_beat
    silence = np.zeros(int(sample_rate * rest_duration), dtype=np.float32)
    audio_samples.extend(silence)

#Konversi ke numpy array
audio_array = np.array(audio_samples, dtype=np.float32)

#Normalisasi
max_val = np.max(np.abs(audio_array))
if max_val > 0:
    audio_array = audio_array / max_val

#Konversi ke 16-bit integer
audio_int16 = np.int16(audio_array * 32767)

#7. SAVE WAV MENGGUNAKAN WAVE LIBRARY STANDAR (TANPA SCIPY)
def save_wav(filename, data, sample_rate):
    """Menyimpan file WAV tanpa scipy"""
    data_bytes = data.tobytes()

    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit = 2 bytes
        wav_file.setframerate(sample_rate)
        wav_file.setnframes(len(data))
        wav_file.writeframes(data_bytes)

save_wav('rek_ayo_rek_banchoff.wav', audio_int16, sample_rate)
print("✅ File WAV berhasil dibuat: 'rek_ayo_rek_banchoff.wav'")

#8. ANALISIS HASIL
dt = 1.0 / sample_rate
total_energy = np.sum(audio_array ** 2) * dt
rms = np.sqrt(np.mean(audio_array ** 2))
db_level = 20 * np.log10(rms + 1e-10)

print("\n" + "="*50)
print("📊 HASIL ANALISIS")
print("="*50)
print(f"Total energi akustik: {total_energy:.4f}")
print(f"RMS: {rms:.4f}")
print(f"Level dB: {db_level:.2f} dB")
print(f"Jumlah nada: {N}")
print(f"Rentang MIDI: {min(midi_notes)} - {max(midi_notes)}")
print(f"Rata-rata velocity: {np.mean(velocities):.1f}")
print("="*50)

#Coba visualisasi jika matplotlib terinstal
try:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Parameterisasi Klein Bottle 4D Banchoff - Rek Ayo Rek')

    axes[0, 0].plot(u_vals, [(R + r * np.cos(v)) * np.cos(u_vals[i]) for i, v in enumerate(v_vals)], 'b-')
    axes[0, 0].set_title('Koordinat x(u): Pitch')
    axes[0, 0].grid(True)

    axes[0, 1].plot(u_vals, v_vals, 'r-')
    axes[0, 1].set_title('Lintasan v(u)')
    axes[0, 1].grid(True)

    axes[1, 0].plot(u_vals, velocities, 'g-')
    axes[1, 0].set_title('Koordinat z(u): Velocity')
    axes[1, 0].grid(True)

    axes[1, 1].plot(u_vals, w_vals, 'm-')
    axes[1, 1].axhline(y=0.7*r, color='k', linestyle='--', label='Threshold Gong')
    axes[1, 1].axhline(y=-0.7*r, color='k', linestyle='--', label='Threshold Bonang')
    axes[1, 1].set_title('Koordinat w(u): Aksen')
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig('klein_bottle_analysis.png', dpi=150)
    print("✅ Visualisasi: 'klein_bottle_analysis.png'")

except ImportError:
    print("⚠️ Matplotlib tidak terinstal, lewati visualisasi")
except Exception as e:
    print(f"⚠️ Error visualisasi: {e}")

print("\n🎵 Selesai! File audio siap diputar.")
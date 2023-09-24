import discord
from discord.ext import commands
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import fft
from pydub import AudioSegment  # You'll need to install the pydub library
import os
from scipy.io.wavfile import write

# Dictionary to store user-specific frequency spectrum data
user_spectrum_data = {}

# Defines your intents and enable message content
intents = discord.Intents.default()
intents.typing = False  # Disable typing notifications (optional)
intents.message_content = True  # Enable message content intent

# Creates a Discord bot instance with intents
bot = commands.Bot(command_prefix='!', intents=intents)


# Function to convert MP3 to WAV and generate the spectrum
def process_audio(file_path):
    # Converts MP3 to WAV
    audio = AudioSegment.from_mp3(file_path)
    wav_path = file_path.replace('.mp3', '.wav')
    audio.export(wav_path, format="wav")

    # Reads the WAV file and perform FFT analysis
    sample_rate, audio_data = wavfile.read(wav_path)
    
    # Converts audio_data to a NumPy array
    audio_data = np.array(audio_data, dtype=np.float64)  # Ensure it's a float64 array
    
    fft_result = fft(audio_data)
    
    # Cleans up temporary WAV file
    os.remove(wav_path)

    return fft_result


# Function to generate a waveform image
def generate_waveform_image(audio_data, user_id):
    # Creates a unique filename for each user based on their Discord ID
    image_path = f'waveform_{user_id}.png'

    plt.figure(figsize=(8, 4))
    plt.plot(audio_data)
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.title('Waveform')
    plt.savefig(image_path)
    plt.close()

    return image_path
   
def generate_spectrum_image(audio_data, user_id):
    # Creates a unique filename for each user based on their Discord ID
    image_path = f'spectrogram_{user_id}.png'

    plt.figure(figsize=(8, 4))
    plt.plot(np.abs(audio_data))
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')
    plt.title('Frequency Spectrum')
    plt.savefig(image_path)
    plt.close()

    return image_path
   

# Command to upload and process an MP3 file
@bot.command()
async def upload(ctx):
    if not ctx.message.attachments:
        await ctx.send("Please upload an MP3 file.")
        return

    user_id = ctx.author.id
    file = ctx.message.attachments[0]
    # Saves the file in the root folder
    file_path = file.filename
    
    await file.save(file_path)

    fft_result = process_audio(file_path)
    user_spectrum_data[user_id] = fft_result

    spectrum_image_path = generate_spectrum_image(fft_result, user_id)
    waveform_image_path = generate_waveform_image(fft_result, user_id)

   
    # Sends images and messages
    spectrum_file = discord.File(spectrum_image_path)
    waveform_file = discord.File(waveform_image_path)

    await ctx.send("Frequency spectrum generated!")
    await ctx.send("Waveform:")
    await ctx.send(file=waveform_file)
    await ctx.send("Frequency Spectrum:")
    await ctx.send(file=spectrum_file) 



@bot.command()
async def spectrum(ctx):
    user_id = ctx.author.id
    if user_id in user_spectrum_data:
        image_path = generate_spectrum_image(user_spectrum_data[user_id], user_id)
        file = discord.File(image_path)
        await ctx.send(file=file)
    else:
        await ctx.send("No spectrum data found. Please upload an MP3 file first.")

# Command to delete a specific frequency component
@bot.command()
async def delete(ctx, frequency_to_delete: int):
    user_id = ctx.author.id
    if user_id in user_spectrum_data:
        fft_result = user_spectrum_data[user_id]
        fft_result[frequency_to_delete] = 0
        user_spectrum_data[user_id] = fft_result

        # Generates a new spectrum image based on the modified FFT data
        spectrum_image_path = generate_spectrum_image(fft_result, user_id)

        # Sends the updated spectrum image back to Discord
        spectrum_file = discord.File(spectrum_image_path)
        await ctx.send(f"Frequency component at {frequency_to_delete} Hz deleted. Updated Spectrum:")
        await ctx.send(file=spectrum_file)
    else:
        await ctx.send("No spectrum data found. Please upload an MP3 file first.")


# Command to alter a specific frequency component
@bot.command()
async def alter(ctx, frequency_to_alter: int, new_amplitude: float):
    user_id = ctx.author.id
    if user_id in user_spectrum_data:
        fft_result = user_spectrum_data[user_id]
        fft_result[frequency_to_alter] *= new_amplitude
        user_spectrum_data[user_id] = fft_result

        # Generates a new spectrum image based on the modified FFT data
        spectrum_image_path = generate_spectrum_image(fft_result, user_id)

        # Sends the updated spectrum image back to Discord
        spectrum_file = discord.File(spectrum_image_path)
        await ctx.send(f"Frequency component at {frequency_to_alter} Hz altered. Updated Spectrum:")
        await ctx.send(file=spectrum_file)
    else:
        await ctx.send("No spectrum data found. Please upload an MP3 file first.")


# Run the bot
bot.run('Enter Your Token')

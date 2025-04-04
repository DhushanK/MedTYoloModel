import pygame
import time

# Initialize pygame mixer with stereo output
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# Create a channel to play the sound
channel = pygame.mixer.Channel(0)  # Use a single stereo channel

# Boolean variable (Set dynamically)
car = False  # Change this to False to play in the right ear


# Function to control sound direction
def play_sound(car: bool, source: str):
    # Load the sound file (Make sure it's a WAV file)
    sound = pygame.mixer.Sound(f"Sounds/{source}")
    if car:
        left_vol, right_vol = 1.0, 0.0  # Play in the LEFT ear
    else:
        left_vol, right_vol = 0.0, 1.0  # Play in the RIGHT ear

    # Set stereo volume
    channel.set_volume(left_vol, right_vol)

    # Play sound
    channel.play(sound)
    print(".")


# Play the sound 3 times
if __name__ == "__main__":
    for _ in range(3):
        play_sound(car, "sound1.mp3")

        # Wait for the sound to finish before playing again
        while channel.get_busy():
            time.sleep(0.01)

    print("Finished playing audio 3 times.")

    # Cleanup
    pygame.mixer.quit()

import pygame
import boto3
import os
import tempfile
from botocore.exceptions import ClientError
from dotenv import load_dotenv


load_dotenv()
aws_access_key = os.environ['AWS_ACCESS_KEY_ID']
aws_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
aws_region = os.environ['AWS_REGION']


def upload_audio_to_s3(local_file_path, bucket_name, s3_key):
    """Upload an audio file to S3."""
    s3_client = boto3.client('s3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )
    
    try:
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        return True
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False

upload_audio_to_s3("./assets/audio/sfx/hit_1.MP3", "bvr-game", "hit_1.MP3")
upload_audio_to_s3("./assets/audio/sfx/hit_1.MP3", "bvr-game", "hit_2.MP3")
upload_audio_to_s3("./assets/audio/music/hit_1.MP3", "bvr-game", "El Bosque Sombrío.mp3")

class AudioManager:
    def __init__(self, bucket_name):
        """
        Initialize the AudioManager.
        - Connects to an AWS S3 bucket to download audio files.
        - Sets up Pygame's mixer for playing audio.
        - Creates a temporary directory to store downloaded files.
        """
        self.bucket_name = bucket_name  # Name of the S3 bucket to fetch audio from
        self.s3_client = boto3.client('s3',  # Initialize S3 client using boto3
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),  # AWS credentials from environment variables
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        self.audio_cache = {}  # Dictionary to cache loaded sounds
        self.temp_dir = tempfile.mkdtemp()  # Create a temporary directory for storing downloaded files
        
        # Initialize Pygame's mixer for audio playback
        pygame.mixer.init()

    def download_audio(self, s3_key):
        """
        Download an audio file from S3 and save it locally.
        - s3_key: Path of the audio file in the S3 bucket.
        Returns the local file path or None if there's an error.
        """
        local_path = os.path.join(self.temp_dir, os.path.basename(s3_key))  # Define local save path
        
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)  # Download file from S3
            return local_path  # Return the local file path
        except ClientError as e:  # Handle download errors
            print(f"Error downloading audio: {e}")
            return None  # Return None if download fails

    def load_sound(self, s3_key):
        """
        Load a sound effect from S3 into the Pygame mixer.
        - s3_key: Path of the audio file in the S3 bucket.
        Returns the Pygame Sound object or None if there's an error.
        """
        if s3_key in self.audio_cache:  # Check if the sound is already cached
            return self.audio_cache[s3_key]

        local_path = self.download_audio(s3_key)  # Download the file if not cached
        if local_path:
            sound = pygame.mixer.Sound(local_path)  # Load the sound into Pygame
            self.audio_cache[s3_key] = sound  # Cache the loaded sound
            return sound
        return None  # Return None if loading fails

    def load_music(self, s3_key):
        """
        Load a background music file from S3 into the Pygame mixer.
        - s3_key: Path of the audio file in the S3 bucket.
        Returns True if the music is loaded successfully, False otherwise.
        """
        local_path = self.download_audio(s3_key)  # Download the file
        if local_path:
            pygame.mixer.music.load(local_path)  # Load the music into the mixer
            return True
        return False

    def play_music(self, loops=-1):
        """
        Play the loaded background music.
        - loops: Number of times to loop the music (-1 for infinite loop).
        """
        pygame.mixer.music.play(loops)

    def stop_music(self):
        """Stop the currently playing background music."""
        pygame.mixer.music.stop()

    def cleanup(self):
        """
        Clean up temporary files created during execution.
        - Deletes the temporary directory and all its contents.
        """
        import shutil
        shutil.rmtree(self.temp_dir)  # Remove the temporary directory and its contents





# Initialize the audio manager
audio_manager = AudioManager('my-game-assets-bucket')

# Load and play background music
audio_manager.load_music('audio/music/background_music.mp3')
audio_manager.play_music()

# Load sound effects
hit_sound = audio_manager.load_sound('audio/sfx/hit_sound.wav')

# Play sound effects when needed
hit_sound.play()

# When quitting the game
audio_manager.stop_music()
audio_manager.cleanup()
import os
import random
import torch
import gradio as gr
import shutil
from datetime import datetime
from kokoro import KModel, KPipeline
from tqdm import tqdm
from scipy.io.wavfile import write
import warnings

# Get the application root directory
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"Application directory: {app_dir}")

# Always use system cache directory
system_cache = os.path.join(app_dir, 'system', 'cache')
hf_home = os.path.join(system_cache, 'HF_HOME')
torch_home = os.path.join(system_cache, 'TORCH_HOME')

# Create directories if they don't exist
if not os.path.exists(system_cache):
    os.makedirs(system_cache, exist_ok=True)
    print(f"Created system cache directory: {system_cache}")

if not os.path.exists(hf_home):
    os.makedirs(hf_home, exist_ok=True)
    print(f"Created HF_HOME directory: {hf_home}")

if not os.path.exists(torch_home):
    os.makedirs(torch_home, exist_ok=True)
    print(f"Created TORCH_HOME directory: {torch_home}")

# Set environment variables to use system cache
os.environ["HF_HOME"] = hf_home
os.environ["TORCH_HOME"] = torch_home
os.environ["TRANSFORMERS_CACHE"] = hf_home
os.environ["HF_DATASETS_CACHE"] = hf_home
os.environ["HF_HUB_CACHE"] = hf_home
os.environ["HUGGINGFACE_HUB_CACHE"] = hf_home
os.environ["HF_ASSETS_CACHE"] = hf_home
os.environ["HUGGINGFACE_ASSETS_CACHE"] = hf_home
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# Force the huggingface_hub library to use our cache directory
try:
    from huggingface_hub import constants
    # Override the default cache paths in the huggingface_hub library
    constants.HF_HUB_CACHE = hf_home
    constants.HF_HOME = hf_home
    constants.HUGGINGFACE_HUB_CACHE = hf_home
    constants.hf_cache_home = hf_home
    constants.default_cache_path = os.path.join(hf_home, "hub")
    print("Successfully overrode huggingface_hub cache constants")
except Exception as e:
    print(f"Warning: Could not override huggingface_hub cache constants: {str(e)}")

# Set phonemizer to use local directory for espeak-ng.dll
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = os.path.join(app_dir, 'system', 'Lib', 'site-packages', 'espeakng_loader', 'espeak-ng.dll')

# Print cache locations for debugging
print(f"Using HF_HOME: {os.environ['HF_HOME']}")
print(f"Using TORCH_HOME: {os.environ['TORCH_HOME']}")

print(f"Using cache directory: {os.environ['HF_HOME']}")

torch.nn.utils.parametrize = torch.nn.utils.parametrizations.weight_norm
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")

# Check if CUDA is available
CUDA_AVAILABLE = torch.cuda.is_available()
if CUDA_AVAILABLE:
    print("CUDA is available. Will use GPU acceleration.")
else:
    print("CUDA is not available. Using CPU mode.")

try:
    # Check if models exist in the system cache
    model_path = os.path.join(hf_home, 'hub', 'models--hexgrad--Kokoro-82M')

    # Function to check if models are complete
    def is_model_complete(path):
        # Check if the directory exists
        if not os.path.exists(path):
            print(f"Model directory does not exist: {path}")
            return False

        # Look for key model files
        try:
            model_files = [f for f in os.listdir(path) if f.endswith('.bin') or f.endswith('.json')]
            if len(model_files) > 0:
                print(f"Found {len(model_files)} model files in {path}")
                return True
            else:
                print(f"No model files found in {path}")
                return False
        except Exception as e:
            print(f"Error checking {path}: {str(e)}")
            return False

    # Check if models exist
    if not is_model_complete(model_path):
        # Check if the marker file exists
        marker_file = os.path.join(model_path, 'DOWNLOAD_COMPLETE')
        if os.path.exists(marker_file):
            print(f"Model marker file found in: {model_path}")
            print("Using cached models - offline mode enabled")
        else:
            print("First run detected, downloading models...")
            # Temporarily disable offline mode to allow downloads
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
            os.environ.pop("HF_HUB_OFFLINE", None)
            print(f"Models will be downloaded to: {model_path}")
    else:
        print(f"Models found in: {model_path}")
        print("Using cached models - offline mode enabled")

    # Load models with environment variables controlling cache location
    if CUDA_AVAILABLE:
        # Use GPU if available
        models = {True: KModel(repo_id="hexgrad/Kokoro-82M").to('cuda').eval(),
                 False: KModel(repo_id="hexgrad/Kokoro-82M").to('cpu').eval()}
        print("Model loaded to GPU.")
    else:
        # CPU only
        models = {True: KModel(repo_id="hexgrad/Kokoro-82M").to('cpu').eval(),
                 False: KModel(repo_id="hexgrad/Kokoro-82M").to('cpu').eval()}
        print("Model loaded to CPU.")

    # Load pipelines with environment variables controlling cache location
    pipelines = {lang_code: KPipeline(repo_id="hexgrad/Kokoro-82M", lang_code=lang_code, model=False) for lang_code in 'abpi'}
    pipelines['a'].g2p.lexicon.golds['kokoro'] = 'kˈOkəɹO'
    pipelines['b'].g2p.lexicon.golds['kokoro'] = 'kˈQkəɹQ'
    # Add try-except for Italian pipeline which might not have lexicon attribute
    try:
        if hasattr(pipelines['i'].g2p, 'lexicon'):
            pipelines['i'].g2p.lexicon.golds['kokoro'] = 'kˈkɔro'
        else:
            print("Warning: Italian pipeline g2p doesn't have lexicon attribute, skipping custom pronunciation")
    except Exception as e:
        print(f"Warning: Could not set custom pronunciation for Italian: {str(e)}")

    # Create marker file after successful loading
    print("Models were downloaded successfully. Creating marker file...")

    # Check if the model directory exists now
    if os.path.exists(model_path):
        try:
            # Create a marker file
            with open(os.path.join(model_path, 'DOWNLOAD_COMPLETE'), 'w') as f:
                f.write('Models downloaded successfully')
            print(f"Created marker file in: {model_path}")

            # List the contents of the model directory
            print(f"Contents of {model_path}:")
            for item in os.listdir(model_path):
                print(f"  - {item}")
        except Exception as e:
            print(f"Warning: Could not create marker file in {model_path}: {str(e)}")

    # Re-enable offline mode to prevent future download attempts
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"

except Exception as e:
    print(f"Error during model loading: {str(e)}")
    print("Attempting to load in online mode...")
    # If offline loading fails, try online mode
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    os.environ.pop("HF_HUB_OFFLINE", None)

    # Load models with environment variables controlling cache location
    if CUDA_AVAILABLE:
        # Use GPU if available
        models = {True: KModel(repo_id="hexgrad/Kokoro-82M").to('cuda').eval(),
                 False: KModel(repo_id="hexgrad/Kokoro-82M").to('cpu').eval()}
        print("Model loaded to GPU.")
    else:
        # CPU only
        models = {True: KModel(repo_id="hexgrad/Kokoro-82M").to('cpu').eval(),
                 False: KModel(repo_id="hexgrad/Kokoro-82M").to('cpu').eval()}
        print("Model loaded to CPU.")

    # Load pipelines with environment variables controlling cache location
    pipelines = {lang_code: KPipeline(repo_id="hexgrad/Kokoro-82M", lang_code=lang_code, model=False) for lang_code in 'abpi'}
    pipelines['a'].g2p.lexicon.golds['kokoro'] = 'kˈOkəɹO'
    pipelines['b'].g2p.lexicon.golds['kokoro'] = 'kˈQkəɹQ'
    # Add try-except for Italian pipeline which might not have lexicon attribute
    try:
        if hasattr(pipelines['i'].g2p, 'lexicon'):
            pipelines['i'].g2p.lexicon.golds['kokoro'] = 'kˈkɔro'
        else:
            print("Warning: Italian pipeline g2p doesn't have lexicon attribute, skipping custom pronunciation")
    except Exception as e:
        print(f"Warning: Could not set custom pronunciation for Italian: {str(e)}")

# Store loaded voices to avoid reloading
loaded_voices = {}

CHAR_LIMIT = 5000

# Use portable paths for output and custom voices folders
output_folder = os.path.join(app_dir, 'kokoro', 'outputs')
custom_voices_folder = os.path.join(app_dir, 'kokoro', 'custom_voices')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if not os.path.exists(custom_voices_folder):
    os.makedirs(custom_voices_folder)

CHOICES = {
    '🇺🇸 🚺 Heart ❤️': 'af_heart',
    '🇺🇸 🚺 Bella 🔥': 'af_bella',
    '🇺🇸 🚺 Nicole 🎧': 'af_nicole',
    '🇺🇸 🚺 Aoede': 'af_aoede',
    '🇺🇸 🚺 Kore': 'af_kore',
    '🇺🇸 🚺 Sarah': 'af_sarah',
    '🇺🇸 🚺 Nova': 'af_nova',
    '🇺🇸 🚺 Sky': 'af_sky',
    '🇺🇸 🚺 Alloy': 'af_alloy',
    '🇺🇸 🚺 Jessica': 'af_jessica',
    '🇺🇸 🚺 River': 'af_river',
    '🇺🇸 🚹 Michael': 'am_michael',
    '🇺🇸 🚹 Fenrir': 'am_fenrir',
    '🇺🇸 🚹 Puck': 'am_puck',
    '🇺🇸 🚹 Echo': 'am_echo',
    '🇺🇸 🚹 Eric': 'am_eric',
    '🇺🇸 🚹 Liam': 'am_liam',
    '🇺🇸 🚹 Onyx': 'am_onyx',
    '🇺🇸 🚹 Santa': 'am_santa',
    '🇺🇸 🚹 Adam': 'am_adam',
    '🇬🇧 🚺 Emma': 'bf_emma',
    '🇬🇧 🚺 Isabella': 'bf_isabella',
    '🇬🇧 🚺 Alice': 'bf_alice',
    '🇬🇧 🚺 Lily': 'bf_lily',
    '🇬🇧 🚹 George': 'bm_george',
    '🇬🇧 🚹 Fable': 'bm_fable',
    '🇬🇧 🚹 Lewis': 'bm_lewis',
    '🇬🇧 🚹 Daniel': 'bm_daniel',
    'PF 🚺 Dora': 'pf_dora',
    'PM 🚹 Alex': 'pm_alex',
    'PM 🚹 Santa': 'pm_santa',
    '🇮🇹 🚺 Sara': 'if_sara',
    '🇮🇹 🚹 Nicola': 'im_nicola',
}

# Function to get custom voices from the custom_voices folder
def get_custom_voices():
    custom_voices = {}
    if os.path.exists(custom_voices_folder):
        for file in os.listdir(custom_voices_folder):
            file_path = os.path.join(custom_voices_folder, file)
            # Check if it's a .pt file (PyTorch model file)
            if file.endswith('.pt') and os.path.isfile(file_path):
                voice_id = os.path.splitext(file)[0]  # Remove the .pt extension
                custom_voices[f'👤 Custom: {voice_id}'] = f'custom_{voice_id}'
    return custom_voices

# Update choices with custom voices
def update_voice_choices():
    updated_choices = CHOICES.copy()
    custom_voices = get_custom_voices()
    updated_choices.update(custom_voices)
    return updated_choices

def preload_voices():
    print("Preloading voices...")
    for voice_name, voice_id in CHOICES.items():
        print(f"Loading voice: {voice_name} ({voice_id})")
        pipeline = pipelines[voice_id[0]]
        try:
            voice_pack = pipeline.load_voice(voice_id)
            loaded_voices[voice_id] = voice_pack
            print(f"Successfully loaded voice: {voice_name}")
        except Exception as e:
            print(f"Error loading voice {voice_name}: {str(e)}")

    # Load custom voices if any
    custom_voices = get_custom_voices()
    for voice_name, voice_id in custom_voices.items():
        try:
            # Custom voices use the American English pipeline by default
            pipeline = pipelines['a']
            voice_file = f"{voice_id.split('_')[1]}.pt"
            voice_path = os.path.join(custom_voices_folder, voice_file)

            # Check if the file exists
            if not os.path.exists(voice_path):
                print(f"Custom voice file not found: {voice_file}")
                continue

            # Load the .pt file directly
            try:
                voice_pack = torch.load(voice_path, weights_only=True)
                loaded_voices[voice_id] = voice_pack
                print(f"Successfully loaded custom voice: {voice_name}")
            except Exception as e:
                print(f"Error loading custom voice {voice_name}: {str(e)}")
        except Exception as e:
            print(f"Error loading custom voice {voice_name}: {str(e)}")

    print(f"All voices preloaded successfully. Total voices in cache: {len(loaded_voices)}")

preload_voices()

def forward(ps, ref_s, speed):
    try:
        if CUDA_AVAILABLE:
            return models[True](ps, ref_s, speed)
        else:
            return models[False](ps, ref_s, speed)
    except Exception as e:
        print(f"Error with processing: {e}. Falling back to CPU.")
        return models[False](ps, ref_s, speed)

def generate_first(text, voice='af_heart', speed=1):
    text = text.strip()

    # Check if the voice is a display name from standard voices
    if voice in CHOICES:
        voice = CHOICES[voice]
    # Check if the voice is a custom voice display name
    elif voice.startswith('👤 Custom:'):
        custom_voices = get_custom_voices()
        if voice in custom_voices:
            voice = custom_voices[voice]
        else:
            raise gr.Error(f"Custom voice not found: {voice}")

    chunks = [text[i:i + CHAR_LIMIT] for i in range(0, len(text), CHAR_LIMIT)]

    audio_output = []
    ps_output = []

    # Determine if this is a custom voice
    is_custom = voice.startswith('custom_')

    # Use the appropriate pipeline
    if is_custom:
        pipeline = pipelines['a']  # Use American English pipeline for custom voices
    else:
        pipeline = pipelines[voice[0]]

    # Get voice from in-memory cache or load it
    if voice in loaded_voices:
        pack = loaded_voices[voice]
        print(f"Using cached voice: {voice}")
    else:
        print(f"Voice {voice} not found in cache, loading now...")
        if is_custom:
            # Load custom voice from the custom_voices folder
            voice_name = voice.split('_')[1]
            voice_file = f"{voice_name}.pt"
            voice_path = os.path.join(custom_voices_folder, voice_file)

            # Check if the file exists
            if not os.path.exists(voice_path):
                raise gr.Error(f"Custom voice file not found: {voice_file}")

            # Load the .pt file directly
            try:
                pack = torch.load(voice_path, weights_only=True)
            except Exception as e:
                raise gr.Error(f"Error loading custom voice: {str(e)}")
        else:
            pack = pipeline.load_voice(voice)
        loaded_voices[voice] = pack

    for chunk in tqdm(chunks, desc="Processing chunks", ncols=100):
        for _, ps, _ in pipeline(chunk, voice if not is_custom else None, speed):
            ref_s = pack[len(ps)-1]
            try:
                audio = forward(ps, ref_s, speed)
            except gr.exceptions.Error as e:
                gr.Warning(str(e))
                gr.Info('Retrying with CPU.')
                audio = models[False](ps, ref_s, speed)

            audio_output.append(torch.tensor(audio.numpy()))
            ps_output.append(ps)

    audio_combined = torch.cat(audio_output, dim=-1)

    audio_combined_numpy = audio_combined.detach().cpu().numpy()

    phoneme_sequence = '\n'.join(ps_output)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"audio_{timestamp}.wav"
    audio_filepath = os.path.join(output_folder, audio_filename)

    write(audio_filepath, 24000, audio_combined_numpy)

    return audio_filepath, phoneme_sequence

# Function to handle custom voice upload
def upload_custom_voice(files, voice_name):
    if not voice_name or not voice_name.strip():
        return "Please provide a name for your custom voice."

    # Sanitize voice name (remove spaces and special characters)
    voice_name = ''.join(c for c in voice_name if c.isalnum() or c == '_')

    if not voice_name:
        return "Invalid voice name. Please use alphanumeric characters."

    # Check if any files were uploaded
    if not files:
        return "Please upload a .pt voice file."

    # In Gradio, the file object structure depends on the file_count parameter
    # For file_count="single", files is the file path as a string
    file_path = files

    # Check if the uploaded file is a .pt file
    if not file_path.endswith('.pt'):
        return "Please upload a valid .pt voice file."

    # Copy the file to the custom_voices folder with the new name
    target_file = os.path.join(custom_voices_folder, f"{voice_name}.pt")

    # If file already exists, remove it
    if os.path.exists(target_file):
        os.remove(target_file)

    # Copy the uploaded file
    shutil.copy(file_path, target_file)

    # Try to load the voice to verify it works
    voice_id = f'custom_{voice_name}'

    try:
        # Load the .pt file directly
        voice_pack = torch.load(target_file, weights_only=True)

        # Verify that the voice pack is usable with the model
        # Check if it's a tensor or a list/tuple of tensors
        if not isinstance(voice_pack, (torch.Tensor, list, tuple)):
            raise ValueError("The voice file is not in the expected format (should be a tensor or list of tensors)")

        # If it's a list or tuple, check that it contains tensors
        if isinstance(voice_pack, (list, tuple)) and (len(voice_pack) == 0 or not isinstance(voice_pack[0], torch.Tensor)):
            raise ValueError("The voice file does not contain valid tensor data")

        loaded_voices[voice_id] = voice_pack
        return f"Custom voice '{voice_name}' uploaded and loaded successfully!"
    except Exception as e:
        # If loading fails, remove the file
        if os.path.exists(target_file):
            os.remove(target_file)
        return f"Error loading custom voice: {str(e)}"

# Function to handle custom voice upload and refresh lists
def upload_and_refresh(files, voice_name):
    result = upload_custom_voice(files, voice_name)

    # If upload was successful, clear the input fields
    if "successfully" in result:
        return result, get_custom_voice_list(), "", None
    else:
        return result, get_custom_voice_list(), voice_name, files

# Function to refresh the voice list
def refresh_voice_list():
    updated_choices = update_voice_choices()
    return gr.update(choices=list(updated_choices.keys()), value=list(updated_choices.keys())[0])

# Function to get the list of custom voices for the dataframe
def get_custom_voice_list():
    custom_voices = get_custom_voices()
    if not custom_voices:
        return [["No custom voices found", "N/A"]]
    return [[name.replace('👤 Custom: ', ''), "Loaded"] for name in custom_voices.keys()]

# Add voice mixing functionality
def parse_voice_formula(formula):
    if not formula.strip():
        raise ValueError("Empty voice formula")

    weighted_sum = None
    terms = formula.split('+')
    weights = 0

    for term in terms:
        parts = term.strip().split('*')
        if len(parts) != 2:
            raise ValueError(f"Invalid term format: {term.strip()}")

        voice_name = parts[0].strip()
        weight = float(parts[1].strip())
        weights += weight

        if voice_name not in loaded_voices:
            raise ValueError(f"Unknown voice: {voice_name}")

        voice_tensor = loaded_voices[voice_name]

        if weighted_sum is None:
            weighted_sum = weight * voice_tensor
        else:
            weighted_sum += weight * voice_tensor

    return weighted_sum / weights

def get_new_voice(formula, custom_name=""):
    try:
        weighted_voices = parse_voice_formula(formula)

        # Create a filename with custom name or timestamp if no name provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_name and custom_name.strip():
            # Sanitize custom name (remove spaces and special characters)
            custom_name = ''.join(c for c in custom_name if c.isalnum() or c == '_')
            voice_name = f"{custom_name}"
        else:
            voice_name = f"mixed_{timestamp}"

        voice_pack_name = os.path.join(custom_voices_folder, f"{voice_name}.pt")

        torch.save(weighted_voices, voice_pack_name)
        return voice_pack_name, voice_name
    except Exception as e:
        raise gr.Error(f"Failed to create voice: {str(e)}")

def generate_mixed_voice(formula_text, voice_name="", text_input=""):
    try:
        # Create the mixed voice file with custom name
        voice_file_path, voice_name = get_new_voice(formula_text, voice_name)
        voice_id = f"custom_{voice_name}"

        # Load the voice into memory to ensure it's available
        voice_pack = torch.load(voice_file_path, weights_only=True)
        loaded_voices[voice_id] = voice_pack

        # If text input is provided, generate audio with the mixed voice
        if text_input.strip():
            audio_path, _ = generate_first(text_input, voice_id)
            return f"Mixed voice '{voice_name}' created successfully! You can now select it from the voice dropdown as '👤 Custom: {voice_name}'", audio_path
        else:
            return f"Mixed voice '{voice_name}' created successfully! You can now select it from the voice dropdown as '👤 Custom: {voice_name}'", None
    except Exception as e:
        raise gr.Error(f"Failed to generate mixed voice: {e}")

# Function to build voice formula from sliders
def build_formula_from_sliders(*args):
    # The args will contain alternating checkbox and slider values
    formula_parts = []

    # Get the organized list of voices in the same order as they appear in the UI
    voice_keys = list(CHOICES.keys())
    voice_keys.sort()
    us_female_voices = [k for k in voice_keys if k.startswith('🇺🇸 🚺')]
    us_male_voices = [k for k in voice_keys if k.startswith('🇺🇸 🚹')]
    gb_female_voices = [k for k in voice_keys if k.startswith('🇬🇧 🚺')]
    gb_male_voices = [k for k in voice_keys if k.startswith('🇬🇧 🚹')]
    other_voices = [k for k in voice_keys if not (k.startswith('🇺🇸') or k.startswith('🇬🇧'))]
    organized_voices = us_female_voices + us_male_voices + gb_female_voices + gb_male_voices + other_voices

    for i in range(0, len(args), 2):
        if i+1 < len(args):  # Make sure we have both checkbox and slider
            checkbox = args[i]
            slider = args[i+1]

            if checkbox and i//2 < len(organized_voices):  # If checkbox is checked
                voice_name = organized_voices[i//2]
                voice_id = CHOICES[voice_name]
                formula_parts.append(f"{voice_id} * {slider}")

    if not formula_parts:
        return ""

    return " + ".join(formula_parts)

# Create the Gradio interface
with gr.Blocks(css="""
            /* Background animation */
            @keyframes gradientBG {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            /* Glow effects */
            @keyframes glow {
                0% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
                50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8), 0 0 30px rgba(102, 126, 234, 0.6); }
                100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
            }

            @keyframes textGlow {
                0% { text-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
                50% { text-shadow: 0 0 15px rgba(102, 126, 234, 0.8), 0 0 25px rgba(102, 126, 234, 0.6); }
                100% { text-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
            }

            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }

            body {
                background: linear-gradient(135deg, #0f1724, #1a1f35);
                background-size: 400% 400%;
                animation: gradientBG 15s ease infinite;
                margin: 0;
                padding: 20px;
                font-family: 'Poppins', sans-serif;
                color: #f5f5f5;
                min-height: 100vh;
            }

            .gradio-container {
                background: rgba(20, 25, 40, 0.7);
                border-radius: 16px;
                backdrop-filter: blur(10px);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                padding: 1.5rem;
                max-width: 100%;
                width: 2000px;
                margin: 0 auto;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            """) as demo:

    gr.HTML("""
    <div style="text-align: center; margin-bottom: 1rem">
        <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; background: linear-gradient(45deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Kokoro TTS</h1>
        <p style="font-size: 1.2rem; opacity: 0.8;">High-quality text-to-speech with multiple voices</p>
    </div>
    """)

    with gr.Tab("Text to Speech"):
        with gr.Row():
            with gr.Column(scale=3):
                text_input = gr.Textbox(
                    label="Text Input",
                    placeholder="Enter text to convert to speech...",
                    lines=10
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        voice_dropdown = gr.Dropdown(
                            choices=list(update_voice_choices().keys()),
                            value=list(update_voice_choices().keys())[0],
                            label="Voice"
                        )

                        refresh_button = gr.Button("🔄 Refresh Voice List")
                        refresh_button.click(fn=refresh_voice_list, outputs=voice_dropdown)

                    with gr.Column(scale=1):
                        speed_slider = gr.Slider(
                            minimum=0.5,
                            maximum=2.0,
                            value=1.0,
                            step=0.05,
                            label="Speed"
                        )

                generate_button = gr.Button("🔊 Generate Speech", variant="primary")

            with gr.Column(scale=2):
                output_audio = gr.Audio(label="Generated Audio", type="filepath")
                phoneme_output = gr.Textbox(label="Phoneme Sequence", visible=False)

        generate_button.click(
            fn=generate_first,
            inputs=[text_input, voice_dropdown, speed_slider],
            outputs=[output_audio, phoneme_output]
        )

    with gr.Tab("Custom Voices"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("""
                <div style="padding: 1rem; background: rgba(30, 35, 50, 0.5); border-radius: 12px; margin-bottom: 1rem;">
                    <h3 style="margin-top: 0;">Upload Custom Voice</h3>
                    <p>Upload a .pt voice file to use with the TTS system.</p>
                </div>
                """)

                voice_name_input = gr.Textbox(
                    label="Voice Name",
                    placeholder="Enter a name for your custom voice"
                )

                voice_file_input = gr.File(
                    label="Voice File (.pt)",
                    file_count="single",
                    file_types=[".pt"]
                )

                upload_button = gr.Button("📤 Upload Voice")

                upload_result = gr.Textbox(label="Upload Result")

            with gr.Column(scale=1):
                gr.HTML("""
                <div style="padding: 1rem; background: rgba(30, 35, 50, 0.5); border-radius: 12px; margin-bottom: 1rem;">
                    <h3 style="margin-top: 0;">Custom Voice List</h3>
                    <p>List of all custom voices available in the system.</p>
                </div>
                """)

                custom_voice_list = gr.Dataframe(
                    headers=["Voice Name", "Status"],
                    datatype=["str", "str"],
                    value=get_custom_voice_list(),
                    label="Custom Voices"
                )

        upload_button.click(
            fn=upload_and_refresh,
            inputs=[voice_file_input, voice_name_input],
            outputs=[upload_result, custom_voice_list, voice_name_input, voice_file_input]
        )

    with gr.Tab("Voice Mixer"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("""
                <div style="padding: 1rem; background: rgba(30, 35, 50, 0.5); border-radius: 12px; margin-bottom: 1rem;">
                    <h3 style="margin-top: 0;">Voice Mixer</h3>
                    <p>Create new voices by mixing existing ones with different weights.</p>
                </div>
                """)

                formula_input = gr.Textbox(
                    label="Voice Formula",
                    placeholder="Example: af_heart * 0.7 + am_michael * 0.3",
                    lines=3
                )

                mixed_voice_name = gr.Textbox(
                    label="Mixed Voice Name",
                    placeholder="Enter a name for your mixed voice"
                )

                test_text_input = gr.Textbox(
                    label="Test Text (Optional)",
                    placeholder="Enter text to test the mixed voice...",
                    lines=3
                )

                mix_button = gr.Button("🔄 Create Mixed Voice")

                mix_result = gr.Textbox(label="Mix Result")
                mix_audio = gr.Audio(label="Test Audio", type="filepath")

            with gr.Column(scale=1):
                gr.HTML("""
                <div style="padding: 1rem; background: rgba(30, 35, 50, 0.5); border-radius: 12px; margin-bottom: 1rem;">
                    <h3 style="margin-top: 0;">Voice Mixer Helper</h3>
                    <p>Use sliders to easily create voice formulas.</p>
                </div>
                """)

                # Create checkboxes and sliders for each voice
                voice_keys = list(CHOICES.keys())
                voice_keys.sort()

                # Organize voices by category
                us_female_voices = [k for k in voice_keys if k.startswith('🇺🇸 🚺')]
                us_male_voices = [k for k in voice_keys if k.startswith('🇺🇸 🚹')]
                gb_female_voices = [k for k in voice_keys if k.startswith('🇬🇧 🚺')]
                gb_male_voices = [k for k in voice_keys if k.startswith('🇬🇧 🚹')]
                other_voices = [k for k in voice_keys if not (k.startswith('🇺🇸') or k.startswith('🇬🇧'))]

                organized_voices = us_female_voices + us_male_voices + gb_female_voices + gb_male_voices + other_voices

                # Create a list to store all checkbox and slider components
                mixer_components = []

                with gr.Accordion("US Female Voices", open=True):
                    for voice in us_female_voices:
                        with gr.Row():
                            cb = gr.Checkbox(label=voice, value=False)
                            sl = gr.Slider(minimum=0.0, maximum=1.0, value=0.5, step=0.05, label=None)
                            mixer_components.extend([cb, sl])

                with gr.Accordion("US Male Voices", open=False):
                    for voice in us_male_voices:
                        with gr.Row():
                            cb = gr.Checkbox(label=voice, value=False)
                            sl = gr.Slider(minimum=0.0, maximum=1.0, value=0.5, step=0.05, label=None)
                            mixer_components.extend([cb, sl])

                with gr.Accordion("UK Female Voices", open=False):
                    for voice in gb_female_voices:
                        with gr.Row():
                            cb = gr.Checkbox(label=voice, value=False)
                            sl = gr.Slider(minimum=0.0, maximum=1.0, value=0.5, step=0.05, label=None)
                            mixer_components.extend([cb, sl])

                with gr.Accordion("UK Male Voices", open=False):
                    for voice in gb_male_voices:
                        with gr.Row():
                            cb = gr.Checkbox(label=voice, value=False)
                            sl = gr.Slider(minimum=0.0, maximum=1.0, value=0.5, step=0.05, label=None)
                            mixer_components.extend([cb, sl])

                with gr.Accordion("Other Voices", open=False):
                    for voice in other_voices:
                        with gr.Row():
                            cb = gr.Checkbox(label=voice, value=False)
                            sl = gr.Slider(minimum=0.0, maximum=1.0, value=0.5, step=0.05, label=None)
                            mixer_components.extend([cb, sl])

                update_formula_button = gr.Button("📝 Update Formula")

        # Connect the mixer components to the formula input
        update_formula_button.click(
            fn=build_formula_from_sliders,
            inputs=mixer_components,
            outputs=formula_input
        )

        # Connect the mix button to the generate_mixed_voice function
        mix_button.click(
            fn=generate_mixed_voice,
            inputs=[formula_input, mixed_voice_name, test_text_input],
            outputs=[mix_result, mix_audio]
        )

# Launch the app
if __name__ == "__main__":
    # Automatically open the browser when the app is launched
    # since models have been successfully loaded
    demo.launch(inbrowser=True)
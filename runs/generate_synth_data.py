import os

from bldfm import config

from flugs.utils.synth_data_generator import generate
from flugs.utils.config_loader import load_synth_config

from flugs.config import CONFIG_DIR

config.NUM_THREADS = min(16, os.cpu_count() or 1)

if __name__ == "__main__":
    synth_config = load_synth_config(f"{CONFIG_DIR}/generate_synth_data.yml")
    print(synth_config)
    generate(synth_config)

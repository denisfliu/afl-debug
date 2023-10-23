from omegaconf import OmegaConf


def get_config():
    config_path = "config.yaml"
    return OmegaConf.load(config_path)

def fancy_print(s: str):
    print("-" * 15)
    print(s)
    print("-" * 15)

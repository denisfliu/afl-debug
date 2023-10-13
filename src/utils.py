from omegaconf import OmegaConf


def get_config():
    config_path = "config.yaml"
    return OmegaConf.load(config_path)

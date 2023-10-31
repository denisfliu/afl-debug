import os
from omegaconf import OmegaConf


def get_config():
    if os.path.exists("/home/denis"):
        return OmegaConf.load("dconfig.yaml")
    return OmegaConf.load("config.yaml")


def fancy_print(s: str):
    print("-" * 15)
    print(s)
    print("-" * 15)

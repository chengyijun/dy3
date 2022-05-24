# -*- coding:utf-8 -*-
# 作者: 程义军
# 时间: 2022/5/24 14:40
from ruamel.yaml import YAML


class Config:
    def __init__(self):
        self.yml = YAML()

    def read_config(self):
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            return self.yml.load(f)

    def modify_config(self, modify_dict: dict):
        with open("config/config.yaml", "w", encoding="utf-8") as f:
            self.yml.dump(modify_dict, f)

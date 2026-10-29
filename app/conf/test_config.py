from dataclasses import dataclass
from pathlib import Path

import yaml
from omegaconf import OmegaConf


def load_by_yaml():
    # yaml配置的路径
    yaml_path = Path(__file__).parents[2] / "conf" / "test_config.yaml"
    # 打开文件流
    with open(yaml_path, mode="r", encoding="utf-8") as file:
        # 加载文件内容，得到数据
        yaml_data = yaml.safe_load(file)
        print(yaml_data, type(yaml_data))

        # 问题：读取属性时有补全提示, 也没有错误的警告提示
        print(yaml_data["name"])

@dataclass
class PersonConfig:
    name: str
    age: int
    height: float
    # def __init__(self, name, age, height):
    #     self.name = name
    #     self.age = age
    #     self.height = height

def load_by_omegaconf():
    # yaml配置的路径
    yaml_path = Path(__file__).parents[2] / "conf" / "test_config.yaml"
    # 加载文件
    yaml_data = OmegaConf.load(yaml_path)
    print(yaml_data, type(yaml_data))
    print(yaml_data["name"])
    # 将得到数据封装成指定类型的对象
    person_config:PersonConfig = OmegaConf.to_object(OmegaConf.merge(PersonConfig, yaml_data))
    print(person_config)
    print(person_config.name)


if __name__ == '__main__':
    # load_by_yaml()
    load_by_omegaconf()
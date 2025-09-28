"""
配置管理器 - 统一管理日志系统配置
职责：加载、验证和提供配置信息
"""

import os
import yaml
from typing import Dict, Any


class ConfigManager:
    """日志配置管理器"""

    def __init__(self):
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config.yaml"
        )
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            # 返回默认配置
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'output': {
                'directory': 'output',
                'files': {
                    'current': 'current.log',
                    'summary': 'summary.log',
                    'errors': 'errors.log'
                },
                'clear_on_start': True
            },
            'formatting': {
                'timestamp': '%H:%M:%S',
                'current_template': '[{time}] {level} {module} | {message}',
                'summary_template': '{message}',
                'error_template': '[{time}] ERROR {module} | {message}'
            }
        }

    def get_output_dir(self) -> str:
        """获取输出目录路径"""
        logs_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(logs_dir, self._config['output']['directory'])

    def get_file_path(self, file_type: str) -> str:
        """获取日志文件完整路径"""
        output_dir = self.get_output_dir()
        filename = self._config['output']['files'][file_type]
        return os.path.join(output_dir, filename)

    def should_clear_on_start(self) -> bool:
        """是否在启动时清空日志"""
        return self._config['output']['clear_on_start']

    def get_timestamp_format(self) -> str:
        """获取时间戳格式"""
        return self._config['formatting']['timestamp']

    def get_template(self, template_type: str) -> str:
        """获取日志模板"""
        return self._config['formatting'][f'{template_type}_template']
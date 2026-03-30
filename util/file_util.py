import yaml
import os


class FileUtil:
    """文件操作工具类"""

    @staticmethod
    def read_yaml(file_path):
        """
        读取 YAML 配置文件
        :param file_path: YAML 文件路径
        :return: 解析后的字典数据
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在：{file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def write_yaml(file_path, data):
        """
        写入 YAML 文件
        :param file_path: YAML 文件路径
        :param data: 要写入的数据（字典）
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    @staticmethod
    def get_project_root():
        """
        获取项目根目录
        :return: 项目根目录的绝对路径
        """
        # 当前文件的上级目录的上级目录
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(current_dir)
        return parent_dir

    @staticmethod
    def get_config_path():
        """
        获取配置文件路径
        :return: 配置文件的绝对路径
        """
        project_root = FileUtil.get_project_root()
        return os.path.join(project_root, 'config', 'config.yml')

    @staticmethod
    def get_report_dir():
        """
        获取报告目录
        :return: 报告目录的绝对路径
        """
        project_root = FileUtil.get_project_root()
        report_dir = os.path.join(project_root, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        return report_dir

    @staticmethod
    def get_log_dir():
        project_dir = os.path.join(FileUtil.get_project_root())
        log_dir = os.path.join(project_dir, 'log','logger')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

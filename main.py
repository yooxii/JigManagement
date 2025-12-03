import os
import sys
import logging
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_dir="logs", log_filename="app.log"):
    """
    配置全局日志：同时输出到控制台和文件
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    full_log_path = log_path / log_filename

    # 创建格式器
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 创建处理器：控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 创建处理器：文件（带轮转更佳，这里先用基础版）
    file_handler = logging.FileHandler(full_log_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # 获取根 logger 并设置级别
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 避免重复添加 handler（重要！）
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)


setup_logging()

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from gui.mainWin import QApplication, MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

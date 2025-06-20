import logging

from rich.logging import RichHandler


def get_logger(name):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # 创建一个 RichHandler
    rich_handler = RichHandler(rich_tracebacks=True)
    logger = logging.getLogger(name)
    # 将处理器添加到日志记录器
    logger.addHandler(rich_handler)
    return logger

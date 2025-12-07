import sys
from loguru import logger
from tqdm import tqdm


# 配置 loguru：清除默认 handler
logger.remove()

# 自定义一个 sink，使用 tqdm.write 来输出日志
def tqdm_sink(message):
    tqdm.write(message, end="")

# 添加新的 sink
# 这将把所有日志通过 tqdm.write 输出，从而避免破坏进度条
logger.add(
    tqdm_sink,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",  # 保持 DEBUG 级别，以便看到所有日志
)


# 保留 TqdmToLogger，以防其他地方用到
# 自定义一个适配器：让 tqdm.write() → logger.info()
class TqdmToLogger:
    def __init__(self, logger, level="INFO"):
        self.logger = logger
        self.level = level

    def write(self, buf):
        buf = buf.strip()
        if buf:
            self.logger.opt(depth=1).log(self.level, buf)

    def flush(self):
        pass  # logger 自动 flush


# 创建适配器实例
tqdm_logger = TqdmToLogger(logger, level="INFO")

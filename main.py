import torch

from src.utils.logger import get_logger


logger = get_logger(__name__)

def main():
    logger.info("Hello from 30daymapchallenge!")
    logger.info(f"Torch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"CUDA device(s): {torch.cuda.device_count()}")


if __name__ == "__main__":
    main()

import logging
import os
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        os.makedirs("output/logs", exist_ok=True)
        os.makedirs("output/errors", exist_ok=True)
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Info log handler
        fh_info = logging.FileHandler(f"output/logs/run_{current_time}.log")
        fh_info.setLevel(logging.INFO)
        
        # Error log handler
        fh_error = logging.FileHandler(f"output/errors/run_errors_{current_time}.log")
        fh_error.setLevel(logging.ERROR)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh_info.setFormatter(formatter)
        fh_error.setFormatter(formatter)
        
        logger.addHandler(ch)
        logger.addHandler(fh_info)
        logger.addHandler(fh_error)
        
    return logger

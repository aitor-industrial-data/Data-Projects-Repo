import logging
import os
from pathlib import Path
from datetime import datetime

def setup_logging():
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    log_dir = BASE_DIR / "logs"
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"SunSaver_{today}.log" 
    log_path = log_dir / log_filename

    logger = logging.getLogger("SunSaver_System")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s | %(message)s', 
                                    datefmt='%Y-%m-%d %H:%M:%S')
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger



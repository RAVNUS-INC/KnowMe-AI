import logging

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with the specified name and log file."""
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# Example usage:
# logger = setup_logger('my_logger', 'app.log')
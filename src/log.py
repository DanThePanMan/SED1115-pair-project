from config import LOGLEVEL

def log_trace(source: str, message: str):
    if LOGLEVEL <= 0:
        log("trace", source, message, color="90")

def log_debug(source: str, message: str):
    if LOGLEVEL <= 1:
        log("debug", source, message, color="34")

def log_info(source: str, message: str):
    if LOGLEVEL <= 2:
        log("info", source, message, color="32")

def log_warn(source: str, message: str):
    if LOGLEVEL <= 3:
        log("warn", source, message, color="93")

def log_error(source: str, message: str):
    log("error", source, message, color="31")

def log(level: str, source: str, message: str, color:str="0"):
    print(f"\x1b[{color}m{level:5}\x1b[0m   {source:20}   {message}")

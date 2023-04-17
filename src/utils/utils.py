import os
from typing import Optional
from loguru import logger
from termcolor import colored

def success(text: str, extra_info: Optional[str] = None):
    print("\n")
    message = colored(text, "green")
    if extra_info:
        message += f" - {extra_info}"
    logger.opt(colors=True).success(os.linesep + message)

def info(text: str, extra_info: Optional[str] = None):
    print("\n")
    message = colored(text, "yellow")
    if extra_info:
        message += f" - {extra_info}"
    logger.opt(colors=True).info(os.linesep + message)
        
def warning(text: str, extra_info: Optional[str] = None):
    print("\n")
    message = colored(text, "magenta")
    if extra_info:
        message += f" - {extra_info}"
    logger.opt(colors=True).warning(os.linesep + message)
    
def select_option(text: str, extra_info: Optional[str] = None, color: Optional[str] = "orange"):
    print("\n")
    message = colored(text, color)
    if extra_info:
        message += f" - {extra_info}"
    logger.opt(colors=True).warning(os.linesep + message)


def error(text: str, extra_info: Optional[str] = None):
    print("\n")
    message = colored(text, "red")
    if extra_info:
        message += f" - {extra_info}"
    logger.opt(colors=True).error(os.linesep + message)
    
def debug(text: str, extra_info: Optional[str] = None):
    print("\n")
    message = colored(text, "magenta")
    if extra_info:
        message += f" - {extra_info}"
    logger.opt(colors=True).debug(os.linesep + message)

def log(msg):
    print(f"{msg}")

import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler

import colorlog
import logredactor

DATE_FMT = "%Y-%m-%d %H:%M:%S"


class CartDLLogger(logging.Logger):

    def __init__(
        self,
        name="CartDL",
        log_level="INFO",
        log_dir="log",
        max_logs=9,
    ):
        """Intialise a custom logging class

        Args:
            name (str): The name of the logger. Defaults to "CartDL".
            log_level (str): Logging level. Defaults to "INFO"
            log_dir (str): The directory to save logs to. Defaults to "log".
                Set to None to skip file logging.
            max_logs (int): The maximum number of logs to save. Defaults to 9
        """

        super().__init__(name, log_level)

        if log_level.lower() not in ["debug", "info", "critical"]:
            log_level = "INFO"
            print(f"Defaulting to {log_level}")

        self.name = name
        self.log_level = log_level
        self.log_dir = log_dir
        self.max_logs = max_logs

        self.redact_patterns = []
        self.redact_filter = None

        self.propagate = False
        self.file_handler = None
        self.console_handler = None
        self.get_logger()

    def close(self):
        """Close file handler to release log file locks"""
        if self.file_handler:
            self.file_handler.close()
            self.removeHandler(self.file_handler)
            self.file_handler = None

    def get_logger(self):
        """Initialise the logging to file, and the console logger"""

        self.setLevel(self.log_level.upper())
        self.handlers.clear()

        self.console_handler = self.get_gui_logger()
        self.addHandler(self.console_handler)

        if self.log_dir is not None:
            self.file_handler = self.get_file_logger()
            self.addHandler(self.file_handler)

    def get_file_logger(
        self,
    ):
        """Initialise logging to a file, moving files if necessary"""

        # Create the log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Define the log file path, and sanitize if needs be
        log_file = os.path.join(self.log_dir, f"{self.name}.log")

        # Check if log file already exists
        if os.path.isfile(log_file):
            for i in range(self.max_logs - 1, 0, -1):
                old_log = os.path.join(self.log_dir, f"{self.name}.log.{i}")
                new_log = os.path.join(self.log_dir, f"{self.name}.log.{i + 1}")
                if os.path.exists(old_log):
                    if os.path.exists(new_log):
                        os.remove(new_log)
                    os.rename(old_log, new_log)
            os.rename(log_file, os.path.join(self.log_dir, f"{self.name}.log.1"))

        # Define the log message format for the log files
        logfile_formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s: %(message)s",
            datefmt=DATE_FMT,
        )

        # Create a RotatingFileHandler for log files
        handler = RotatingFileHandler(
            log_file, delay=True, mode="w", backupCount=self.max_logs
        )
        handler.setFormatter(logfile_formatter)

        self.addHandler(handler)

        return handler

    def get_gui_logger(self):
        """Get the GUI logger"""

        # Set up the handler
        handler = colorlog.StreamHandler(sys.stdout)
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s[%(asctime)s] %(levelname)s: %(message)s",
                datefmt=DATE_FMT,
            )
        )
        self.addHandler(handler)

        return handler

    def update_redact_filter(
        self,
        redact_pattern,
    ):
        """Update the redact patterns, update the redact filter

        Args:
            redact_pattern (str): The regex pattern to redact.
                Any special regex characters are automatically
                escaped so this should be input as a literal
                string
        """

        # Update redact patterns
        self.redact_patterns.append(re.compile(re.escape(redact_pattern)))

        # Remove the filter if it already exists on the file handler
        if self.file_handler is not None:
            if self.redact_filter is not None:
                self.file_handler.removeFilter(self.redact_filter)

            # Create the new filter and add it to the file handler only
            self.redact_filter = logredactor.RedactingFilter(
                patterns=self.redact_patterns,
                default_mask="[REDACTED]",
            )
            self.file_handler.addFilter(self.redact_filter)

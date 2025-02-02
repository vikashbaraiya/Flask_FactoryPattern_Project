import logging

class BaseLogger:
    """
    A base class to provide logging functionality to derived classes.
    """
    def __init__(self, logger_name=None):
        """
        Initialize the logger with a specific name.
        :param logger_name: Optional name for the logger (default: module name).
        """
        if logger_name:
            self.logger = logging.getLogger(logger_name)
        else:
            # Default to the module name where the class is used
            self.logger = logging.getLogger(self.__class__.__module__)

        # Set logging level (can be environment-specific)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.hasHandlers():
            # Add a StreamHandler (console output)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)

        # Prevent log propagation to avoid duplicate logs
        self.logger.propagate = False

    def get_logger(self):
        """
        Get the logger instance.
        """
        return self.logger

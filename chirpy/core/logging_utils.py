"""
This file contains functions to create and configure the chirpylogger, which is a single simple logger to replace
the more complicated LoggerFactory that came with Cobot.
"""

import logging
import sys
import colorama
from dataclasses import dataclass
from typing import Optional
from chirpy.core.logging_formatting import ChirpyFormatter
from chirpy.core.logging_rich import ChirpyHandler
from rich.highlighter import NullHighlighter


PRIMARY_INFO_NUM = logging.INFO + 5  # between INFO and WARNING


@dataclass
class LoggerSettings:
    logtoscreen_level: int
    logtoscreen_usecolor: bool
    logtofile_level: Optional[int]  # None means don't log to file
    logtofile_path: Optional[str]  # None means don't log to file
    logtoscreen_allow_multiline: bool  # If true, log-to-screen messages contain \n. If false, all the \n are replaced with <linebreak>
    integ_test: bool  # If True, we setup the logger in a special way to work with nosetests
    remove_root_handlers: bool  # If True, we remove all other handlers on the root logger
    allow_rich_formatting: bool = True
    filter_by_rg: str = None
    disable_annotation: bool = False


# AWS adds a LambdaLoggerHandler to the root handler, which causes duplicate logging because we have our customized
# StreamHandler on the root logger too. So we set remove_root_handlers=True to remove the LambdaLoggerHandler.
# See here: https://stackoverflow.com/questions/50909824/getting-logs-twice-in-aws-lambda-function
PROD_LOGGER_SETTINGS = LoggerSettings(logtoscreen_level=logging.DEBUG,
                                      logtoscreen_usecolor=True,
                                      logtofile_level=None,
                                      logtofile_path=None,
                                      logtoscreen_allow_multiline=True,
                                      integ_test=False,
                                      remove_root_handlers=True,
                                      allow_rich_formatting=True,
                                      filter_by_rg=None,
                                      disable_annotation=False)


def setup_logger(logger_settings, session_id=None):
    """
    Sets up the chirpylogger using given logger_settings and session_id.

    Following best practices (https://docs.python.org/3/library/logging.html#logging.Logger.propagate) we attach our
    customized handlers to the root logger. The chirpylogger is a descendent of the root logger, so all chirpylogger
    messages are passed to the root logger, and then handled by our handlers.
    """
    # Set elasticsearch level to ERROR (it does excessive long WARNING logs)
    logging.getLogger('elasticsearch').setLevel(logging.ERROR)

    # For colored logging, automatically add RESET_ALL after each print statement.
    # This is especially important for when we log errors/warnings in red (we do not RESET ourselves because we want the
    # stack trace to be red too).
    if logger_settings.logtoscreen_usecolor:
        colorama.init(convert=False, strip=False, autoreset=True)

    # Either create or get existing logger with name chirpylogger
    chirpy_logger = logging.getLogger('chirpylogger')

    # Save our logger_settings in chirpy_logger
    chirpy_logger.logger_settings = logger_settings

    # Get root logger
    root_logger = logging.getLogger()

    # If the root logger already has our handler(s) set up, no need to do anything else
    if hasattr(root_logger, 'chirpy_handlers'):
        return chirpy_logger

    # Optionally, remove any pre-existing handlers on the root logger
    if logger_settings.remove_root_handlers:
        for h in root_logger.handlers:
            root_logger.removeHandler(h)

    # For integration tests, we need our logger to work with nosetests Logcapture plugin.
    # For complicated reasons, that means we need to set chirpy_logger to have the desired level (not the handlers)
    # See the "integration tests" internal documentation for explanation.
    if logger_settings.integ_test:
        if logger_settings.logtofile_level:
            assert logger_settings.logtoscreen_level == logger_settings.logtofile_level, f'For integration testing, ' \
                f'logtoscreen_level={logger_settings.logtoscreen_level} must equal logtofile_level={logger_settings.logtofile_level}'
            chirpy_logger.setLevel(logger_settings.logtoscreen_level)
    else:
        # For non integration tests, set chirpy logger's level as low as possible.
        # This means chirpylogger passes on all messages, and the handlers filter by level.
        chirpy_logger.setLevel(logging.DEBUG)

    # Create the stream handler and attach it to the root logger
    print("allow_multiline = ", logger_settings.logtoscreen_allow_multiline )
    print("rich formatting = ", logger_settings.allow_rich_formatting)
    if logger_settings.logtoscreen_allow_multiline and logger_settings.allow_rich_formatting:
        root_logger.addHandler(ChirpyHandler(log_time_format="[%H:%M:%S.%f]",
                                             level=logger_settings.logtoscreen_level,
                                             markup=True,
                                             highlighter=NullHighlighter(),
                                             filter_by_rg=logger_settings.filter_by_rg,
                                             disable_annotation=logger_settings.disable_annotation))
    else:
        # Use the stream handler if no multi-line to not mess up production logs
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logger_settings.logtoscreen_level)
        stream_formatter = ChirpyFormatter(allow_multiline=logger_settings.logtoscreen_allow_multiline, use_color=logger_settings.logtoscreen_usecolor, session_id=session_id)
        stream_handler.setFormatter(stream_formatter)
        root_logger.addHandler(stream_handler)
    #root_logger.addHandler(RichHandler(log_time_format="[%H:%M:%S]", level=logger_settings.logtoscreen_level, markup=True))

    # Create the file handler and attach it to the root logger
    if logger_settings.logtofile_path:
        file_handler = logging.FileHandler(logger_settings.logtofile_path, mode='w')
        file_handler.setLevel(logger_settings.logtofile_level)
        file_formatter = ChirpyFormatter(allow_multiline=True, use_color=False, session_id=session_id)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Mark that the root logger has the chirpy handlers attached
    root_logger.chirpy_handlers = True

    # Add the color PRIMARY_INFO level to chirpy logger
    add_new_level(chirpy_logger, 'PRIMARY_INFO', PRIMARY_INFO_NUM)

    return chirpy_logger


def add_new_level(logger, level_name, level_num):
    """
    Add a new logging level to a logging.Logger object.

    logger: a Logger
    level_name: string
    level_num: int
    """

    # Add the level name
    logging.addLevelName(level_num, level_name.upper())

    # Make a function to log messages at the new level
    # This function copies the convenience functions Logger.debug(), Logger.info(), etc
    def log_message_at_level(msg, *args, **kwargs):
        if logger.isEnabledFor(level_num):
            logger._log(level_num, msg, args, **kwargs)

    # Attach this function to the logger
    setattr(logger, level_name.lower(), log_message_at_level)


def update_logger(session_id, function_version):
    """
    This function does some updates that need to be done at the start of every turn.
    It is assumed that setup_logger has already been run.
    """
    root_logger = logging.getLogger()
    chirpy_logger = logging.getLogger('chirpylogger')
    logger_settings = chirpy_logger.logger_settings

    # When running integration tests with nosetests and the logcapture plugin, logs are captured by MyMemoryHandler
    # (which is attached to root logger) and then printed for failed tests.
    # See "integration tests" internal documentation for more info.
    # For readability, we want MyMemoryHandler to use ChirpyFormatter. This needs to be set every turn because
    # MyMemoryHandler sometimes gets reinitialized between turns/tests.
    if logger_settings.integ_test:
        for h in root_logger.handlers:
            if type(h).__name__ == 'MyMemoryHandler':
                # use_color=False because it shows up as color codes, rather than actual colors, when we view the
                # nosetest results in an output text file / in dev pipeline.
                stream_formatter = ChirpyFormatter(allow_multiline=logger_settings.logtoscreen_allow_multiline,
                                                   use_color=False, session_id=session_id)
                h.setFormatter(stream_formatter)

    # Add session_id and function_version to the ChirpyFormatters attached to handlers on the root logger
    # This will mean session_id and function_version are shown in every log message.
    for handler in root_logger.handlers:
        if isinstance(handler.formatter, ChirpyFormatter):
            handler.formatter.update_session_id(session_id)
            handler.formatter.update_function_version(function_version)
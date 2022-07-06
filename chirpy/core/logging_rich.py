import logging
from datetime import datetime
from logging import Handler, LogRecord
from pathlib import Path
from collections import Iterable
from typing import ClassVar, Iterable, List, Optional, Type, TYPE_CHECKING, Union, Callable
import os
import rich

from rich import get_console
from rich._log_render import LogRender, FormatTimeCallable
from rich.containers import Renderables
from rich.console import Console, ConsoleRenderable, RenderableType
from rich.highlighter import Highlighter, ReprHighlighter
from rich.text import Text, TextType
from rich.traceback import Traceback
from rich.logging import RichHandler

from rich.table import Table

from chirpy.core.logging_formatting import COLOR_SETTINGS

PATH_WIDTH = 25

LEVEL_STYLES = {"primary_info": "dim",
                "error": "bold red on bright_yellow"}

LEVEL_LINE_COLORS = {"error": "red"}

COBOT_HOME = os.environ.get('COBOT_HOME', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_rich_color(text):
    for component_name, settings in COLOR_SETTINGS.items():
        if component_name.lower() in text.lower():
            return settings.get('rich_color')
        if 'path_strings' in settings:
            for path_string in settings['path_strings']:
                if path_string.lower() in text.lower():
                    return settings.get('rich_color')
    return None

def add_emoji(text, check_text = None):
    if not check_text:
        check_text = text
    for component_name, settings in COLOR_SETTINGS.items():
        if component_name in check_text and settings.get('emoji'):
            return settings['emoji'] + ' ' + text
        if 'path_strings' in settings:
            for path_string in settings['path_strings']:
                if path_string in check_text and settings.get('emoji'):
                    return settings['emoji'] + ' ' + text
    return text

class ChirpyLogRender(LogRender):
    def __call__(
        self,
        console: "Console",
        renderables: Iterable["ConsoleRenderable"],
        log_time: datetime = None,
        time_format: Union[str, FormatTimeCallable] = None,
        level: TextType = "",
        path: str = None,
        line_no: int = None,
        link_path: str = None,
        path_color: str = None,
    ) -> "Table":
        output = Table.grid(padding=(0, 1))
        output.expand = True
        if self.show_level:
            output.add_column(width=self.level_width)
        if self.show_path and path:
            output.add_column(width=PATH_WIDTH) #style="dim",
        output.add_column(ratio=1, style="log.message", overflow="fold")
        if self.show_time:
            output.add_column(style="log.time")
        row: List["RenderableType"] = []
        if self.show_level:
            row.append(level[:3])
        if self.show_path and path:
            path_text = Text.from_markup(path)
            if line_no:
                if len(path_text) > PATH_WIDTH - len(str(line_no)) - 2:
                    path_text.truncate(PATH_WIDTH - len(str(line_no)) - 2)
                    path_text.append("…")
                path_text.append(f":{line_no}")
            path_text.stylize(path_color)
            row.append(path_text)

        row.append(Renderables(renderables))
        if self.show_time:
            log_time = log_time or console.get_datetime()
            time_format = time_format or self.time_format
            if callable(time_format):
                log_time_display = time_format(log_time)
            else:
                log_time_display = Text(log_time.strftime(time_format)[:-4] + ']')
            if log_time_display == self._last_time and self.omit_repeated_times:
                row.append(Text(" " * len(log_time_display)))
            else:
                row.append(log_time_display)
                self._last_time = log_time_display

        output.add_row(*row)
        return output


class ChirpyHandler(RichHandler):
    DICT_OPEN_TAG: str = "[dict]\n"
    DICT_CLOSE_TAG: str = "\n[/dict]"

    def __init__(
        self,
        level: Union[int, str] = logging.NOTSET,
        console: Console = None,
        *,
        show_time: bool = True,
        omit_repeated_times: bool = True,
        show_level: bool = True,
        show_path: bool = True,
        enable_link_path: bool = True,
        highlighter: Highlighter = None,
        markup: bool = False,
        rich_tracebacks: bool = False,
        tracebacks_width: Optional[int] = None,
        tracebacks_extra_lines: int = 3,
        tracebacks_theme: Optional[str] = None,
        tracebacks_word_wrap: bool = True,
        tracebacks_show_locals: bool = False,
        locals_max_length: int = 10,
        locals_max_string: int = 80,
        log_time_format: Union[str, FormatTimeCallable] = "[%x %X]",
        filter_by_rg: str = None,
        disable_annotation: bool = False,
    ) -> None:
        super().__init__(
            level=level,
            console=console,
            show_time=show_time,
            omit_repeated_times=omit_repeated_times,
            show_level=show_level,
            show_path=show_path,
            enable_link_path=enable_link_path,
            highlighter=highlighter,
            markup=markup,
            rich_tracebacks=rich_tracebacks,
            tracebacks_width=tracebacks_width,
            tracebacks_extra_lines=tracebacks_extra_lines,
            tracebacks_theme=tracebacks_theme,
            tracebacks_word_wrap=tracebacks_word_wrap,
            tracebacks_show_locals=tracebacks_show_locals,
            locals_max_length=locals_max_length,
            locals_max_string=locals_max_string,
            log_time_format=log_time_format,
        )
        self._log_render = ChirpyLogRender(
            show_time=show_time,
            show_level=show_level,
            show_path=show_path,
            time_format=log_time_format,
            omit_repeated_times=omit_repeated_times,
            level_width=None,
        )
        if filter_by_rg:
            valid_rg_filenames = [f.name.lower() for f in os.scandir(os.path.join(COBOT_HOME, "chirpy/response_generators")) if f.is_dir()]
            filter_by_rg = filter_by_rg.lower()
            assert filter_by_rg in valid_rg_filenames, f"{filter_by_rg} does not specify a valid RG filename (must be a folder in chirpy/response_generators)"
        self.filter_by_rg = filter_by_rg
        self.disable_annotation = disable_annotation

    def process_dictionary(self, dict_text: str) -> "ConsoleRenderable":
        lines = dict_text.split('\n')
        pairs = [line.split('\u00a0' * 5) for line in lines]
        assert all(len(p) == 2 for p in pairs)
        grid = Table.grid(expand=True, padding=(0, 3))
        grid.add_column(justify="left", width=25)
        grid.add_column(ratio=1)
        for pair in pairs:
            pair = [p.strip().strip("'") for p in pair]
            name, value = pair
            text_color = get_rich_color(name)
            name = add_emoji(name)
            if text_color:
                grid.add_row(Text.from_markup(name, style=text_color), value)
            else:
                grid.add_row(name, value)
        return grid

    def render_message(self, record: LogRecord, message: str) -> List["ConsoleRenderable"]:
        """Render message text in to Text.

        record (LogRecord): logging Record.
        message (str): String cotaining log message.

        Returns:
            ConsoleRenderable: Renderable to display log message.
        """
        use_markup = (
            getattr(record, "markup") if hasattr(record, "markup") else self.markup
        )
        message_texts = []
        if record.levelname.lower() in LEVEL_LINE_COLORS:
            color = LEVEL_LINE_COLORS[record.levelname.lower()]
            message = "[" + color + "]" + message
            message = message.replace('\n', "[/" + color + "]\n", 1)
        if self.DICT_OPEN_TAG in message:
            start = message.find(self.DICT_OPEN_TAG)
            end = message.find(self.DICT_CLOSE_TAG)
            dict_text = message[start + len(self.DICT_OPEN_TAG):end]
            message_one = message[:start]
            message_two = message[end + len(self.DICT_CLOSE_TAG):]
            text_color = None
            message_texts.append(Text.from_markup(message_one) if use_markup else Text(message_one))
            message_texts.append(self.process_dictionary(dict_text))
            message_texts.append(Text.from_markup(message_two) if use_markup else Text(message_two))
        else:
            message_texts.append(Text.from_markup(message) if use_markup else Text(message))
        for message_text in message_texts:
            if isinstance(message_text, Text):
                if self.highlighter:
                    message_text = self.highlighter(message_text)
                if self.KEYWORDS:
                    message_text.highlight_words(self.KEYWORDS, "logging.keyword")
        return message_texts

    def get_level_text(self, record: LogRecord) -> Text:
        """Get the level name from the record.

        Args:
            record (LogRecord): LogRecord instance.

        Returns:
            Text: A tuple of the style and level name.
        """
        level_name = record.levelname
        level_text = Text.styled(
            level_name[:3].ljust(8).capitalize(), f"logging.level.{level_name.lower()}"
        )
        if level_name.lower() in LEVEL_STYLES:
            level_text.stylize(LEVEL_STYLES[level_name.lower()])
        return level_text

    def emit(self, record: LogRecord) -> None:
        """Invoked by logging."""
        message = self.format(record)
        traceback = None
        if (
            self.rich_tracebacks
            and record.exc_info
            and record.exc_info != (None, None, None)
        ):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            traceback = Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
            )
            message = record.getMessage()
            if self.formatter:
                record.message = record.getMessage()
                formatter = self.formatter
                if hasattr(formatter, "usesTime") and formatter.usesTime():  # type: ignore
                    record.asctime = formatter.formatTime(record, formatter.datefmt)
                message = formatter.formatMessage(record)

        if self.should_show(record):
            message_renderable = self.render_message(record, message)
            log_renderable = self.render(
                record=record, traceback=traceback, message_renderable=message_renderable
            )
            self.console.print(log_renderable)

    def should_show(self, record):
        if record.levelname.lower() in ['error', 'warning']:
            return True
        path = record.pathname
        if 'response_generators' not in path.lower():
            return not self.disable_annotation
        if self.filter_by_rg is None:
            return True
        return self.filter_by_rg in path.lower()

    def render(
        self,
        *,
        record: LogRecord,
        traceback: Optional[Traceback],
        message_renderable: "ConsoleRenderable",
    ) -> "ConsoleRenderable":
        """Render log for display.

        Args:
            record (LogRecord): logging Record.
            traceback (Optional[Traceback]): Traceback instance or None for no Traceback.
            message_renderable (ConsoleRenderable): Renderable (typically Text) containing log message contents.

        Returns:
            ConsoleRenderable: Renderable to display log.
        """
        path_color = get_rich_color(record.pathname)
        path = Path(record.pathname).name
        path = add_emoji(path, record.pathname)
        if record.levelname.lower() in LEVEL_LINE_COLORS:
            path_color = LEVEL_LINE_COLORS[record.levelname.lower()]
        level = self.get_level_text(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)

        if traceback:
            message_renderable.append(traceback)

        log_renderable = self._log_render(
            self.console,
            message_renderable,
            log_time=log_time,
            time_format=time_format,
            level=level,
            path=path,
            line_no=record.lineno,
            link_path=record.pathname if self.enable_link_path else None,
            path_color=path_color,
        )
        return log_renderable
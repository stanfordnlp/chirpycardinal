import logging
from typing import Optional
from colorama import Fore, Back

from pathlib import Path

def get_active_branch_name():
    git_dir = Path(".") / ".git"
    if git_dir.is_dir():
        head_dir = git_dir / "HEAD"
        with head_dir.open("r") as f: content = f.read().splitlines()

        for line in content:
            if line[0:4] == "ref:":
                return line.partition("refs/heads/")[2]
    else: # for integ. testing, we don't copy .git/ to the instance
        return []

LINEBREAK = '<linebreak>'

# The key in this dict must match the 'name' given to the component in baseline_bot.py (case-insensitive)
# The path_strings are strings we'll search for (case-insensitive) in the path of the file that does the log message
# You can comment out parts of this dict and add your own components to make it easier to only see what you're working on
# See https://rich.readthedocs.io/en/stable/appendix/colors.html for list of rich colors
# See https://github.com/willmcgugan/rich/blob/master/rich/_emoji_codes.py for emoji codes
COLOR_SETTINGS = {
    'ACKNOWLEDGMENT': {'color': Fore.CYAN, 'rich_color': '#0AAB42',
                       'emoji': ':white_heavy_check_mark:', 'path_strings': ['acknowledgment']},
    'ALEXA_COMMANDS': {'emoji': ':speaking_head_in_silhouette:', 'path_strings': ['alexa_commands']},
    'ALIENS': {'rich_color': '#1EA8B3', 'emoji': ':alien:'},
    'CATEGORIES': {'rich_color': '#15EBCE', 'emoji': ':newspaper:', 'path_strings': ['categories']},
    'CORONAVIRUS': {'rich_color': '#F70C6E', 'emoji': ':face_with_medical_mask:'},
    'FOOD': {'rich_color': '#97F20F', 'emoji': ':sushi:'},
    'LAUNCH': {'emoji': ':checkered_flag:', 'path_strings': ['launch']},
    'MOVIES': {'rich_color': '#F0D718', 'emoji': ':movie_camera:', 'path_strings': ['movies']},
    'MUSIC': {'rich_color': '#0586FF', 'emoji': ':musical_notes:'},
    'NEURAL_CHAT': {'rich_color': '#0EE827', 'emoji': ':brain:', 'path_strings': ['neural_chat']},
    'NEWS': {'rich_color': '#1C64FF', 'emoji': ':newspaper:'},
    'OFFENSIVE_USER': {'rich_color': '#EB5215', 'emoji': ':prohibited:'},
    'ONE_TURN_HACK': {'rich_color': '#88B0B3', 'emoji': ':hammer:'},
    'OPINION': {'rich_color': '#D011ED', 'emoji': ':thinking_face:'},
    'PERSONAL_ISSUES': {'rich_color': '#BC3BEB', 'emoji': ':slightly_frowning_face:'},
    'SPORTS': {'rich_color': '#EB8715', 'emoji': ':football:'},
    'WIKI': {'rich_color': '#42C2F5', 'emoji': ':books:'},
    'TRANSITION': {'rich_color': '#5FD700', 'emoji': ':soon_arrow:'},
    'REOPEN': {'rich_color': '##5F00FF', 'emoji': ':door:'},
    'entity_linker': {'color': Fore.LIGHTCYAN_EX, 'rich_color': '#0BC3E3', 'path_strings': ['entity_linker']},
    'entity_tracker': {'color': Fore.LIGHTYELLOW_EX, 'rich_color': '#DB960D', 'path_strings': ['entity_tracker']},
    'experiments': {'color': Fore.LIGHTGREEN_EX, 'rich_color': '#CADB0D', 'path_strings': ['experiments']},
    'navigational_intent': {'color': Fore.LIGHTMAGENTA_EX, 'rich_color': '#DB0D93', 'path_strings': ['navigational_intent']}
}

LOG_FORMAT = '[%(levelname)s] [%(asctime)s] [fn_vers: {function_version}] [session_id: {session_id}] [%(pathname)s:%(lineno)d]\n%(message)s\n'


def colored(str, fore=None, back=None, include_reset=True):
    """Function to give a colorama-colored string."""
    new_str = str
    if fore:
        new_str = '{}{}{}'.format(fore, new_str, Fore.RESET if include_reset else '')
    if back:
        new_str = '{}{}{}'.format(back, new_str, Back.RESET if include_reset else '')
    return new_str

def get_rich_color_for_rg(rg_name):
    for component_name, settings in COLOR_SETTINGS.items():
        if component_name.lower() == rg_name.lower() and settings.get('rich_color'):
            color = settings['rich_color']
            return f"[{color}]{rg_name}[/{color}]"
    return rg_name

def get_line_color(line, branch_name):
    """
    Given a line of logging (which is one line of a multiline log message), searches for component names at the
    beginning of the line. If one is found, returns its color.
    """
    first_part_line = line.strip().split()[0]
    for component_name, settings in COLOR_SETTINGS.items():
        if component_name in first_part_line:
            return settings.get('color')
    if any(b.lower() in first_part_line.lower() for b in branch_name):
        return Fore.BLUE
    return None


def linecolored_msg_fmt(line_colors):
    """
    Given line_colors, which is a list of colors for each line, return the new formatting string for a message
    (i.e. a template showing where each line goes, with the color formatting strings surrounding particular lines).
    """
    return '\n'.join([colored('%({})s'.format(get_line_key(idx)), fore=color)
                      for idx, color in enumerate(line_colors)])


def get_line_key(idx: int):
    """Return a key to act as a placeholder for a particular line in the log formatting string"""
    return 'line_{}'.format(idx)


class ChirpyFormatter(logging.Formatter):
    """
    A color formatter that formats linebreaks and color according to logger_settings, and the context of each message.

    Based on this: https://stackoverflow.com/a/14859558
    """

    def __init__(self, allow_multiline: bool, use_color: bool, session_id: Optional[str]=None, function_version: Optional[int]=None):
        self.allow_multiline = allow_multiline
        self.use_color = use_color
        self.session_id = session_id
        self.function_version = function_version
        if self.use_color:
            branch_name = get_active_branch_name()
            branch_name = ''.join([x if x.isalpha() else ' ' for x in branch_name])
            self.branch_name = branch_name.split()
        self.update_format()

    def update_format(self):
        """Recomputes fmt based on self.session_id and self.function_version, optionally adjusts fmt for linebreaks,
        then saves and re-initializes"""

        fmt = LOG_FORMAT.format(session_id=self.session_id, function_version=self.function_version)

        # If we're not allowing multilines, change \n to <linebreak> in the format
        # This affects the linebreaks between the boilerplate and the message, and the linebreak after the message
        if not self.allow_multiline:
            fmt = fmt.replace('\n', LINEBREAK)

        # Save the format and re-initialize
        self.fmt = fmt
        super().__init__(fmt=fmt, datefmt=None, style='%')

    def update_session_id(self, session_id):
        """Update the format to use the given session_id"""
        self.session_id = session_id
        self.update_format()

    def update_function_version(self, function_version):
        """Update the format to use the given function_version"""
        self.function_version = function_version
        self.update_format()

    def format(self, record):

        # If we're not allowing multilines, change \n to <linebreak> in the message
        if not self.allow_multiline:
            record.msg = str(record.msg).replace('\n', LINEBREAK)

        # Optionally format with color
        if self.use_color:
            result = self.format_color(record)
        else:
            result = logging.Formatter.format(self, record)

        return result


    def format_color(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # If it's a WARNING or ERROR, color in red
        # include_reset=False to make sure the stack trace is red too. Assumes we have autoreset=True in colorama
        if record.levelno >= logging.WARNING:
            self._style._fmt = colored(self.fmt, fore=Fore.RED, include_reset=False)

        # If we passed a specific component name using the 'color_msg_by_component' flag, color it that component's
        # color (if it has a color)
        elif hasattr(record, 'color_msg_by_component'):
            component = record.color_msg_by_component
            if component in COLOR_SETTINGS:
                self._style._fmt = colored(self.fmt, fore=COLOR_SETTINGS[component]['color'])

        # If we passed the 'color_lines_by_component' flag, color each line differently (according to component)
        elif hasattr(record, 'color_lines_by_component'):
            lines = record.msg.split('\n')
            for idx, line in enumerate(lines):
                setattr(record, get_line_key(idx), line)  # e.g. record['line_5'] -> the text of the 5th line of logging
            line_colors = [get_line_color(line, self.branch_name) for line in lines]  # get the color for each line
            self._style._fmt = self.fmt.replace('%(message)s', linecolored_msg_fmt(line_colors))  # this format string has keys for line_1, line_2, etc, along with line-specific colors

        # If the filepath of the calling function contains a path string for a colored component, return its color
        else:
            for component, settings in COLOR_SETTINGS.items():
                if settings.get('path_strings'):
                    for path_string in settings['path_strings']:
                        if path_string in record.pathname:
                            self._style._fmt = colored(self.fmt, fore=settings['color'])
                            continue
                if any(b in record.pathname for b in self.branch_name):
                    self._style._fmt = colored(self.fmt, fore=Fore.BLUE)

        # Use the formatter class to do the formatting (with a possibly modified format)
        result = logging.Formatter.format(self, record)

        # Restore the original format
        self._style._fmt = format_orig

        return result
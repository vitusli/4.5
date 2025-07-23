
import typing

ATTR_BOLD = 1
ATTR_DARK = 2
ATTR_UNDERLINE = 4
ATTR_BLINK = 5
ATTR_REVERSE = 7
ATTR_CONCEALED = 8

COLOR_BLACK = 30
COLOR_RED = 31
COLOR_GREEN = 32
COLOR_YELLOW = 33
COLOR_BLUE = 34
COLOR_MAGENTA = 35
COLOR_CYAN = 36
COLOR_LIGHT_GRAY = 37
COLOR_DARK_GRAY = 90
COLOR_LIGHT_RED = 91
COLOR_LIGHT_GREEN = 92
COLOR_LIGHT_YELLOW = 93
COLOR_LIGHT_BLUE = 94
COLOR_LIGHT_MAGENTA = 95
COLOR_LIGHT_CYAN = 96
COLOR_WHITE = 97
COLOR_DEFAULT = COLOR_WHITE

HL_BLACK = 40
HL_RED = 41
HL_GREEN = 42
HL_YELLOW = 43
HL_BLUE = 44
HL_MAGENTA = 45
HL_CYAN = 46
HL_LIGHT_GRAY = 47
HL_DARK_GRAY = 100
HL_LIGHT_RED = 101
HL_LIGHT_GREEN = 102
HL_LIGHT_YELLOW = 103
HL_LIGHT_BLUE = 104
HL_LIGHT_MAGENTA = 105
HL_LIGHT_CYAN = 106
HL_WHITE = 107
HL_DEFAULY = HL_BLACK

RESET = "\033[0m"


def format_markdown(markdown: str, indent: str = '  '):
    result = ''
    lines = markdown.split('\n')
    indentation = 0

    for line in lines:
        words = line.split(' ')
        if len(words) < 1:
            result += "\n"
            continue

        result += indent * indentation

        if len(words) > 1 and all(char == "#" for char in words[0]):
            result += ' '.join(words[1:])
            result += '\n'
            indentation = len(words[0])
            continue

        result += line + '\n'

    return result

def _color_enabled_in_terminal() -> bool:
    import os, sys

    # Then check env vars:
    if "ANSI_COLORS_DISABLED" in os.environ:
        return False
    if "NO_COLOR" in os.environ:
        return False
    if "FORCE_COLOR" in os.environ:
        return True
    return (
        hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
        and os.environ.get("TERM") != "dumb"
    )


def color(text: str, color: int = None, highlight: int = None, attrs: typing.Iterable[int] = None) -> str:

    if not _color_enabled_in_terminal():
        return text

    formatter = "\033[%dm%s"
    if color is not None:
        text = formatter % (color, text)

    if highlight is not None:
        text = formatter % (highlight, text)

    if attrs is not None:
        for attr in attrs:
            text = formatter % (attr, text)

    return text + RESET
    
def box(lines: typing.Iterable[str], header: str = ''):
    
    max_line_length = max((len(l) for l in lines))
    header_text = "═" * max_line_length
    if header != '':
        header_text = "╡ " + header + " ╞"
        max_line_length = max(max_line_length, len(header_text))

    text = "\n"
    text += " ╔═" + header_text + "═" * (max_line_length - len(header_text)) +              "═╗" + "\n"
    for line in lines:
        text += " ║ " + line + " " * (max_line_length - len(line)) +                        " ║" + "\n"
    text += " ╚═" + "═" * max_line_length +                                                 "═╝" + "\n"
    return text
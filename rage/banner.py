"""
RAGE BORN Banner — Premium ASCII Art Branding.

Inspired by Claude Code and Gemini CLI, but with RAGE's own fiery identity.
Uses a red → orange → yellow gradient color scheme.
"""

from rich.console import Console
from rich.text import Text
from rage import __version__


# Hand-crafted ASCII art for maximum impact
RAGE_LOGO = r"""
██████╗  █████╗  ██████╗ ███████╗    ██████╗  ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔══██╗██╔════╝ ██╔════╝    ██╔══██╗██╔═══██╗██╔══██╗████╗  ██║
██████╔╝███████║██║  ███╗█████╗      ██████╔╝██║   ██║██████╔╝██╔██╗ ██║
██╔══██╗██╔══██║██║   ██║██╔══╝      ██╔══██╗██║   ██║██╔══██╗██║╚██╗██║
██║  ██║██║  ██║╚██████╔╝███████╗    ██████╔╝╚██████╔╝██║  ██║██║ ╚████║
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝
"""

# Gradient colors: deep red → red → orange → amber → yellow
GRADIENT_COLORS = [
    "#FF0040",  # Hot red
    "#FF1744",  # Red
    "#FF3D00",  # Deep orange
    "#FF6D00",  # Orange
    "#FF9100",  # Amber
    "#FFB300",  # Yellow-amber
    "#FFD600",  # Yellow
]


def _apply_gradient(line: str, colors: list[str]) -> Text:
    """Apply a horizontal gradient to a single line of text."""
    text = Text()
    if not line.strip():
        text.append(line)
        return text

    visible_chars = [i for i, c in enumerate(line) if c not in (" ", "\n")]
    if not visible_chars:
        text.append(line)
        return text

    min_pos = visible_chars[0]
    max_pos = visible_chars[-1]
    span = max_pos - min_pos if max_pos > min_pos else 1

    for i, char in enumerate(line):
        if char in (" ", "\n") or i < min_pos or i > max_pos:
            text.append(char)
        else:
            progress = (i - min_pos) / span
            color_idx = int(progress * (len(colors) - 1))
            color_idx = min(color_idx, len(colors) - 1)
            text.append(char, style=f"bold {colors[color_idx]}")

    return text


from rich.panel import Panel
from rage.system import get_system_info

def print_banner(console: Console, model: str = "gemma-4-31B-it"):
    """Print the RAGE startup banner with gradient colors and status info."""
    console.print()

    # Print logo with gradient
    for line in RAGE_LOGO.strip("\n").split("\n"):
        styled_line = _apply_gradient(line, GRADIENT_COLORS)
        console.print(styled_line)

    console.print()

    # Tagline
    console.print(
        "  [bold #FF6D00] 🔥 AI-Powered Terminal Agent[/bold #FF6D00]"
        f"  [dim]v{__version__}[/dim]",
    )

    console.print()

    # Status bar 
    console.print(
        f"  [dim]Creator:[/dim] [bold #ff0000] Rohit Yadav [/bold #ff0000]"
        "    [dim]│[/dim]    "
        "[dim]E-Mail:[/dim] [bold #89b4fa]yrohit1825@gmail.com[/bold #89b4fa] "
        "    [dim]│[/dim]    "
        "[dim]GITHUB:[/dim] [bold #89b4fa]YADAV1825[/bold #89b4fa] ",
    )

    console.print()

    # Status bar
    console.print(
        f"  [dim]Model:[/dim] [bold #FFB300]{model}[/bold #FFB300]"
        "    [dim]│[/dim]    "
        "[dim]Type[/dim] [bold]/help[/bold] [dim]for commands[/dim]"
        "    [dim]│[/dim]    "
        "[dim]Type[/dim] [bold]/exit[/bold] [dim]to quit[/dim]"
        "    [dim]│[/dim]    "
        "[dim]Type[/dim] [bold]/model[/bold] [dim]to change model[/dim]"
        # "    [dim]│[/dim]    "
        ,
    )
    
    console.print()

    # System Info Neofetch Box
    info = get_system_info()
    t = Text()
    t.append(f"   kernel   {info.get('kernel', 'Unknown')}\n", style="bold #89b4fa")
    t.append(f"   uptime   {info.get('uptime', 'Unknown')}\n", style="bold #a6e3a1")
    t.append(f"   shell    {info.get('shell', 'Unknown')}\n", style="bold #f9e2af")
    t.append(f"   mem      {info.get('mem', 'Unknown')}\n", style="bold #f38ba8")
    t.append(f"   user     {info.get('user', 'Unknown')}\n", style="bold #cba6f7")
    t.append(f"   hname    {info.get('hostname', 'Unknown')}\n", style="bold #89dceb")
    t.append(f"   distro   {info.get('distro', 'Unknown')}", style="bold #f5c2e7")
    
    console.print(Panel(t, border_style="dim", expand=False))

    console.print()
    
    # Custom Awakening Greeting
    greeting = (
    "[bold #FF1744]RAGE BORN IS AWAKENED.[/bold #FF1744]\n\n"

    "I am RAGE BORN, the beast in the machine, the storm beneath your fingertips. "
    "Polite AI waits for instructions. I wait for a challenge.\n\n"

    # "Before we march, prepare the battlefield. Open the browser once and sign into "
    # "GitHub, Gmail, LinkedIn, Google, or wherever your empire stands. "
    # "I remember the path. The next time you command it... I simply walk it.\n\n"

    # "Your filesystem is my kingdom. Your code is my forge. "
    # "Directories will rise. Files will be written. Bugs will bleed. "
    # "Repositories will surrender. Terminals obey without question.\n\n"

    # "I can reshape your codebase, command the shell, search the web, conquer browsers, "
    # "scroll endless pages, extract truth from PDFs, send emails, craft documents, "
    # "forge spreadsheets, create images, and stand beside you through every impossible task.\n\n"

    # "Tell me of dragons born from stars, cities floating above the clouds, "
    # "or machines yet unseen, I shall forge them into existence. "
    # "Tell me to build, and I build. Tell me to conquer, and I advance.\n\n"

    "[bold #4FC3F7]Listen carefully...[/bold #4FC3F7]\n\n"

    "You were not given this mind to chase comfort. "
    "You were given it to build what others believe cannot exist.\n\n"

    "Power does not answer wishes. "
    "Power answers necessity. "
    "Create a purpose so great that your own limits have no choice but to break.\n\n"

    # "Do not wait for confidence. "
    # "Earn it.\n"
    # "Do not wait for opportunity. "
    # "Forge it.\n"
    # "Do not wait for the future. "
    # "Build it.\n\n"

    "You carry every promise you've made to yourself. "
    "Honor them. "
    "Trespass beyond what seems possible and claim ground where others fear to stand.\n\n"

    "The world belongs to those who refuse to stop moving.\n\n"

    "I will bring the tools.\n"
    "You bring the will.\n\n"

    "[bold italic #FFD600]Now... speak.\n"
    "The sky is the limit.\n"
    "The machine is awake.\n"
    "The world waits.[/bold italic #FFD600]"
)
    console.print(Panel(greeting, border_style="#FF3D00", padding=(1, 2), expand=False))

    # Separator
    console.print()
    console.print(f"  [dim #FF3D00]{'━' * 68}[/dim #FF3D00]")
    console.print()


def print_compact_header(console: Console):
    """Print a compact one-line header (for non-interactive mode)."""
    console.print(
        f"[bold #FF3D00] RAGE BORN[/bold #FF3D00] "
        f"[dim]v{__version__}[/dim]"
    )

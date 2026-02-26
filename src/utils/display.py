"""
Display — Terminal display utilities.

Provides progress bars, banners, and formatting for live simulation output.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn


console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🔧  DIGITAL TWIN — Resource-Constrained IoT Simulator     ║
║                                                              ║
║   Simulating: Wireless IoT Sensor Node                       ║
║   Components: CPU • RAM • Battery • Network • Sensors        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]
"""
    console.print(banner)


def print_config_summary(config: dict):
    """Print a summary of the simulation configuration."""
    device = config["device"]
    sim = config["simulation"]
    sync = config["sync"]

    text = (
        f"[bold]Device:[/bold] {device['processor']['name']} @ {device['processor']['clock_mhz']} MHz\n"
        f"[bold]RAM:[/bold] {device['memory']['total_ram_kb']} KB  │  "
        f"[bold]Battery:[/bold] {device['battery']['capacity_mah']} mAh  │  "
        f"[bold]Network:[/bold] {device['network']['type']} ({device['network']['max_bandwidth_kbps']} kbps)\n"
        f"[bold]Duration:[/bold] {sim['duration_hours']}h  │  "
        f"[bold]Sampling:[/bold] every {sim['sampling_rate_seconds']}s  │  "
        f"[bold]Sync:[/bold] {sync['default_strategy']}\n"
        f"[bold]Seed:[/bold] {sim['random_seed']}  │  "
        f"[bold]Log Format:[/bold] {sim['log_format']}"
    )

    console.print(Panel(text, title="⚙️  Configuration", border_style="dim"))
    console.print()


def create_progress_bar(total_ticks: int) -> Progress:
    """Create a progress bar for the simulation."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def print_simulation_complete(filepath: str):
    """Print simulation completion message."""
    console.print()
    console.print(Panel(
        f"[bold green]✅ Simulation complete![/bold green]\n"
        f"📁 Log saved to: [cyan]{filepath}[/cyan]",
        border_style="green",
    ))
    console.print()

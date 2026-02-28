"""ZineCore2 Server Onboarding TUI — interactive setup wizard powered by Textual."""

from __future__ import annotations

import asyncio
import os
import re
import secrets
import shutil
import string
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Awaitable, Callable

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, ProgressBar, RichLog, Static

# ---------------------------------------------------------------------------
# Project root (directory containing this script)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
MANAGE_PY = ".venv/bin/python backend/manage.py"
DJANGO_ENV = {"DJANGO_SETTINGS_MODULE": "zinecore.settings.development"}


def _load_dotenv() -> dict[str, str]:
    """Read key=value pairs from .env (ignoring comments and blank lines)."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return {}
    result = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


# ---------------------------------------------------------------------------
# Step model
# ---------------------------------------------------------------------------
class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class OnboardingStep:
    name: str
    run: Callable[..., Awaitable[None]]
    needs_prompt: Callable[..., Awaitable[bool]] | None = None
    prompt_text: str = ""
    status: StepStatus = field(default=StepStatus.PENDING)


# ---------------------------------------------------------------------------
# Custom widgets
# ---------------------------------------------------------------------------
class StepList(Vertical):
    """Sidebar list of onboarding steps with status indicators."""

    def __init__(self, steps: list[OnboardingStep], **kwargs) -> None:
        super().__init__(**kwargs)
        self.steps = steps

    def compose(self) -> ComposeResult:
        for i, step in enumerate(self.steps):
            yield Static(
                self._format(i, step),
                id=f"step-{i}",
                classes="step-item --pending",
                markup=True,
            )

    def update_step(self, index: int, step: OnboardingStep) -> None:
        widget = self.query_one(f"#step-{index}", Static)
        widget.update(self._format(index, step))
        for cls in ("--pending", "--running", "--completed", "--failed", "--skipped"):
            widget.remove_class(cls)
        widget.add_class(f"--{step.status.value}")

    @staticmethod
    def _format(index: int, step: OnboardingStep) -> str:
        icons = {
            StepStatus.PENDING: "  ",
            StepStatus.RUNNING: "> ",
            StepStatus.COMPLETED: "[green]\u2713[/green] ",
            StepStatus.SKIPPED: "[dim]--[/dim]",
            StepStatus.FAILED: "[red]!![/red]",
        }
        icon = icons.get(step.status, "  ")
        return f"{icon} {step.name}"


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
class OnboardingApp(App):
    """ZineCore2 Server Onboarding TUI."""

    CSS_PATH = "onboarding.tcss"
    TITLE = "ZineCore2 Server Onboarding"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.steps: list[OnboardingStep] = self._define_steps()
        self._prompt_event: asyncio.Event | None = None
        self._prompt_answer: bool | None = None
        self._current_proc: asyncio.subprocess.Process | None = None

    # -- compose -------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static(" ZineCore2 Server Onboarding", id="masthead")
        with Horizontal(id="main-content"):
            with Vertical(id="sidebar"):
                yield Static(self._progress_text(0), id="progress-info")
                yield ProgressBar(
                    total=len(self.steps),
                    show_eta=False,
                    show_percentage=False,
                    id="progress-bar",
                )
                yield StepList(self.steps, id="step-list")
            yield RichLog(
                highlight=True,
                markup=True,
                auto_scroll=True,
                id="log-panel",
            )
        with Vertical(id="prompt-bar"):
            yield Static("", id="prompt-text", markup=True)
            with Horizontal():
                yield Input(placeholder="y/n", id="prompt-input", max_length=1)

    def on_mount(self) -> None:
        self._run_all_steps()

    # -- step runner ---------------------------------------------------------

    @work(exclusive=True)
    async def _run_all_steps(self) -> None:
        log = self.query_one("#log-panel", RichLog)
        step_list = self.query_one("#step-list", StepList)
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        total = len(self.steps)

        for i, step in enumerate(self.steps):
            step.status = StepStatus.RUNNING
            step_list.update_step(i, step)
            self._update_progress(i, total)

            log.write(f"\n[bold]--- Step {i + 1}/{total}: {step.name} ---[/bold]")

            user_said_yes: bool | None = None

            if step.needs_prompt is not None:
                should_prompt = await step.needs_prompt(self)
                if should_prompt:
                    user_said_yes = await self._ask_user(step.prompt_text)

            try:
                await step.run(self, user_said_yes)
                if step.status == StepStatus.RUNNING:
                    step.status = StepStatus.COMPLETED
            except Exception as exc:
                step.status = StepStatus.FAILED
                log.write(f"[red]Error: {exc}[/red]")

            step_list.update_step(i, step)
            progress_bar.advance(1)
            self._update_progress(i + 1, total)

        self._show_summary(log)

    # -- prompt mechanism ----------------------------------------------------

    async def _ask_user(self, question: str) -> bool:
        self._prompt_event = asyncio.Event()
        self._prompt_answer = None

        prompt_bar = self.query_one("#prompt-bar")
        prompt_bar.add_class("--visible")
        self.query_one("#prompt-text", Static).update(question)

        prompt_input = self.query_one("#prompt-input", Input)
        prompt_input.value = ""
        prompt_input.focus()

        await self._prompt_event.wait()

        prompt_bar.remove_class("--visible")
        return self._prompt_answer  # type: ignore[return-value]

    @on(Input.Submitted, "#prompt-input")
    def _on_prompt_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip().lower()
        if value in ("y", "n"):
            self._prompt_answer = value == "y"
            if self._prompt_event:
                self._prompt_event.set()
            event.input.value = ""
        else:
            event.input.value = ""
            self.query_one("#log-panel", RichLog).write(
                "[yellow]Please enter 'y' or 'n'[/yellow]"
            )

    # -- subprocess helper ---------------------------------------------------

    async def run_command(
        self,
        cmd: str,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> int:
        merged_env = {**os.environ, **_load_dotenv(), **DJANGO_ENV, **(env or {})}
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(cwd or PROJECT_ROOT),
            env=merged_env,
        )
        self._current_proc = proc
        log = self.query_one("#log-panel", RichLog)

        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            log.write(line.decode("utf-8", errors="replace").rstrip("\n"))

        returncode = await proc.wait()
        self._current_proc = None

        if check and returncode != 0:
            raise RuntimeError(f"Command exited with code {returncode}")
        return returncode

    def log_message(self, text: str) -> None:
        self.query_one("#log-panel", RichLog).write(text)

    # -- progress helpers ----------------------------------------------------

    def _progress_text(self, completed: int) -> str:
        total = len(self.steps) if self.steps else 9
        pct = int((completed / total) * 100) if total else 0
        return f"Progress: {completed}/{total}  {pct}%"

    def _update_progress(self, completed: int, total: int) -> None:
        pct = int((completed / total) * 100) if total else 0
        self.query_one("#progress-info", Static).update(
            f"Progress: {completed}/{total}  {pct}%"
        )

    # -- completion summary --------------------------------------------------

    def _show_summary(self, log: RichLog) -> None:
        failed = [s for s in self.steps if s.status == StepStatus.FAILED]
        skipped = [s for s in self.steps if s.status == StepStatus.SKIPPED]

        log.write("")
        log.write("[bold green]============================[/bold green]")
        log.write("[bold green]  Onboarding Complete!      [/bold green]")
        log.write("[bold green]============================[/bold green]")
        log.write("")

        if failed:
            log.write(
                f"[red]Failed steps: {', '.join(s.name for s in failed)}[/red]"
            )
        if skipped:
            log.write(
                f"[yellow]Skipped steps: {', '.join(s.name for s in skipped)}[/yellow]"
            )

        log.write("")
        log.write("You can now run:")
        log.write("  ./start.sh        - Start development server")
        log.write("")
        log.write("Admin credentials:")
        log.write("  Username: admin")
        log.write("  Password: admin")
        log.write("")
        log.write("Services:")
        log.write("  PostgreSQL:   localhost:5433")
        log.write("  Django:       http://localhost:8000")
        log.write("  Admin:        http://localhost:8000/admin/")
        log.write("  API docs:     http://localhost:8000/api/docs/")
        log.write("")
        log.write("[dim]Press Ctrl+C to exit[/dim]")

    # -- graceful quit -------------------------------------------------------

    def action_quit(self) -> None:
        if self._current_proc is not None:
            try:
                self._current_proc.terminate()
            except ProcessLookupError:
                pass
        self.exit()

    # -----------------------------------------------------------------------
    # Step definitions
    # -----------------------------------------------------------------------

    def _define_steps(self) -> list[OnboardingStep]:
        return [
            OnboardingStep(
                name="Docker Volumes",
                run=step_docker_volumes,
                needs_prompt=check_docker_volumes,
                prompt_text="Delete and recreate docker volumes? (WARNING: deletes all data) (y/n):",
            ),
            OnboardingStep(
                name="Set up ENV",
                run=step_env,
                needs_prompt=check_env,
                prompt_text="Regenerate .env with new secrets? (y/n):",
            ),
            OnboardingStep(
                name="Spec Submodule",
                run=step_spec_submodule,
            ),
            OnboardingStep(
                name="Docker Compose",
                run=step_docker_compose,
            ),
            OnboardingStep(
                name="Python Venv",
                run=step_python_venv,
                needs_prompt=check_python_venv,
                prompt_text="Delete and recreate virtual environment? (y/n):",
            ),
            OnboardingStep(
                name="Database Setup",
                run=step_database,
            ),
            OnboardingStep(
                name="Load GeoNames Places",
                run=step_load_geonames,
            ),
            OnboardingStep(
                name="Load Vocabularies",
                run=step_load_vocabularies,
            ),
            OnboardingStep(
                name="Load ISO 639-1 Languages",
                run=step_load_languages,
            ),
            OnboardingStep(
                name="Import Fixtures",
                run=step_import_fixture_data,
            ),
            OnboardingStep(
                name="Import Custom Fixtures",
                run=step_import_custom_data,
            ), 
            OnboardingStep(
                name="Create Superuser",
                run=step_create_superuser,
            ),
        ]


# ---------------------------------------------------------------------------
# Prompt-condition checkers (return True if a prompt is needed)
# ---------------------------------------------------------------------------


async def check_docker_volumes(app: OnboardingApp) -> bool:
    # Check for any containers (running or stopped) from this compose project
    proc_ps = await asyncio.create_subprocess_shell(
        "docker compose ps -a -q",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        cwd=str(PROJECT_ROOT),
    )
    stdout_ps, _ = await proc_ps.communicate()
    has_containers = bool(stdout_ps.decode().strip())

    # Check for volumes matching this compose project
    proc_vol = await asyncio.create_subprocess_shell(
        "docker volume ls --format '{{.Name}}'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        cwd=str(PROJECT_ROOT),
    )
    stdout_vol, _ = await proc_vol.communicate()
    names = stdout_vol.decode().strip().splitlines()
    found = [n for n in names if n.startswith("zinecore2_")]

    if has_containers or found:
        if found:
            app.log_message("Found existing data volumes:")
            for name in found:
                app.log_message(f"  {name}")
        if has_containers:
            app.log_message("Found existing compose containers.")
        return True
    app.log_message("No existing docker volumes or containers found.")
    return False


async def check_env(app: OnboardingApp) -> bool:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        app.log_message("Found existing .env file")
        return True
    return False


async def check_python_venv(app: OnboardingApp) -> bool:
    venv_path = PROJECT_ROOT / ".venv"
    if venv_path.is_dir():
        app.log_message("Found existing .venv directory")
        return True
    return False


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------


async def step_docker_volumes(app: OnboardingApp, user_said_yes: bool | None) -> None:
    if user_said_yes is None:
        return
    if user_said_yes:
        app.log_message("Stopping containers and removing volumes...")
        await app.run_command("docker compose down -v")
        app.log_message("[green]\u2713 Volumes deleted[/green]")
    else:
        app.log_message("Keeping existing volumes, stopping containers...")
        await app.run_command("docker compose down")


async def step_env(app: OnboardingApp, user_said_yes: bool | None) -> None:
    env_path = PROJECT_ROOT / ".env"
    example_path = PROJECT_ROOT / ".env.example"

    if user_said_yes is False:
        app.log_message("Keeping existing .env")
        return

    if user_said_yes is None:
        app.log_message("Creating .env from .env.example...")
    else:
        app.log_message("Regenerating .env with new secrets...")

    secret_key = secrets.token_urlsafe(50)
    alphanumeric = string.ascii_letters + string.digits
    postgres_password = "".join(secrets.choice(alphanumeric) for _ in range(16))

    template = example_path.read_text()
    content = template
    content = re.sub(
        r"^DJANGO_SECRET_KEY=.*$",
        f"DJANGO_SECRET_KEY={secret_key}",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^DATABASE_PASSWORD=.*$",
        f"DATABASE_PASSWORD={postgres_password}",
        content,
        flags=re.MULTILINE,
    )

    env_path.write_text(content)
    app.log_message("[green]\u2713 .env written with new secrets[/green]")
    app.log_message(f"  DJANGO_SECRET_KEY={secret_key[:12]}...")
    app.log_message(f"  DATABASE_PASSWORD={postgres_password[:12]}...")


async def step_spec_submodule(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Initializing and updating spec submodule...")
    await app.run_command("git submodule update --init --remote spec")
    app.log_message("[green]\u2713 Spec submodule is up to date[/green]")


async def step_docker_compose(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Bringing up PostgreSQL...")
    await app.run_command("docker compose up -d --wait")
    app.log_message("[green]\u2713 PostgreSQL is ready[/green]")


async def step_python_venv(app: OnboardingApp, user_said_yes: bool | None) -> None:
    if user_said_yes is True:
        app.log_message("Removing .venv...")
        shutil.rmtree(PROJECT_ROOT / ".venv", ignore_errors=True)
        app.log_message("[green]\u2713 .venv removed[/green]")
    elif user_said_yes is False:
        app.log_message("Keeping existing .venv...")

    app.log_message("Running uv sync...")
    await app.run_command("uv sync")
    app.log_message("[green]\u2713 Python dependencies installed[/green]")


async def step_database(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Waiting for PostgreSQL to accept connections...")
    for attempt in range(10):
        ret = await app.run_command(
            "docker compose exec db pg_isready -U zinecore",
            check=False,
        )
        if ret == 0:
            break
        app.log_message(f"  Attempt {attempt + 1}/10 — waiting 3s...")
        await asyncio.sleep(3)
    else:
        raise RuntimeError("PostgreSQL did not become ready in time")

    app.log_message("Running migrations...")
    await app.run_command(f"{MANAGE_PY} migrate")
    app.log_message("[green]\u2713 Database migrations complete[/green]")


async def step_load_vocabularies(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Fetching controlled vocabularies from zinecore.org API...")
    try:
        await app.run_command(f"{MANAGE_PY} load_vocabularies")
    except RuntimeError:
        app.log_message(
            "[yellow]Warning: Some vocabularies failed to fetch from API[/yellow]"
        )

    # Load external_id_systems and external_uri_types from data/ directory
    app.log_message("Loading external identifier and URI vocabularies from data/ directory...")
    try:
        await app.run_command(
            f"{MANAGE_PY} load_vocabularies --local --vocab external_id_systems --vocab-dir data"
        )
        await app.run_command(
            f"{MANAGE_PY} load_vocabularies --local --vocab external_uri_types --vocab-dir data"
        )
        app.log_message("[green]\u2713 Vocabularies loaded[/green]")
    except RuntimeError:
        app.log_message(
            "[yellow]Warning: Failed to load local vocabularies from data/. "
            "You can retry later with: ./manage.py load_vocabularies --local --vocab-dir data[/yellow]"
        )
        for s in app.steps:
            if s.name == "Load Vocabularies":
                s.status = StepStatus.SKIPPED
                break


async def step_load_languages(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Fetching ISO 639-1 language codes from Library of Congress...")
    try:
        await app.run_command(f"{MANAGE_PY} load_languages")
        app.log_message("[green]\u2713 ISO 639-1 languages loaded[/green]")
    except RuntimeError:
        app.log_message(
            "[yellow]Warning: Failed to fetch languages from LOC. "
            "You can retry later with: ./manage.py load_languages[/yellow]"
        )
        for s in app.steps:
            if s.name == "Load ISO 639-1 Languages":
                s.status = StepStatus.SKIPPED
                break


async def step_load_geonames(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Loading geographic places from GeoNames (countries, admin1, cities)...")
    try:
        await app.run_command(f"{MANAGE_PY} load_geonames")
        app.log_message("[green]\u2713 GeoNames places loaded[/green]")
    except RuntimeError:
        app.log_message(
            "[yellow]Warning: Failed to load GeoNames data. "
            "You can retry later with: ./manage.py load_geonames[/yellow]"
        )
        for s in app.steps:
            if s.name == "Load GeoNames Places":
                s.status = StepStatus.SKIPPED
                break


async def step_import_fixture_data(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    data_file = PROJECT_ROOT / "data" / "fixtures.json"
    if not data_file.exists():
        app.log_message("[yellow]data/fixtures.json not found, skipping[/yellow]")
        for s in app.steps:
            if s.name == "Import Fixtures":
                s.status = StepStatus.SKIPPED
                break
        return

    app.log_message("Loading sample data (agents, repos, zines, holdings)...")
    await app.run_command(f"{MANAGE_PY} loaddata data/fixtures.json")
    app.log_message("[green]\u2713 Sample data loaded[/green]")


async def step_import_custom_data(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    data_file = PROJECT_ROOT / "data" / "custom.json"
    if not data_file.exists():
        app.log_message("[yellow]data/custom.json not found, skipping[/yellow]")
        for s in app.steps:
            if s.name == "Import Custom Fixtures":
                s.status = StepStatus.SKIPPED
                break
        return

    app.log_message("Loading custom data (agents, repos, zines, holdings)...")
    await app.run_command(f"{MANAGE_PY} loaddata data/custom.json")
    app.log_message("[green]\u2713 Custom data loaded[/green]")


async def step_create_superuser(app: OnboardingApp, _user_said_yes: bool | None) -> None:
    app.log_message("Ensuring admin superuser (username: admin, password: admin)...")
    await app.run_command(
        f'{MANAGE_PY} shell -c "'
        "from django.contrib.auth import get_user_model;"
        "User = get_user_model();"
        "u, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True});"
        "u.set_password('admin');"
        "u.is_staff = True;"
        "u.is_superuser = True;"
        "u.save();"
        "print('Created' if created else 'Reset password for', 'admin superuser')"
        '"',
    )
    app.log_message("[green]\u2713 Superuser ready[/green]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = OnboardingApp()
    app.run()

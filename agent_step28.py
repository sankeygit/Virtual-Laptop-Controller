import pyautogui
import subprocess
import time
import os
import shutil
import threading
import webbrowser
import urllib.parse
from google import genai
import json


import torch
import speech_recognition as sr
from PIL import ImageGrab
from transformers import (
    AutoProcessor,
    Qwen3VLForConditionalGeneration,
    BitsAndBytesConfig
)

pyautogui.FAILSAFE = True


MODEL = r"C:\Users\LENOVO\.cache\huggingface\hub\models--Qwen--Qwen3-VL-2B-Instruct\snapshots\89644892e4d85e24eaac8bacfd4f463576704203"

print("Loading Qwen...")

processor = AutoProcessor.from_pretrained(MODEL)

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL,
    device_map="auto",
    quantization_config=quant_config,
    torch_dtype=torch.float16,
)

model.eval()
print("Qwen loaded successfully.")

# Gemini reasoning brain
gemini_client = genai.Client()
GEMINI_MODEL = "gemini-3.8-flash"

print("Gemini reasoning brain connected.")

def gemini_plan_command(command):
    """Use Gemini as the high-level reasoning/planning layer."""

    prompt = f"""
You are the planning brain for a Windows computer-use agent.

The user gave this command:
{command}

Create a practical execution plan for the COMPLETE request.

Rules:
- Understand the user's actual goal and every requested operation.
- If the user asks for multiple operations, preserve ALL of them and their order/dependencies.
- Break complex requests into ordered, concrete subgoals.
- Do not stop planning after the first operation.
- Do not invent unnecessary steps.
- Do not directly control the computer.
- The local Python agent will execute one low-level action at a time and verify the screen after each action.
- A request may involve different applications, websites, files, searches, typing, clicking, media, settings, or other Windows operations in the same task.
- Keep the plan general-purpose; never assume the task is only about a particular app.
- Return ONLY valid JSON.

JSON format:
{{
    "goal": "short description of the user's goal",
    "steps": [
        {{
            "step": 1,
            "instruction": "what the computer agent should do"
        }}
    ]
}}
"""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )

        plan = json.loads(response.text)

        print("\n===== GEMINI PLAN =====")
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        print("=======================\n")

        return plan

    except Exception as e:
        print("Gemini planning error:", e)
        return None

# ==================================================
# BASIC COMPUTER ACTIONS
# ==================================================

def move_mouse(x, y, duration=0.2):
    pyautogui.moveTo(x, y, duration=duration)


def click(x, y):
    pyautogui.click(x, y)


def double_click(x, y):
    pyautogui.doubleClick(x, y, interval=0.1)


def right_click(x, y):
    pyautogui.rightClick(x, y)


def drag(x1, y1, x2, y2, duration=0.5):
    pyautogui.moveTo(x1, y1, duration=0.2)
    pyautogui.dragTo(x2, y2, duration=duration, button="left")


def type_text(text):
    pyautogui.write(text, interval=0.005)


def press_key(key):
    pyautogui.press(key)


def hotkey(*keys):
    pyautogui.hotkey(*keys)


def scroll(amount):
    pyautogui.scroll(amount)


def wait(seconds):
    time.sleep(seconds)


# ==================================================
# COMMON COMPUTER / WINDOWS ACTIONS
# ==================================================

def show_desktop():
    hotkey("win", "d")

def open_start_menu():
    press_key("win")

def open_task_manager():
    hotkey("ctrl", "shift", "esc")

def show_run_dialog():
    hotkey("win", "r")

def open_settings():
    hotkey("win", "i")

def lock_pc():
    hotkey("win", "l")

def copy_selection():
    hotkey("ctrl", "c")

def paste_clipboard():
    hotkey("ctrl", "v")

def cut_selection():
    hotkey("ctrl", "x")

def select_all():
    hotkey("ctrl", "a")

def undo_action():
    hotkey("ctrl", "z")

def redo_action():
    hotkey("ctrl", "y")

def save_current():
    hotkey("ctrl", "s")

def find_text():
    hotkey("ctrl", "f")

def volume_up():
    press_key("volumeup")

def volume_down():
    press_key("volumedown")

def volume_mute():
    press_key("volumemute")

def media_play_pause():
    press_key("playpause")

def media_next():
    press_key("nexttrack")

def media_previous():
    press_key("prevtrack")


def snap_left():
    hotkey("win", "left")


def snap_right():
    hotkey("win", "right")


def snap_up():
    hotkey("win", "up")


def snap_down():
    hotkey("win", "down")


def open_file_explorer():
    hotkey("win", "e")


def open_windows_search():
    hotkey("win", "s")


def open_notification_center():
    hotkey("win", "n")


def open_quick_settings():
    hotkey("win", "a")


def open_control_panel():
    subprocess.Popen(["control.exe"])


def zoom_in():
    hotkey("ctrl", "+")


def zoom_out():
    hotkey("ctrl", "-")


def zoom_reset():
    hotkey("ctrl", "0")


def page_top():
    hotkey("ctrl", "home")


def page_bottom():
    hotkey("ctrl", "end")


def browser_search(query):
    hotkey("ctrl", "l")
    type_text(query)
    press_key("enter")


# ==================================================
# WINDOWS ACTIONS
# ==================================================

def open_app(app_name):
    """Open a Windows application by name, using direct launch then Windows Search."""
    app_name = str(app_name).strip()
    if not app_name:
        return False

    aliases = {
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "command prompt": "cmd.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "control panel": "control.exe",
        "settings": "ms-settings:",
    }

    target = aliases.get(app_name.lower(), app_name)

    try:
        print(f"Opening application: {target}")
        if target.startswith("ms-settings:"):
            os.startfile(target)
        else:
            result = subprocess.run(
                ["cmd", "/c", "start", "", target],
                shell=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Windows start command failed")
        return True
    except Exception as e:
        print(f"Direct launch failed for '{app_name}': {e}")

    # Universal fallback: Windows Search can find installed apps by their
    # display name even when we do not know the executable name.
    try:
        print(f"Searching Windows for: {app_name}")
        hotkey("win", "s")
        time.sleep(0.4)
        type_text(app_name)
        time.sleep(0.8)
        press_key("enter")
        return True
    except Exception as e:
        print(f"Windows Search fallback failed: {e}")
        return False

def close_window():
    hotkey("alt", "f4")


def minimize_window():
    hotkey("alt", "space")
    press_key("n")


def maximize_window():
    hotkey("alt", "space")
    press_key("x")


def switch_window():
    hotkey("alt", "tab")


def open_folder(path):
    if os.path.exists(path):
        subprocess.Popen(["explorer", os.path.abspath(path)])
        return True

    print("Folder does not exist:", path)
    return False


def open_file(path):
    if os.path.exists(path):
        os.startfile(os.path.abspath(path))
        return True

    print("File does not exist:", path)
    return False


def run_command(command):
    """Run a Windows command after the agent's confirmation layer approves it."""
    try:
        subprocess.Popen(command, shell=True)
        return True
    except Exception as e:
        print("Could not run command:", e)
        return False


# ==================================================
# FRIENDLY FOLDER / WEB ACTIONS
# ==================================================

def open_special_folder(name):
    folders = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
        "music": os.path.join(os.path.expanduser("~"), "Music"),
        "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    }
    key = name.strip().lower()
    path = folders.get(key)
    if not path:
        print("Unknown special folder:", name)
        return False
    return open_folder(path)


def search_web(query):
    query = query.strip()
    if not query:
        return False
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    webbrowser.open(url)
    return True


# ==================================================
# FILE ACTIONS
# ==================================================

def create_file(path):
    if os.path.exists(path):
        print("File already exists:", path)
        return False

    folder = os.path.dirname(os.path.abspath(path))

    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8"):
        pass

    return True


def rename_file(old_path, new_path):
    if not os.path.exists(old_path):
        print("Source does not exist:", old_path)
        return False

    if os.path.exists(new_path):
        print("Destination already exists:", new_path)
        return False

    os.rename(old_path, new_path)
    return True


def copy_file(source, destination):
    if not os.path.isfile(source):
        print("Source file does not exist:", source)
        return False

    if os.path.exists(destination):
        print("Destination already exists:", destination)
        return False

    shutil.copy2(source, destination)
    return True


def move_file(source, destination):
    if not os.path.exists(source):
        print("Source does not exist:", source)
        return False

    if os.path.exists(destination):
        print("Destination already exists:", destination)
        return False

    shutil.move(source, destination)
    return True


# ==================================================
# BROWSER ACTIONS
# ==================================================

def open_url(url):
    hotkey("ctrl", "l")
    type_text(url)
    press_key("enter")


def new_tab():
    hotkey("ctrl", "t")


def close_tab():
    hotkey("ctrl", "w")


def switch_tab():
    hotkey("ctrl", "tab")


def previous_tab():
    hotkey("ctrl", "shift", "tab")


def go_back():
    hotkey("alt", "left")


def go_forward():
    hotkey("alt", "right")


def refresh_page():
    press_key("f5")


# ==================================================
# ACTION DISPATCHER
# ==================================================

def execute_action(action, **kwargs):

    if action == "MOVE_MOUSE":
        move_mouse(kwargs["x"], kwargs["y"])

    elif action == "CLICK":
        click(kwargs["x"], kwargs["y"])

    elif action == "DOUBLE_CLICK":
        double_click(kwargs["x"], kwargs["y"])

    elif action == "RIGHT_CLICK":
        right_click(kwargs["x"], kwargs["y"])

    elif action == "DRAG":
        drag(
            kwargs["x1"],
            kwargs["y1"],
            kwargs["x2"],
            kwargs["y2"]
        )

    elif action == "TYPE":
        type_text(kwargs["text"])

    elif action == "PRESS":
        press_key(kwargs["key"])

    elif action == "HOTKEY":
        hotkey(*kwargs["keys"])

    elif action == "SCROLL":
        scroll(kwargs["amount"])

    elif action == "WAIT":
        wait(kwargs["seconds"])

    elif action == "SHOW_DESKTOP":
        show_desktop()

    elif action == "OPEN_START":
        open_start_menu()

    elif action == "OPEN_TASK_MANAGER":
        open_task_manager()

    elif action == "OPEN_RUN":
        show_run_dialog()

    elif action == "OPEN_SETTINGS":
        open_settings()

    elif action == "LOCK_PC":
        lock_pc()

    elif action == "COPY":
        copy_selection()

    elif action == "PASTE":
        paste_clipboard()

    elif action == "CUT":
        cut_selection()

    elif action == "SELECT_ALL":
        select_all()

    elif action == "UNDO":
        undo_action()

    elif action == "REDO":
        redo_action()

    elif action == "SAVE":
        save_current()

    elif action == "FIND":
        find_text()

    elif action == "VOLUME_UP":
        volume_up()

    elif action == "VOLUME_DOWN":
        volume_down()

    elif action == "VOLUME_MUTE":
        volume_mute()

    elif action == "MEDIA_PLAY_PAUSE":
        media_play_pause()

    elif action == "MEDIA_NEXT":
        media_next()

    elif action == "MEDIA_PREVIOUS":
        media_previous()

    elif action == "SNAP_LEFT":
        snap_left()

    elif action == "SNAP_RIGHT":
        snap_right()

    elif action == "SNAP_UP":
        snap_up()

    elif action == "SNAP_DOWN":
        snap_down()

    elif action == "OPEN_FILE_EXPLORER":
        open_file_explorer()

    elif action == "WINDOWS_SEARCH":
        open_windows_search()

    elif action == "NOTIFICATION_CENTER":
        open_notification_center()

    elif action == "QUICK_SETTINGS":
        open_quick_settings()

    elif action == "OPEN_CONTROL_PANEL":
        open_control_panel()

    elif action == "ZOOM_IN":
        zoom_in()

    elif action == "ZOOM_OUT":
        zoom_out()

    elif action == "ZOOM_RESET":
        zoom_reset()

    elif action == "PAGE_TOP":
        page_top()

    elif action == "PAGE_BOTTOM":
        page_bottom()

    elif action == "BROWSER_SEARCH":
        browser_search(kwargs["query"])

    elif action == "SEARCH_WEB":
        search_web(kwargs["query"])

    elif action == "OPEN_SPECIAL_FOLDER":
        open_special_folder(kwargs["name"])

    elif action == "RUN_COMMAND":
        run_command(kwargs["command"])

    elif action == "OPEN_APP":
        open_app(kwargs["app"])

    elif action == "CLOSE_WINDOW":
        close_window()

    elif action == "MINIMIZE_WINDOW":
        minimize_window()

    elif action == "MAXIMIZE_WINDOW":
        maximize_window()

    elif action == "SWITCH_WINDOW":
        switch_window()

    elif action == "OPEN_FOLDER":
        open_folder(kwargs["path"])

    elif action == "OPEN_FILE":
        open_file(kwargs["path"])

    elif action == "CREATE_FILE":
        create_file(kwargs["path"])

    elif action == "RENAME_FILE":
        rename_file(
            kwargs["old_path"],
            kwargs["new_path"]
        )

    elif action == "COPY_FILE":
        copy_file(
            kwargs["source"],
            kwargs["destination"]
        )

    elif action == "MOVE_FILE":
        move_file(
            kwargs["source"],
            kwargs["destination"]
        )

    elif action == "OPEN_URL":
        open_url(kwargs["url"])

    elif action == "NEW_TAB":
        new_tab()

    elif action == "CLOSE_TAB":
        close_tab()

    elif action == "SWITCH_TAB":
        switch_tab()

    elif action == "PREVIOUS_TAB":
        previous_tab()

    elif action == "GO_BACK":
        go_back()

    elif action == "GO_FORWARD":
        go_forward()

    elif action == "REFRESH":
        refresh_page()

    else:
        print("UNKNOWN ACTION:", action)
        return False

    return True


# ==================================================
# TEST
# ==================================================


def test_actions():

    print("================================")
    print("STEP 28 BROWSER TEST")
    print("================================")

    print("Opening Chrome...")

    execute_action(
        "OPEN_APP",
        app="chrome"
    )

    wait(3)

    print("Opening YouTube...")

    execute_action(
        "OPEN_URL",
        url="https://www.youtube.com"
    )

    wait(5)

    print("Browser test complete.")

# ============================================================
# CONTINUOUS VOICE LISTENER + NEWEST-COMMAND-WINS
# ============================================================
command_lock = threading.Lock()
latest_command = None
command_event = threading.Event()
stop_event = threading.Event()
task_active = False

# ==================================================
# GLOBAL WAKE / SLEEP MODE
# ==================================================
# The microphone remains available so the agent can hear the wake phrase,
# but computer commands are ignored while the agent is asleep.
WAKE_PHRASE = "wake up"
SLEEP_PHRASES = (
    "go to sleep",
    "sleep mode",
    "shut down listening",
    "stop listening",
)
agent_awake = False


def normalize_voice_text(text):
    return " ".join(text.lower().strip().split())


def is_sleep_command(text):
    normalized = normalize_voice_text(text)
    return normalized in SLEEP_PHRASES


def extract_wake_command(text):
    """Return (woke_up, command_after_wake_phrase)."""
    normalized = normalize_voice_text(text)

    if normalized == WAKE_PHRASE:
        return True, ""

    prefix = WAKE_PHRASE + " "
    if normalized.startswith(prefix):
        return True, normalized[len(prefix):].strip()

    return False, normalized


def submit_latest_command(command):
    """Handle wake/sleep mode and store only the newest active command."""
    global latest_command, agent_awake

    command = command.strip()
    if not command:
        return

    woke_up, command_after_wake = extract_wake_command(command)

    with command_lock:
        # Wake phrase can be used at any time. If it includes a command,
        # that command becomes active immediately.
        if woke_up:
            if not agent_awake:
                agent_awake = True
                print("\nWAKE MODE: AWAKE")

            command = command_after_wake

            if not command:
                return

        elif not agent_awake:
            # Sleeping means ordinary speech cannot control the computer.
            return

        # One global sleep command returns the agent to sleep mode.
        if is_sleep_command(command):
            agent_awake = False
            latest_command = None
            print("\nSLEEP MODE: microphone is waiting for 'Wake up'.")

            if task_active:
                stop_event.set()

            command_event.clear()
            return

        latest_command = command

        if task_active:
            # Tell the running task to stop at its next safe checkpoint.
            stop_event.set()

    command_event.set()


def voice_listener():
    """Keep the microphone open and continuously listen for commands."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.4

    try:
        with sr.Microphone() as source:
            print()
            print("================================")
            print("VOICE LISTENER STARTED")
            print("Say any computer command.")
            print("Newest command replaces the current task.")
            print("================================")

            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            while True:
                try:
                    audio = recognizer.listen(
                        source,
                        timeout=1,
                        phrase_time_limit=8
                    )

                    command = recognizer.recognize_google(audio).strip()

                    if command:
                        print()
                        print("VOICE INPUT:")
                        print(command)
                        print("--------------------------------")
                        submit_latest_command(command)

                except sr.WaitTimeoutError:
                    # Normal: no speech during this short listening window.
                    continue

                except sr.UnknownValueError:
                    print("Could not understand the speech. Please speak again. Listening again...")
                    continue

                except sr.RequestError as e:
                    print("Speech recognition error:", e)
                    time.sleep(2)

                except Exception as e:
                    print("Microphone error:", e)
                    time.sleep(2)

    except Exception as e:
        print("Could not start microphone listener:", e)
        command_event.set()


def get_latest_command():
    """Wait for a command, then atomically make it the active task."""
    global latest_command, task_active

    command_event.wait()

    with command_lock:
        command = latest_command
        latest_command = None
        task_active = True
        stop_event.clear()

        # If several commands arrived while we were busy, command is already
        # the newest one because submit_latest_command overwrites the old one.
        command_event.clear()

    return command


def finish_current_task():
    """Mark the current task as inactive."""
    global task_active

    with command_lock:
        task_active = False
        stop_event.clear()


def build_task_plan(command):
    """Create a short high-level plan using Gemini so simple commands avoid a second local Qwen generation."""
    plan = gemini_plan_command(command)
    if isinstance(plan, dict):
        steps = plan.get("steps") or []
        if steps:
            lines = []
            for item in steps[:10]:
                instruction = str(item.get("instruction", "")).strip()
                if instruction:
                    lines.append(f"{item.get('step', len(lines) + 1)}. {instruction}")
            if lines:
                return "\n".join(lines)
    return "1. Complete the user's command."

def ask_qwen_about_screen(command, previous_action="NONE", step_number=1, task_plan=""):
    screenshot = ImageGrab.grab()
    screenshot = screenshot.copy()
    screenshot.thumbnail((1152, 648))

    prompt = rf"""
You are an autonomous Windows computer-use agent.

USER'S GOAL:
{command}

HIGH-LEVEL TASK PLAN:
{task_plan}

CURRENT AGENT STEP:
{step_number}

PREVIOUS ACTION:
{previous_action}

You can see the CURRENT Windows screen in the image.
Accomplish the user's goal, not merely the wording of the command.

Think about what is visible, what has already happened, what the next useful
operation is, and how the result should be verified. If an application is
unknown, use Windows Search, Start, or Run. If a file is unknown, use File
Explorer or Windows Search. For websites, use the browser. For text entry,
use the keyboard. For clicks, use coordinates from the CURRENT screenshot.
For multi-step tasks, DO NOT stop after completing the first subgoal.
Perform exactly one low-level action now; the next screenshot will be used
to verify the result and continue with the remaining subgoals. Track the
COMPLETE USER'S GOAL and the HIGH-LEVEL TASK PLAN across all steps. If one
subgoal is complete, immediately continue toward the next requested subgoal.
If the previous action failed, recover another way.

AVAILABLE LOW-LEVEL ACTIONS:
ACTION: OPEN_APP, APP: application name
ACTION: OPEN_URL, URL: https://example.com
ACTION: CLICK, X: 500, Y: 300
ACTION: DOUBLE_CLICK, X: 500, Y: 300
ACTION: RIGHT_CLICK, X: 500, Y: 300
ACTION: MOVE_MOUSE, X: 500, Y: 300
ACTION: DRAG, X1: 500, Y1: 300, X2: 700, Y2: 400
ACTION: TYPE, TEXT: hello
ACTION: PRESS, KEY: enter
ACTION: HOTKEY, KEYS: ctrl+shift+esc
ACTION: SCROLL, DIRECTION: up
ACTION: SCROLL, DIRECTION: down
ACTION: WAIT, SECONDS: 1
ACTION: CLOSE_WINDOW
ACTION: MINIMIZE_WINDOW
ACTION: MAXIMIZE_WINDOW
ACTION: SWITCH_WINDOW
ACTION: SHOW_DESKTOP
ACTION: OPEN_START
ACTION: OPEN_TASK_MANAGER
ACTION: OPEN_RUN
ACTION: OPEN_SETTINGS
ACTION: LOCK_PC
ACTION: COPY
ACTION: PASTE
ACTION: CUT
ACTION: SELECT_ALL
ACTION: UNDO
ACTION: REDO
ACTION: SAVE
ACTION: FIND
ACTION: VOLUME_UP
ACTION: VOLUME_DOWN
ACTION: VOLUME_MUTE
ACTION: MEDIA_PLAY_PAUSE
ACTION: MEDIA_NEXT
ACTION: MEDIA_PREVIOUS
ACTION: SNAP_LEFT
ACTION: SNAP_RIGHT
ACTION: SNAP_UP
ACTION: SNAP_DOWN
ACTION: OPEN_FILE_EXPLORER
ACTION: WINDOWS_SEARCH
ACTION: NOTIFICATION_CENTER
ACTION: QUICK_SETTINGS
ACTION: OPEN_CONTROL_PANEL
ACTION: ZOOM_IN
ACTION: ZOOM_OUT
ACTION: ZOOM_RESET
ACTION: PAGE_TOP
ACTION: PAGE_BOTTOM
ACTION: BROWSER_SEARCH, QUERY: text to search
ACTION: SEARCH_WEB, QUERY: text to search
ACTION: RUN_COMMAND, COMMAND: command
ACTION: OPEN_FOLDER, PATH: C:\Users\...
ACTION: OPEN_FILE, PATH: C:\Users\...
ACTION: CREATE_FILE, PATH: C:\Users\...
ACTION: RENAME_FILE, OLD_PATH: ..., NEW_PATH: ...
ACTION: COPY_FILE, SOURCE: ..., DESTINATION: ...
ACTION: MOVE_FILE, SOURCE: ..., DESTINATION: ...
ACTION: OPEN_SPECIAL_FOLDER, NAME: downloads
ACTION: NEW_TAB
ACTION: CLOSE_TAB
ACTION: SWITCH_TAB
ACTION: PREVIOUS_TAB
ACTION: GO_BACK
ACTION: GO_FORWARD
ACTION: REFRESH
ACTION: DONE

RULES:
1. Look at the current screenshot before deciding.
2. Return EXACTLY ONE next action and no explanation.
3. Never invent screen coordinates.
4. Use OPEN_APP for applications and OPEN_URL for websites.
5. Use OPEN_SPECIAL_FOLDER for Desktop, Documents, Downloads, Pictures, Music, or Videos.
6. Use SEARCH_WEB for a web search when a browser does not need to be reused.
7. Use BROWSER_SEARCH when a browser is already open and a normal search is needed.
8. Use RUN_COMMAND only when the user's goal genuinely requires a Windows shell command.
9. Use LOCK_PC only when the user explicitly asks to lock the computer.
10. Return WAIT when the screen needs time to change.
11. Return DONE only when the user's actual goal is complete.
12. Do not return ACTION: NONE.
13. Do not assume an unknown app, file, button, or window exists without evidence.
14. Sensitive file/system actions are confirmed by the local agent before execution.
15. For compound commands, preserve the user's requested order and complete EVERY subgoal.
16. Do not return DONE merely because one application was opened, one search was performed, or one intermediate result appeared.
17. When a search is requested, verify that the intended search/result is visible before moving to the next requested operation.
18. When the user asks for an operation on an item (file, website, app, message, media, etc.), verify that the intended item is actually selected/affected before DONE.
19. Use the current screen as the source of truth; recover from unexpected screens instead of guessing.
20. DONE means the COMPLETE USER'S GOAL has been fulfilled.
"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": screenshot},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt"
    )

    inputs = {
        key: value.to(model.device) if hasattr(value, "to") else value
        for key, value in inputs.items()
    }

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,
            use_cache=True
        )

    generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]

    response = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0].strip()

    print()
    print("===== QWEN SCREEN DECISION =====")
    print(response)
    print("=================================")

    return response


# ============================================================
# SAFETY / CONFIRMATION LAYER
# ============================================================

CONFIRMATION_WORDS = {
    "yes", "yeah", "yep", "confirm", "confirmed", "do it",
    "okay", "ok", "proceed"
}

CANCEL_WORDS = {
    "no", "nope", "cancel", "stop", "don't", "do not",
    "abort"
}

SENSITIVE_ACTIONS = {
    "LOCK_PC",
    "RUN_COMMAND",
    "CREATE_FILE",
    "RENAME_FILE",
    "COPY_FILE",
    "MOVE_FILE",
}

def is_sensitive_action(action):
    return action in SENSITIVE_ACTIONS

def wait_for_confirmation(action_description):
    """
    Wait for one voice response while a sensitive action is pending.
    Only an explicit yes/confirmation proceeds. Everything else cancels.
    """
    print()
    print("================================")
    print("CONFIRMATION REQUIRED")
    print(action_description)
    print("Say YES to continue or NO to cancel.")
    print("================================")

    while True:
        command = get_latest_command()

        if not command:
            continue

        answer = command.lower().strip()

        if answer in CONFIRMATION_WORDS:
            print("Confirmation received.")
            return True

        if answer in CANCEL_WORDS:
            print("Action cancelled.")
            return False

        print("Please say YES to continue or NO to cancel.")


def run_qwen_action(command, interruption_event=None):
    import re

    # FAST PATH: ONLY truly simple open commands are handled directly.
    # Compound requests such as "open X and search Y" stay in the full
    # planning + vision loop so every requested operation is completed.
    command_clean = " ".join(command.strip().split())

    open_match = re.match(
        r"^(?:open|launch|start)\s+(.+)$",
        command_clean,
        re.IGNORECASE
    )

    compound_markers = (
        " and ", " then ", " after ", " before ", " also ",
        " search ", " find ", " play ", " type ", " click ",
        " close ", " save ", " create ", " rename ",
        " copy ", " move ", " download ", " upload ", " send ",
        " delete ", " go to ", " navigate "
    )

    if open_match and not any(marker in f" {command_clean.lower()} " for marker in compound_markers):
        target = open_match.group(1).strip()
        special_folders = {
            "desktop", "documents", "downloads", "pictures",
            "music", "videos"
        }

        if target.lower() in special_folders:
            print(f"FAST PATH: Opening {target}")
            if execute_action("OPEN_SPECIAL_FOLDER", name=target.lower()):
                return True
        else:
            print(f"FAST PATH: Opening application: {target}")
            if open_app(target):
                print("FAST PATH: Application launch sent.")
                return True
            print("FAST PATH failed. Falling back to full task mode.")

    MAX_STEPS = 20
    previous_action = "NONE"

    # Plan the complete request once, then let the existing vision/action loop
    # execute and verify the individual steps.
    task_plan = build_task_plan(command)

    for step in range(1, MAX_STEPS + 1):
        # Newest-command-wins: stop the current task before its next model/action cycle.
        if interruption_event is not None and interruption_event.is_set():
            print("New command received. Interrupting current task...")
            return False

        print()
        print("================================")
        print(f"AGENT STEP {step}/{MAX_STEPS}")
        print("================================")

        response = ask_qwen_about_screen(
            command,
            previous_action=previous_action,
            step_number=step,
            task_plan=task_plan
        )

        print()
        print("Qwen returned:")
        print(response)

        if interruption_event is not None and interruption_event.is_set():
            print("New command received while Qwen was processing. Discarding old task.")
            return False

        response_upper = response.upper()

        # ------------------------------------------
        # TASK COMPLETED
        # ------------------------------------------
        if re.search(r"ACTION\s*:\s*DONE\b", response_upper):
            print("Task completed.")
            return True

        # ------------------------------------------
        # WAIT
        # ------------------------------------------
        if "ACTION: WAIT" in response_upper:
            match = re.search(
                r"SECONDS:\s*([0-9]+(?:\.[0-9]+)?)",
                response,
                re.IGNORECASE
            )

            seconds = float(match.group(1)) if match else 1.0
            seconds = max(0.2, min(seconds, 10.0))

            print(f"Executing WAIT: {seconds} seconds")
            execute_action("WAIT", seconds=seconds)
            previous_action = f"WAIT {seconds}s"
            continue

        # ------------------------------------------
        # DOUBLE CLICK
        # ------------------------------------------
        if "ACTION: DOUBLE_CLICK" in response_upper:
            match = re.search(
                r"X:\s*(\d+).*?Y:\s*(\d+)",
                response, re.IGNORECASE
            )
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                print(f"Executing DOUBLE_CLICK: ({x}, {y})")
                execute_action("DOUBLE_CLICK", x=x, y=y)
                previous_action = f"DOUBLE_CLICK ({x},{y})"
                time.sleep(0.35)
                continue

        # ------------------------------------------
        # RIGHT CLICK
        # ------------------------------------------
        if "ACTION: RIGHT_CLICK" in response_upper:
            match = re.search(
                r"X:\s*(\d+).*?Y:\s*(\d+)",
                response, re.IGNORECASE
            )
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                print(f"Executing RIGHT_CLICK: ({x}, {y})")
                execute_action("RIGHT_CLICK", x=x, y=y)
                previous_action = f"RIGHT_CLICK ({x},{y})"
                time.sleep(0.35)
                continue

        # ------------------------------------------
        # DRAG
        # ------------------------------------------
        if "ACTION: DRAG" in response_upper:
            match = re.search(
                r"X1:\s*(\d+).*?Y1:\s*(\d+).*?"
                r"X2:\s*(\d+).*?Y2:\s*(\d+)",
                response, re.IGNORECASE
            )
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                print(f"Executing DRAG: ({x1},{y1}) -> ({x2},{y2})")
                execute_action(
                    "DRAG", x1=x1, y1=y1, x2=x2, y2=y2
                )
                previous_action = f"DRAG ({x1},{y1})->({x2},{y2})"
                time.sleep(0.35)
                continue

        # ------------------------------------------
        # MOVE MOUSE
        # ------------------------------------------
        if "ACTION: MOVE_MOUSE" in response_upper:
            match = re.search(
                r"X:\s*(\d+).*?Y:\s*(\d+)",
                response, re.IGNORECASE
            )
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                print(f"Executing MOVE_MOUSE: ({x}, {y})")
                execute_action("MOVE_MOUSE", x=x, y=y)
                previous_action = f"MOVE_MOUSE ({x},{y})"
                time.sleep(0.3)
                continue

        # ------------------------------------------
        # CLICK
        # ------------------------------------------
        if "ACTION: CLICK" in response_upper:
            match = re.search(
                r"X:\s*(\d+).*?Y:\s*(\d+)",
                response, re.IGNORECASE
            )
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                print(f"Executing CLICK: ({x}, {y})")
                execute_action("CLICK", x=x, y=y)
                previous_action = f"CLICK ({x},{y})"
                time.sleep(0.35)
                continue

        # ------------------------------------------
        # OPEN APP
        # ------------------------------------------
        if "ACTION: OPEN_APP" in response_upper:
            match = re.search(
                r"APP:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                app = match.group(1).strip()
                print(f"Executing OPEN_APP: {app}")
                execute_action("OPEN_APP", app=app)
                previous_action = f"OPEN_APP {app}"
                time.sleep(0.8)
                continue

        # ------------------------------------------
        # OPEN URL
        # ------------------------------------------
        if "ACTION: OPEN_URL" in response_upper:
            match = re.search(
                r"URL:\s*(\S+)",
                response, re.IGNORECASE
            )
            if match:
                url = match.group(1).strip()
                print(f"Executing OPEN_URL: {url}")
                execute_action("OPEN_URL", url=url)
                previous_action = f"OPEN_URL {url}"
                time.sleep(0.8)
                continue

        # ------------------------------------------
        # BROWSER SEARCH
        # ------------------------------------------
        if "ACTION: BROWSER_SEARCH" in response_upper:
            match = re.search(
                r"QUERY:\s*(.*)",
                response, re.IGNORECASE
            )
            if match:
                query = match.group(1).strip()
                print(f"Executing BROWSER_SEARCH: {query}")
                execute_action("BROWSER_SEARCH", query=query)
                previous_action = f"BROWSER_SEARCH {query}"
                time.sleep(0.8)
                continue

        # ------------------------------------------
        # SEARCH WEB
        # ------------------------------------------
        if "ACTION: SEARCH_WEB" in response_upper:
            match = re.search(
                r"QUERY:\s*(.*)",
                response, re.IGNORECASE
            )
            if match:
                query = match.group(1).strip()
                print(f"Executing SEARCH_WEB: {query}")
                execute_action("SEARCH_WEB", query=query)
                previous_action = f"SEARCH_WEB {query}"
                time.sleep(0.8)
                continue

        # ------------------------------------------
        # OPEN SPECIAL FOLDER
        # ------------------------------------------
        if "ACTION: OPEN_SPECIAL_FOLDER" in response_upper:
            match = re.search(
                r"NAME:\s*(.*)",
                response, re.IGNORECASE
            )
            if match:
                name = match.group(1).strip()
                print(f"Executing OPEN_SPECIAL_FOLDER: {name}")
                execute_action("OPEN_SPECIAL_FOLDER", name=name)
                previous_action = f"OPEN_SPECIAL_FOLDER {name}"
                time.sleep(0.8)
                continue

        # ------------------------------------------
        # RUN WINDOWS COMMAND
        # ------------------------------------------
        if "ACTION: RUN_COMMAND" in response_upper:
            match = re.search(
                r"COMMAND:\s*(.*)",
                response, re.IGNORECASE
            )
            if match:
                command_text = match.group(1).strip()
                approved = wait_for_confirmation(
                    f"Qwen wants to run this Windows command:\n{command_text}"
                )
                if not approved:
                    previous_action = "RUN_COMMAND CANCELLED"
                    continue
                print(f"Executing RUN_COMMAND: {command_text}")
                execute_action("RUN_COMMAND", command=command_text)
                previous_action = "RUN_COMMAND"
                time.sleep(0.8)
                continue

        # ------------------------------------------
        # TYPE
        # ------------------------------------------
        if "ACTION: TYPE" in response_upper:
            match = re.search(
                r"TEXT:\s*(.*)",
                response, re.IGNORECASE
            )
            if match:
                text = match.group(1).strip()
                print(f"Executing TYPE: {text}")
                execute_action("TYPE", text=text)
                previous_action = "TYPE"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # PRESS
        # ------------------------------------------
        if "ACTION: PRESS" in response_upper:
            match = re.search(
                r"KEY:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                key = match.group(1).strip()
                print(f"Executing PRESS: {key}")
                execute_action("PRESS", key=key)
                previous_action = f"PRESS {key}"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # HOTKEY
        # ------------------------------------------
        if "ACTION: HOTKEY" in response_upper:
            match = re.search(
                r"KEYS:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                keys = [
                    key.strip()
                    for key in match.group(1).split("+")
                    if key.strip()
                ]
                print(f"Executing HOTKEY: {keys}")
                execute_action("HOTKEY", keys=keys)
                previous_action = f"HOTKEY {'+'.join(keys)}"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # SCROLL
        # ------------------------------------------
        if "ACTION: SCROLL" in response_upper:
            match = re.search(
                r"DIRECTION:\s*(up|down)",
                response, re.IGNORECASE
            )
            if match:
                direction = match.group(1).lower()
                amount = 5 if direction == "up" else -5
                print(f"Executing SCROLL: {direction}")
                execute_action("SCROLL", amount=amount)
                previous_action = f"SCROLL {direction}"
                time.sleep(0.35)
                continue

        # ------------------------------------------
        # OPEN FOLDER / FILE
        # ------------------------------------------
        if "ACTION: OPEN_FOLDER" in response_upper:
            match = re.search(
                r"PATH:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                path = match.group(1).strip().strip('"')
                print(f"Executing OPEN_FOLDER: {path}")
                execute_action("OPEN_FOLDER", path=path)
                previous_action = f"OPEN_FOLDER {path}"
                time.sleep(1)
                continue

        if "ACTION: OPEN_FILE" in response_upper:
            match = re.search(
                r"PATH:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                path = match.group(1).strip().strip('"')
                print(f"Executing OPEN_FILE: {path}")
                execute_action("OPEN_FILE", path=path)
                previous_action = f"OPEN_FILE {path}"
                time.sleep(1)
                continue

        # ------------------------------------------
        # CREATE FILE
        # ------------------------------------------
        if "ACTION: CREATE_FILE" in response_upper:
            match = re.search(
                r"PATH:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                path = match.group(1).strip().strip('"')
                approved = wait_for_confirmation(
                    f"Qwen wants to create this file: {path}"
                )
                if not approved:
                    previous_action = "CREATE_FILE CANCELLED"
                    continue
                print(f"Executing CREATE_FILE: {path}")
                execute_action("CREATE_FILE", path=path)
                previous_action = f"CREATE_FILE {path}"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # RENAME FILE
        # ------------------------------------------
        if "ACTION: RENAME_FILE" in response_upper:
            match = re.search(
                r"OLD_PATH:\s*(.*?)\s*,\s*NEW_PATH:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                old_path = match.group(1).strip().strip('"')
                new_path = match.group(2).strip().strip('"')
                approved = wait_for_confirmation(
                    f"Qwen wants to rename:\n{old_path}\n→ {new_path}"
                )
                if not approved:
                    previous_action = "RENAME_FILE CANCELLED"
                    continue
                print(f"Executing RENAME_FILE: {old_path} -> {new_path}")
                execute_action(
                    "RENAME_FILE",
                    old_path=old_path,
                    new_path=new_path
                )
                previous_action = "RENAME_FILE"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # COPY FILE
        # ------------------------------------------
        if "ACTION: COPY_FILE" in response_upper:
            match = re.search(
                r"SOURCE:\s*(.*?)\s*,\s*DESTINATION:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                source = match.group(1).strip().strip('"')
                destination = match.group(2).strip().strip('"')
                approved = wait_for_confirmation(
                    f"Qwen wants to copy:\n{source}\n→ {destination}"
                )
                if not approved:
                    previous_action = "COPY_FILE CANCELLED"
                    continue
                print(f"Executing COPY_FILE: {source} -> {destination}")
                execute_action(
                    "COPY_FILE",
                    source=source,
                    destination=destination
                )
                previous_action = "COPY_FILE"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # MOVE FILE
        # ------------------------------------------
        if "ACTION: MOVE_FILE" in response_upper:
            match = re.search(
                r"SOURCE:\s*(.*?)\s*,\s*DESTINATION:\s*(.+)",
                response, re.IGNORECASE
            )
            if match:
                source = match.group(1).strip().strip('"')
                destination = match.group(2).strip().strip('"')
                approved = wait_for_confirmation(
                    f"Qwen wants to move:\n{source}\n→ {destination}"
                )
                if not approved:
                    previous_action = "MOVE_FILE CANCELLED"
                    continue
                print(f"Executing MOVE_FILE: {source} -> {destination}")
                execute_action(
                    "MOVE_FILE",
                    source=source,
                    destination=destination
                )
                previous_action = "MOVE_FILE"
                time.sleep(0.25)
                continue

        # ------------------------------------------
        # SIMPLE ACTIONS
        # ------------------------------------------
        simple_actions = [
            "CLOSE_WINDOW",
            "MINIMIZE_WINDOW",
            "MAXIMIZE_WINDOW",
            "SWITCH_WINDOW",
            "SHOW_DESKTOP",
            "OPEN_START",
            "OPEN_TASK_MANAGER",
            "OPEN_RUN",
            "OPEN_SETTINGS",
            "LOCK_PC",
            "COPY",
            "PASTE",
            "CUT",
            "SELECT_ALL",
            "UNDO",
            "REDO",
            "SAVE",
            "FIND",
            "VOLUME_UP",
            "VOLUME_DOWN",
            "VOLUME_MUTE",
            "MEDIA_PLAY_PAUSE",
            "MEDIA_NEXT",
            "MEDIA_PREVIOUS",
            "SNAP_LEFT",
            "SNAP_RIGHT",
            "SNAP_UP",
            "SNAP_DOWN",
            "OPEN_FILE_EXPLORER",
            "WINDOWS_SEARCH",
            "NOTIFICATION_CENTER",
            "QUICK_SETTINGS",
            "OPEN_CONTROL_PANEL",
            "ZOOM_IN",
            "ZOOM_OUT",
            "ZOOM_RESET",
            "PAGE_TOP",
            "PAGE_BOTTOM",
            "NEW_TAB",
            "CLOSE_TAB",
            "SWITCH_TAB",
            "PREVIOUS_TAB",
            "GO_BACK",
            "GO_FORWARD",
            "REFRESH",
        ]

        action_found = False

        for action in simple_actions:
            if f"ACTION: {action}" in response_upper:
                if is_sensitive_action(action):
                    approved = wait_for_confirmation(
                        f"Qwen wants to execute: {action}"
                    )
                    if not approved:
                        previous_action = f"{action} CANCELLED"
                        action_found = True
                        break

                print(f"Executing {action}")
                execute_action(action)
                previous_action = action
                action_found = True
                time.sleep(0.25)
                break

        if action_found:
            continue

        print("Qwen returned an unsupported action.")
        print(response)
        return False

    print()
    print("Maximum agent steps reached.")
    print("Returning to voice listening.")
    return False


if __name__ == "__main__":

    print("================================")
    print("QWEN COMPUTER AGENT")
    print("NEWEST-COMMAND-WINS MODE")
    print("GLOBAL WAKE/SLEEP MODE")
    print("Wake: Wake up")
    print("Sleep: Go to sleep")
    print("================================")
    print("SLEEP MODE: say 'Wake up' to activate the agent.")

    # One microphone listener runs continuously in the background while Qwen
    # works. This is what allows a newer voice command to interrupt a task.
    listener_thread = threading.Thread(
        target=voice_listener,
        daemon=True
    )
    listener_thread.start()

    while True:
        command = get_latest_command()

        if not command:
            finish_current_task()
            continue

        print()
        print("================================")
        print("STARTING COMMAND")
        print(command)
        print("================================")

        try:
            run_qwen_action(
                command,
                interruption_event=stop_event
            )
        except KeyboardInterrupt:
            print("Agent stopped by keyboard.")
            break
        except Exception as e:
            print("Agent error:", e)

        finish_current_task()

        print()
        print("READY FOR NEXT COMMAND")

        test_plan = gemini_plan_command(
    "open Chrome and search YouTube for relaxing music"
)

print("TEST PLAN:")
print(test_plan)

import reflex as rx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import uuid
from dotenv import load_dotenv
import os
import itertools

load_dotenv()
import threading
import random
import hashlib

from experiment_app.group_assignment import (
    get_group_counts as _get_group_counts,
    assign_group as _assign_group,
    load_saved_group as _load_saved_group,
)

# Import rxconfig once at module level to avoid repeated __pycache__ writes per call
try:
    from rxconfig import config as _rx_config
    _APP_BRANCH = "dev" if _rx_config.frontend_port == 3001 else "main"
except Exception:
    _APP_BRANCH = "unknown"

DEFAULT_MAX_QUESTIONS = 4

# Output directory — kept OUTSIDE the project tree so Vite's file watcher
# never picks up result/metadata writes and triggers spurious hot-reloads.
OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "output")
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------
# Prolific completion path URLs (replace with actual URLs later)
# ---------------------------------------------------------------
PROLIFIC_COMPLETION_URL = "https://app.prolific.com/submissions/complete?cc=C1BKV0DO"
PROLIFIC_FAILURE_URL = "https://app.prolific.com/submissions/complete?cc=C1FSXGG3"

class Argument(BaseModel):
    id: str
    text: str
    situation: str
    s_id: str
    critical_questions: List[str] = [] # Maps to "critical questions"
    answers: List[str] = []
    original_question_indices: List[int] = [] # Tracks original index before shuffle

    # class Config: (BaseModel handles Pydantic config internally)

class FullContext(BaseModel):
    id: str
    #s_id: str
    full_context: str
    questions: str

class ChatMessage(BaseModel):
    user: str
    assistant: str

class ExperimentState(rx.State):
    state_auto_setters = False

    # Load arguments as a class-level list of dicts (JSON is serializable)
    arguments: List[Argument] = []
    full_contexts: List[FullContext] = []
    selected_argument_groups: List[str] = []
    index: int = 0
    phase: str = "rating1"  # rating1 → chat → rating2
    rating_before: float | None = None
    rating_after: float | None = None
    temp_rating: float = 2.5
    rating_before_selected: bool = False
    rating_after_selected: bool = False
    show_rating_label: bool = False
    initialized: bool = False
    mid_instruction_type: str = "part2" # "part2" or "part3"
    experimental_group: str = "experimental" # "experimental" or "control"
    consent_accepted: bool = False
    consent_error: str = ""
    
    # Demographics
    age: str = ""
    gender: str = ""
    education: str = ""
    native_english: str = ""
    formal_training: str = ""
    formal_training_details: str = ""
    demographics_error: str = ""

    # Last Questions
    last_q1: str = ""
    last_q2: str = ""
    feedback: str = ""
    last_questions_error: str = ""
    discussion_error: str = ""

    @rx.var
    def last_questions_filled(self) -> bool:
        return all([
            self.last_q1,
            self.last_q2
        ])

    @rx.var
    def demographics_filled(self) -> bool:
        return all([
            self.age,
            self.gender,
            self.education,
            self.formal_training,
            (self.formal_training != "Yes") or bool(self.formal_training_details)
        ])

    # Prolific / Origin tracking
    prolific_pid: str = ""
    prolific_study_id: str = ""
    prolific_session_id: str = ""
    origin: str = "url"  # "prolific" or "url"
    recovery_id: str = ""

    # Session & Timing
    session_id: str = ""
    session_start: str = ""
    current_phase_start: str = "" # ISO format
    durations: dict = {}

    def set_temp_rating(self, value: list):
        # Slider returns a list [value]
        if self.is_attention_check:
            self.attention_check_rating = value[0]
            self.attention_check_selected = True
        elif self.phase == "rating1":
            self.temp_rating = value[0]
            self.rating_before_selected = True
        elif self.phase == "rating2":
            self.temp_rating = value[0]
            self.rating_after_selected = True

    def set_show_rating_label(self, show: bool):
        self.show_rating_label = show

    # Chat state
    chat_history: List[ChatMessage] = []
    influenced_answers: List[str] = [] # Format: "source:index"
    timer_end: str | None = None  # store datetime as ISO string
    allow_chat: bool = False
    chat_input: str = ""
    questions_asked: int = 0
    MAX_QUESTIONS: int = DEFAULT_MAX_QUESTIONS

    @rx.var
    def influenced_answers_options_with_metadata(self) -> List[Dict[str, Any]]:
        excluded = [
            "I don't have that information.",
            "I can only answer questions about the context."
        ]
        options = []
        
        # From chat
        for i, msg in enumerate(self.chat_history):
            ans = msg.assistant.strip()
            if ans and ans not in excluded:
                options.append({"text": ans, "source": "chat", "index": i, "id": f"chat:{i}"})
        
        # From provided questions
        if self.arguments and self.index < len(self.arguments):
            arg = self.arguments[self.index]
            for clicked_data in self.clicked_questions:
                clicked_idx = clicked_data["positional"]
                if clicked_idx < len(arg.answers):
                    ans = arg.answers[clicked_idx].strip()
                    if ans and ans not in excluded:
                        options.append({"text": ans, "source": "clicked", "index": clicked_idx, "id": f"clicked:{clicked_idx}"})
        
        # Deduplicate while preserving source/index
        seen_text = set()
        unique_options = []
        for opt in options:
            if opt["text"] not in seen_text:
                unique_options.append(opt)
                seen_text.add(opt["text"])
        return unique_options

    @rx.var
    def tutorial_influenced_answers_options_with_metadata(self) -> List[Dict[str, Any]]:
        excluded = [
            "I don't have that information.",
            "I can only answer questions about the context."
        ]
        options = []
        for i, msg in enumerate(self.tutorial_chat_history):
            ans = msg.assistant.strip()
            if ans and ans not in excluded:
                options.append({"text": ans, "source": "chat", "index": i, "id": f"chat:{i}"})
        
        seen_text = set()
        unique_options = []
        for opt in options:
            if opt["text"] not in seen_text:
                unique_options.append(opt)
                seen_text.add(opt["text"])
        return unique_options

    def toggle_influenced_answer(self, source: str, index: int):
        answer_id = f"{source}:{index}"
        if answer_id in self.influenced_answers:
            self.influenced_answers = [i for i in self.influenced_answers if i != answer_id]
        else:
            self.influenced_answers = self.influenced_answers + [answer_id]

    def toggle_tutorial_influenced_answer(self, source: str, index: int):
        self.toggle_influenced_answer(source, index)
    
    # Provided Questions state
    open_questions: List[int] = []
    clicked_questions: List[dict] = [] # Track unique clicked indices {"positional": int, "original": int}


    def set_chat_input(self, value: str):
        self.chat_input = value
        self.discussion_error = ""

    # Explicit setters for demographics and last questions
    def set_consent_accepted(self, value: bool):
        self.consent_accepted = value

    def set_age(self, value: str):
        self.age = value

    def set_gender(self, value: str):
        self.gender = value

    def set_education(self, value: str):
        self.education = value

    def set_formal_training(self, value: str):
        self.formal_training = value

    def set_formal_training_details(self, value: str):
        self.formal_training_details = value

    def set_native_english(self, value: str):
        self.native_english = value

    def set_last_q1(self, value: str):
        self.last_q1 = value

    def set_last_q2(self, value: str):
        self.last_q2 = value

    def set_feedback(self, value: str):
        self.feedback = value
        
    def toggle_question(self, index: int):
        if not self.arguments or self.index >= len(self.arguments):
            return
        if index in self.open_questions:
            self.open_questions.remove(index)
        else:
            # Enforce limit for opening new questions
            if len(self.open_questions) >= self.MAX_QUESTIONS:
                return
            
            self.open_questions.append(index)
            # Track as clicked if not already recorded (for data logging)
            if not any(q["positional"] == index for q in self.clicked_questions):
                orig_idx = self.arguments[self.index].original_question_indices[index]
                self.clicked_questions.append({"positional": index, "original": orig_idx})
            self.discussion_error = ""

    @rx.var
    def current_situation(self) -> str:
        if self.is_attention_check:
            return "This is a check to see if you are paying attention."
        if not self.arguments or self.index >= len(self.arguments):
            return ""
        # Accessing as attribute since it's a Pydantic model
        return self.arguments[self.index].situation

    @rx.var
    def current_argument_text(self) -> str:
        if self.is_attention_check:
            return "If you are, please rate this argument as 'Strong'."
        if not self.arguments or self.index >= len(self.arguments):
            return ""
        # Accessing as attribute since it's a Pydantic model
        return self.arguments[self.index].text

    @rx.var
    def current_step(self) -> int:
        if not self.arguments:
            return 0
        return min(self.index + 1, len(self.arguments))

    @rx.var
    def total_steps(self) -> int:
        return len(self.arguments)

    @rx.var
    def current_context(self) -> str:
        if not self.arguments or self.index >= len(self.arguments):
            return "No arguments loaded."
        current_arg = self.arguments[self.index]
        curr_id = str(current_arg.id).strip()
        for fc in self.full_contexts:
             if str(fc.id).strip() == curr_id:
                 return fc.full_context
        return "No context found for this argument (ID: " + curr_id + ")."

    # Tutorial state
    tutorial_step: int = 0
    tutorial_rating_before: float = 2.5
    tutorial_rating_after: float = 2.5
    tutorial_chat_history: List[ChatMessage] = [
        ChatMessage(
            user="Is there a situation in which Jess could have both a day job and keep the current salary?", 
            assistant="No, right now this is the only offer Jess has received."
        ),
        ChatMessage(
            user="Could a newer offer come up in the near future?", 
            assistant="Yes, Jess has been told that many new day positions could be opening in the next few months, with the exact same salary they have right now."
        ),
        ChatMessage(
            user="Is that a long wait for Jess?", 
            assistant="Not really, Jess is a bit tired of night shifts, but would prefer to keep the current salary."
        ),
        ChatMessage(
            user="What do you think of this situation?", 
            assistant="I can only answer questions about the context."
        )
    ]
    tutorial_chat_input: str = ""

    def next_tutorial_step(self):
        self.tutorial_step += 1

    def reset_tutorial(self):
        self.tutorial_step = 0
        self.tutorial_chat_history = [
            ChatMessage(
            user="Is there a situation in which Jess could have both a day job and keep the current salary?", 
            assistant="No, right now this is the only offer Jess has received."
        ),
        ChatMessage(
            user="Could a newer offer come up in the near future?", 
            assistant="Yes, Jess has been told that many new day positions could be opening in the next few months, with the exact same salary they have right now."
        ),
        ChatMessage(
            user="Is that a long wait for Jess?", 
            assistant="Not really, Jess is a bit tired of night shifts, but would prefer to keep the current salary."
        ),
        ChatMessage(
            user="What do you think of this situation?", 
            assistant="I can only answer questions about the context."
        )
        ]
        self.tutorial_chat_input = ""

    def set_tutorial_chat_input(self, value: str):
        self.tutorial_chat_input = value

    # @rx.event
    # def init_if_needed(self):
    #     """Load arguments at runtime, only once."""
    #     if self.initialized:
    #         return
            
    #     # ... (Argument loading code remains same) ...
    #     # (Since I'm replacing the whole block, I need to include the loading logic again or just inject methods. 
    #     # Actually, let's just add the methods after init_if_needed.
    #     # But wait, replace_file_content targets specific lines. 
    #     # I will inject the new methods BEFORE init_if_needed to keep it clean)

    # -------------------------------------------
    # Session Management
    # -------------------------------------------
    def init_session(self):
        if self.recovery_id:
            return self.recover_session(self.recovery_id)
            
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
            self.session_start = datetime.now().isoformat()
            self.current_phase_start = datetime.now().isoformat()
            self.durations = {}
            # NOTE: Do NOT call update_metadata() here.
            # The group has not been assigned yet (happens later in init_if_needed).
            # Writing metadata now would save the default group value ("experimental")
            # and cause get_group_counts() to count this session before it is assigned.

    def recover_session(self, recovery_id: str):
        metadata_path = os.path.join(OUTPUT_DIR, f"{recovery_id}_metadata.json")
        if not os.path.exists(metadata_path):
            print(f"Recovery failed: {metadata_path} not found.")
            return

        try:
            with open(metadata_path, "r") as f:
                data = json.load(f)
            
            # Restore core session info
            self.session_id = data.get("session_id", recovery_id)
            self.session_start = data.get("start_time", "")
            self.experimental_group = data.get("experimental_group", "experimental")
            self.origin = data.get("origin", "url")
            self.prolific_pid = data.get("prolific_pid", "")
            self.prolific_study_id = data.get("prolific_study_id", "")
            self.prolific_session_id = data.get("prolific_session_id", "")
            
            # Restore demographics
            demographics = data.get("demographics", {})
            self.age = demographics.get("age", "")
            self.gender = demographics.get("gender", "")
            self.education = demographics.get("education", "")
            self.native_english = demographics.get("native_english", "")
            self.formal_training = demographics.get("formal_training", "")
            self.formal_training_details = demographics.get("formal_training_details", "")
            
            # Restore last questions
            last_q = data.get("last_questions", {})
            self.last_q1 = last_q.get("q1", "")
            self.last_q2 = last_q.get("q2", "")
            self.feedback = last_q.get("feedback", "")
            
            self.attention_checks = data.get("attention_checks", [])
            self.consent_accepted = True  # Assume consent if metadata exists
            
            # Load results to find progress
            results_path = os.path.join(OUTPUT_DIR, f"{self.session_id}_results.jsonl")
            #progress = 0
            last_index = -1
            if os.path.exists(results_path):
                with open(results_path, "r") as rf:
                    for line in rf:
                        if line.strip():
                            trial = json.loads(line)
                            #if trial.get("argument_index") != -1:
                            #    progress += 1
                            idx = trial.get("argument_index")
                            if idx is not None and idx != -1:
                                last_index = max(last_index, idx)
            
            #self.index = progress
            self.index = last_index + 1
            self.initialized = False  # Reset initialization so arguments are re-loaded
            self.init_if_needed()
            
            # Determine redirection
            if self.index >= len(self.arguments):
                return rx.redirect("/last-questions")
            elif self.index in [6, 12]:
                self.mid_instruction_type = "part2" if self.index == 6 else "part3"
                return rx.redirect("/mid-instructions")
            else:
                return rx.redirect("/argument")
                
        except Exception as e:
            print(f"Error recovering session: {e}")

    def update_metadata(self, end_time=None):
        if not self.session_id:
            return
        
        branch = _APP_BRANCH

        data = {
            "session_id": self.session_id,
            "branch": branch,
            "experimental_group": self.experimental_group,
            "origin": self.origin,
            "prolific_pid": self.prolific_pid,
            "prolific_study_id": self.prolific_study_id,
            "prolific_session_id": self.prolific_session_id,
            "start_time": self.session_start,
            "end_time": end_time,
            "demographics": {
                "age": self.age,
                "gender": self.gender,
                "education": self.education,
                "native_english": self.native_english,
                "formal_training": self.formal_training,
                "formal_training_details": self.formal_training_details
            },
            "last_questions": {
                "q1": self.last_q1,
                "q2": self.last_q2,
                "feedback": self.feedback
            },
            "argument_groups": self.selected_argument_groups,
            "attention_checks": self.attention_checks
        }
        
        with open(os.path.join(OUTPUT_DIR, f"{self.session_id}_metadata.json"), "w") as f:
            json.dump(data, f, indent=2)

    @rx.event
    def capture_url_params(self):
        """Read Prolific query params from the URL and set origin flag."""
        params = self.router.page.params
        pid = params.get("PROLIFIC_PID", "")
        study = params.get("STUDY_ID", "")
        session = params.get("SESSION_ID", "")
        recovery = params.get("recovery_id", "")
        self.prolific_pid = pid
        self.prolific_study_id = study
        self.prolific_session_id = session
        self.recovery_id = recovery
        self.origin = "prolific" if pid else "url"

    def record_current_phase_duration(self, phase_name: str):
        if not self.current_phase_start:
            self.current_phase_start = datetime.now().isoformat()
            return
            
        start = datetime.fromisoformat(self.current_phase_start)
        now = datetime.now()
        duration_seconds = (now - start).total_seconds()
        
        self.durations[phase_name] = duration_seconds
        self.current_phase_start = now.isoformat() # Reset for next phase

    def finish_session(self):
        self.update_metadata(end_time=datetime.now().isoformat())

    def submit_consent(self):
        if not self.consent_accepted:
            self.consent_error = "Consenting is necessary to proceed with the experiment. If you do not consent, please close the tab."
            return
        self.consent_error = ""
        return rx.redirect("/demographics")

    def submit_demographics(self):
        missing = []
        if not self.age: missing.append("Age")
        if not self.gender: missing.append("Gender")
        if not self.education: missing.append("Education Level")
        #if not self.native_english: missing.append("Language Background")
        if not self.formal_training: missing.append("Formal Training")
        
        if missing:
            self.demographics_error = f"Please fill in the following information: {', '.join(missing)}"
            return

        if self.formal_training == "Yes" and not self.formal_training_details.strip():
            self.demographics_error = "Please specify what kind of training you have received."
            return

        # Age validation
        age_str = self.age.strip()
        try:
            age_int = int(age_str)
            if age_int < 18:
                self.demographics_error = "You must be 18 or older to participate."
                return
            if age_int >= 100:
                self.demographics_error = "Please enter a valid age under 100."
                return
        except ValueError:
            self.demographics_error = "Age must be an integer."
            return
            
        self.age = age_str # Save stripped version
        self.demographics_error = ""
        self.update_metadata()
        return rx.redirect("/instructions")

    def submit_last_questions(self):
        missing = []
        if not self.last_q1: missing.append("Question 1")
        if not self.last_q2: missing.append("Question 2")
        
        if missing:
            self.last_questions_error = f"Please answer the mandatory questions: {', '.join(missing)}"
            return
            
        self.last_questions_error = ""
        self.update_metadata()
        return rx.redirect("/debriefing")

    def submit_debriefing(self):
        self.finish_session()
        # Prolific completion path: redirect Prolific participants to the completion URL
        if self.origin == "prolific":
            return rx.redirect(PROLIFIC_COMPLETION_URL)
        return rx.redirect("/finished")

    @rx.event
    def check_consent(self):
        if not self.consent_accepted:
             return rx.redirect("/")

    @rx.event
    def check_demographics(self):
        if not self.consent_accepted:
             return rx.redirect("/")
        if not self.demographics_filled:
             return rx.redirect("/demographics")

    # -------------------------------------------
    # Initialization
    # -------------------------------------------
    def get_group_counts(self):
        """Delegate to group_assignment module (testable standalone)."""
        return _get_group_counts(
            output_dir=OUTPUT_DIR,
            current_branch=_APP_BRANCH,
            current_session_id=self.session_id,
        )

    def _load_arguments_and_contexts(self):
        """Load argument groups and full contexts into state. Called by init_if_needed."""
        print('Loading arguments...')
        group_files = [
            "experiment_app/data/arguments_group_1.json",
            "experiment_app/data/arguments_group_2.json",
            "experiment_app/data/arguments_group_3.json",
            "experiment_app/data/arguments_group_4.json",
            "experiment_app/data/arguments_group_5.json"
        ]
        # 1. Generate all valid combinations (filtering out FORBIDDEN ones)
        all_combinations = list(itertools.permutations(range(5), 3))
        FORBIDDEN = {(1, 2, 3), (2, 3, 4), (3, 4, 0), (4, 0, 1), (0, 1, 2)}
        valid_combinations = [c for c in all_combinations if c not in FORBIDDEN]

        # Deterministic argument group selection based on session_id (separate hash from group assignment)
        h_args = hashlib.md5((self.session_id + ":args").encode()).hexdigest()
        session_hash_args = int(h_args, 16)
        #start_idx = session_hash_args % 5 # keep this only because its referenced later

        # Avoid overrepresented combinations
        combo_idx = session_hash_args % len(valid_combinations)
        selected_indices = valid_combinations[combo_idx]

        selected_groups = [group_files[i] for i in selected_indices]
        self.selected_argument_groups = [os.path.basename(g).replace(".json", "") for g in selected_groups]

        all_arguments = []
        for group_file in selected_groups:
            try:
                with open(group_file) as f:
                    data = json.load(f)

                for item in data:
                    if "critical questions" in item:
                        item["critical_questions"] = item.pop("critical questions")

                    arg = Argument(**item)
                    if arg.critical_questions and arg.answers:
                        arg.original_question_indices = list(range(len(arg.critical_questions)))
                        combined = list(zip(arg.critical_questions, arg.answers, arg.original_question_indices))
                        random.shuffle(combined)
                        arg.critical_questions, arg.answers, arg.original_question_indices = zip(*combined)
                        arg.critical_questions = list(arg.critical_questions)
                        arg.answers = list(arg.answers)
                        arg.original_question_indices = list(arg.original_question_indices)

                    all_arguments.append(arg)
            except Exception as e:
                print(f"Error loading group file {group_file}: {e}")

        self.arguments = all_arguments
        print(f'Loaded {len(self.arguments)} arguments from {selected_groups} (offset {combo_idx})')

        print('Loading contexts...')
        try:
            with open("experiment_app/data/full-contexts.json") as f:
                c_data = json.load(f)

            new_contexts = []
            for item in c_data:
                fc_text = item.get("full context", item.get("full_context", ""))
                new_contexts.append(FullContext(
                    id=str(item["id"]),
                    full_context=fc_text,
                    questions=item.get("questions", "")
                ))
            self.full_contexts = new_contexts
            print(f"Loaded {len(self.full_contexts)} contexts")
        except Exception as e:
            print(f"Error loading full-contexts.json: {e}")

    @rx.event
    def init_if_needed(self):
        """Load arguments at runtime, only once per session."""
        if self.initialized:
            return

        if not self.session_id:
            self.capture_url_params()
            self.init_session()

        # --- Reconnection guard ---
        # Reflex may rebuild state on WebSocket reconnections, resetting `initialized`
        # to False. If a metadata file already exists for this session, restore the
        # previously assigned group from disk instead of re-running the balancing logic.
        saved_group = _load_saved_group(OUTPUT_DIR, self.session_id)
        if saved_group:
            print(f"Reconnection detected — restoring group '{saved_group}' from disk for session {self.session_id}")
            self.experimental_group = saved_group
            self._load_arguments_and_contexts()
            self.initialized = True
            return

        # --- New session: balance and assign group ---
        exp_count, ctrl_count = self.get_group_counts()
        print(f"Current group counts (finished/recent): experimental={exp_count}, control={ctrl_count}")

        self.experimental_group = _assign_group(self.session_id, exp_count, ctrl_count)
        print(f"Assigned to group: {self.experimental_group}")

        self._load_arguments_and_contexts()

        self.initialized = True
        # Write metadata now — group is already assigned, so the file is correct from the start.
        self.update_metadata()



    # -------------------------------------------
    # Rating methods
    # -------------------------------------------
    # -------------------------------------------
    # Rating methods
    # -------------------------------------------
    def submit_rating_before(self):
        if self.phase != "rating1":
            return
        self.record_current_phase_duration("rating1")
        self.rating_before = self.temp_rating
        self.phase = "chat"
        self.start_chat_timer()
        # Reset temp rating for next phase? Maybe keep it or reset
        self.temp_rating = 2.5
        self.rating_before_selected = False
        self.rating_after_selected = False
        self.discussion_error = ""

    is_attention_check: bool = False
    attention_check_id: int = 0
    attention_check_rating: float = 2.5
    attention_check_selected: bool = False
    attention_checks: List[dict] = []  # Accumulated attention check results
    attention_check_1_failed: bool = False  # True if AC1 was failed (rating not in [3.5, 4.0])

    def submit_rating_after(self):
        if self.phase != "rating2":
            return
        self.record_current_phase_duration("rating2")
        self.rating_after = self.temp_rating
        self.save_trial()

        # Move to next argument
        self.index += 1
        
        # Check for attention checks before continuing
        if self.index == 1:
            return self.show_attention_check(1)
        if self.index == 3:
            return self.show_attention_check(2)
        if self.index == 13:
            return self.show_attention_check(3)

        return self.continue_after_rating()

    def show_attention_check(self, ac_id: int):
        self.is_attention_check = True
        self.attention_check_id = ac_id
        self.attention_check_rating = 2.5
        self.attention_check_selected = False
        return rx.redirect("/argument")

    def submit_attention_check(self):
        if not self.is_attention_check or not self.attention_check_selected:
            return
        
        # Calculate duration
        start = datetime.fromisoformat(self.current_phase_start)
        now = datetime.now()
        duration_seconds = (now - start).total_seconds()
        self.current_phase_start = now.isoformat() # Reset for whatever comes next

        # Determine Experimental Phase (same logic as save_trial)
        experimental_phase = "pre-intervention"
        if self.experimental_group == "experimental":
            if 6 <= self.index < 12:
                experimental_phase = "intervention"
            elif self.index >= 12:
                experimental_phase = "post-intervention"
        else:
            if 6 <= self.index < 12:
                experimental_phase = "control-session-2"
            elif self.index >= 12:
                experimental_phase = "control-session-3"

        # Log the attention check
        trial_data = {
            "session_id": self.session_id,
            "experimental_group": self.experimental_group,
            "argument_index": -1, # Marker for attention check
            "argument_id": f"attention check {self.attention_check_id}",
            "order": self.index, # Current position
            "experimental_phase": experimental_phase,
            "rating": self.attention_check_rating,
            "timestamp": now.isoformat(),
            "durations": {"attention_check": duration_seconds}
        }

        filename = os.path.join(OUTPUT_DIR, f"{self.session_id}_results.jsonl")
        try:
            with open(filename, "a") as o:
                o.write(json.dumps(trial_data) + "\n")
        except Exception as e:
            print(f"Error saving attention check: {e}")

        # Accumulate attention check result for metadata
        ac_entry = {
            "id": self.attention_check_id,
            "order": self.index,
            "rating": self.attention_check_rating,
            "timestamp": trial_data["timestamp"]
        }
        self.attention_checks = self.attention_checks + [ac_entry]
        self.update_metadata()

        self.is_attention_check = False

        # Prolific completion path: screen out only if BOTH AC1 and AC2 are failed.
        # A correct response is a rating of 4 ("Strong"). Any other value is a failure (we also accept 3.5).
        if self.origin == "prolific":
            failed = self.attention_check_rating not in [3.5, 4.0]
            if self.attention_check_id == 1:
                self.attention_check_1_failed = failed
            elif self.attention_check_id == 2 and failed and self.attention_check_1_failed:
                return rx.redirect(PROLIFIC_FAILURE_URL)

        return self.continue_after_rating()

    def continue_after_rating(self):
        if self.index >= len(self.arguments):
            return rx.redirect("/last-questions")

        # Check for interstitial pages (index 6 means we just finished arg 6, entering phase 2)
        # Check for interstitial pages (index 12 means we just finished arg 12, entering phase 3)
        if self.index == 6:
            self.mid_instruction_type = "part2"
            # Reset for next argument but redirect to instructions first
            self.reset_for_next_arg()
            return rx.redirect("/mid-instructions")
        
        if self.index == 12:
            self.mid_instruction_type = "part3"
            # Reset for next argument but redirect to instructions first
            self.reset_for_next_arg()
            return rx.redirect("/mid-instructions")
        
        # For other indices, just reset for next argument
        self.reset_for_next_arg()
        return rx.redirect("/argument")

    def reset_for_next_arg(self):
        self.phase = "rating1"
        self.rating_before = None
        self.rating_after = None
        self.temp_rating = 2.5
        self.questions_asked = 0
        self.allow_chat = True
        self.influenced_answers = []
        self.timer_end = None
        self.open_questions = []
        self.clicked_questions = []
        self.chat_history = []
        self.rating_before_selected = False
        self.rating_after_selected = False

    
    def force_finish_chat(self):
        if self.phase != "chat":
            return
        # Validation: check if at least one question was asked
        if len(self.chat_history) == 0 and len(self.clicked_questions) == 0:
            self.discussion_error = "Please ask at least 1 question before proceeding."
            return

        self.discussion_error = ""
        self.record_current_phase_duration("chat")
        self.allow_chat = False
        self.phase = "rating2"


    # -------------------------------------------
    # Chat / Timer methods
    # -------------------------------------------
    time_left_label: str = "1:00"

    def start_chat_timer(self):
        # Phase 2 (index 6-11) are "Provided Questions" phase for experimental group
        if self.experimental_group == "experimental" and 6 <= self.index < 12:
             self.allow_chat = False # Chat input disabled, but phase is 'chat' to show questions
             self.timer_end = None
             return

        # Store datetime as ISO string for serialization
        self.timer_end = (datetime.now() + timedelta(minutes=3)).isoformat()
        self.allow_chat = True
        self.time_left_label = "3:00"
        self.questions_asked = 0

    def tick(self, _=None):
        """Called every second via frontend timer."""
        if self.timer_end:
            now = datetime.now()
            end = datetime.fromisoformat(self.timer_end)
            if now >= end:
                # Timer expired - but we disable automatic transition as per USER_REQUEST to remove timer
                # self.record_current_phase_duration("chat")
                # self.allow_chat = False
                # self.phase = "rating2"
                # self.time_left_label = "0:00"
                pass
            else:
                # Update label
                diff = end - now
                minutes, seconds = divmod(diff.seconds, 60)
                self.time_left_label = f"{minutes}:{seconds:02d}"

    def ask_llm(self, form_data: dict = None):
        """Process chat message with optimistic UI updates."""
        if not self.arguments or self.index >= len(self.arguments):
            return
        if not self.allow_chat or not self.chat_input.strip():
            return
        if self.questions_asked >= self.MAX_QUESTIONS:
            return

        self.discussion_error = ""
        question = self.chat_input
        self.chat_input = ""
        self.questions_asked += 1
        
        # 1. Optimistic Update: Show user message immediately with loading state
        # We use a placeholder for assistant response
        self.chat_history.append(ChatMessage(user=question, assistant="..."))
        yield

        arg_id = self.index
        current_arg = self.arguments[self.index]
        
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Update last message with error
                self.chat_history[-1] = ChatMessage(user=question, assistant="Error: OPENAI_API_KEY not found in .env")
                return

            llm = ChatOpenAI(model="gpt-5.4", api_key=api_key, reasoning_effort="low", temperature=0.0)
            
            # Find the full context for this argument
            context_text = "No context found."
            curr_id = str(current_arg.id).strip()
            for fc in self.full_contexts:
                if str(fc.id).strip() == curr_id:
                    context_text = fc.full_context
                    break
            
            # Load few shot examples
            few_shot_json_path = os.path.join(os.path.dirname(__file__), "data", "few-shot.json")
            few_shot_data = {}
            if os.path.exists(few_shot_json_path):
                try:
                    with open(few_shot_json_path, 'r', encoding='utf-8') as f:
                        few_shot_data = json.load(f)
                except Exception as e:
                    print(f"Error loading few-shot.json: {e}")
            
            fs_examples = few_shot_data.get(curr_id)
            if not fs_examples:
                fs_examples = few_shot_data.get("1", {"do": [], "avoid": []})
            
            few_shot_text = ""
            if fs_examples.get("do") or fs_examples.get("avoid"):
                few_shot_text = "Here are some examples of how to answer (Good) and how NOT to answer (Bad):\n"
                if fs_examples.get("do"):
                    few_shot_text += "\nGood Examples:\n"
                    for ex in fs_examples["do"]:
                        few_shot_text += f"- Question: {ex['question']}\n  Answer: {ex['answer']}\n"
                
                if fs_examples.get("avoid"):
                    few_shot_text += "\nBad Examples (Avoid this style):\n"
                    for ex in fs_examples["avoid"]:
                        few_shot_text += f"- Question: {ex['question']}\n  Answer: {ex['answer']}\n"

            # Build rigid system prompt as requested
            system_msg = (
                "You are a neutral information assistant. "
                "You have access to a private context document. "
                "Your only function is to answer the user's questions strictly based on that document.\n\n"
                "Rules:\n"
                "1. Answer based on the information available in the context. You may combine facts from different parts of the context if, and only if, all of them are necessary to answer the specific question asked. Do not introduce facts that are relevant to the situation but answer a different question than the one asked.\n"
                "2. If the context contains partial or ambiguous information relevant to the question, answer with what is available and indicate clearly that the information is incomplete.\n"
                "3. If the context contains no information whatsoever relevant to the question, say only: I don't have that information. However, if the context explicitly states or clearly implies that something does not exist, has not happened, or is unknown to a character, convey that directly as a fact (e.g. \"Jay does not know...\", \"Alex can't remember...\"). Never use phrases like \"the context does not...\" or \"the context provides...\" — instead, express the absence of information in first person: \"I don't have that information\", or as a fact about the character: \"River hasn't looked into that.\".\n"
                "4. Answer in one or two short sentences maximum. Be precise and factual.\n"
                "5. Answer only what the question directly asks for. Do not add related information, qualifications, or additional facts that were not requested. In particular, never extend your answer with connectors like \"however\", \"although\", \"but\", \"additionally\", or \"also\" to introduce unrequested information. For example, if asked \"Does X have experience?\", answer only whether they do or not; do not add what limitations that experience has, unless explicitly asked. If asked about a budget, answer with the budget, not with what they can or cannot afford with it.\n"
                "6. Do not hint at, evaluate, or comment on the relevance of any information. Your tone must be completely neutral and flat.\n"
                "7. Never reveal that you are working from a context document. Never use phrases like \"the context\", \"the document\", \"based on the context\", \"the context doesn't specify\", or similar. To express absence or ambiguity, use these alternatives instead:\n"
                "Instead of \"the context doesn't specify X\" → \"It's not clear whether X\"\n"
                "Instead of \"based on the context\" → simply state the fact directly\n"
                "Instead of \"the context says\" → state the information as a plain fact\n"
                "8. If the user sends something that is not a request for information, respond only with: I can only answer questions about the context.\n"
                "9. Answer in one sentence only. Do not add a second sentence with related information, context, or qualifications. If the answer genuinely requires two pieces of information to be complete, combine them into a single sentence.\n\n"
                f"{few_shot_text}\n"
                f"Context:\n{context_text}"
            )

            #print(system_msg)
            
            messages = [("system", system_msg)]
            # Exclude the last message (the one we just added) from history to avoid confusion
            # or include it as the latest user message.
            # `self.chat_history` has the new message at [-1].
            # We need to construct history from previous messages + current question.
            
            for msg in self.chat_history[:-1]:
                messages.append(("human", msg.user))
                messages.append(("assistant", msg.assistant))
            messages.append(("human", question))
            
            # 2. Call LLM
            # THE PRINT SHOULD BE REMOVED BEFORE LAUNCHING THE EXPERIMENT
            # print("\n" + "="*60)
            # print("[LLM CALL] Full prompt being sent to OpenAI:")
            # for role, content in messages:
            #     print(f"\n[{role.upper()}]:\n{content}")
            # print("="*60 + "\n")
            response = None
            for attempt in range(5):
                try:
                    response = llm.invoke(messages)
                    break

                except InternalServerError as e:
                    print(f"OpenAI server error: {e}", flush=True)

                    if attempt == 4:
                        raise

                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

            answer = response.content if response else ""
            
                
            # 3. Update with real response
            self.chat_history[-1] = ChatMessage(user=question, assistant=answer)
            
            # If the response is the exact sentence "I don't have that information.",
            # do not count it towards the question limit.
            if answer.strip() == "I don't have that information.":
                self.questions_asked -= 1
            
        except Exception as e:
            print(f"[ERROR] Chat failed: {e}")
            self.chat_history[-1] = ChatMessage(user=question, assistant=f"Error: {str(e)}")



    # -------------------------------------------
    # Save results
    # -------------------------------------------
    def save_trial(self):
        if not self.session_id:
            # Fallback if accessed directly without init
            self.init_session()

        if not self.arguments or self.index >= len(self.arguments):
            print(f"Warning: save_trial called with index {self.index} out of range (total arguments: {len(self.arguments)})")
            return

        current_arg = self.arguments[self.index]
        
        # Determine Experimental Phase
        # 0-5: pre-intervention, 6-11: intervention, 12-17: post-intervention
        experimental_phase = "pre-intervention"
        if self.experimental_group == "experimental":
            if 6 <= self.index < 12:
                experimental_phase = "intervention"
            elif self.index >= 12:
                experimental_phase = "post-intervention"
        else:
            # Control group has no intervention, but we can still label the segments for analysis
            if 6 <= self.index < 12:
                experimental_phase = "control-session-2"
            elif self.index >= 12:
                experimental_phase = "control-session-3"

        # Save only serializable info
        trial_data = {
            "session_id": self.session_id,
            "experimental_group": self.experimental_group,
            "argument_index": self.index,
            "argument_id": current_arg.id,
            "argument_s_id": current_arg.s_id,
            "order": self.index + 1,
            "experimental_phase": experimental_phase,
            "argument_text": current_arg.text,
            "situation_text": current_arg.situation,
            # "phase" in typical reflex sense is 'rating2' at this point, but we log the experimental nature above
            "rating_before": self.rating_before,
            "rating_after": self.rating_after,
            "chat_history": [msg.dict() for msg in self.chat_history],
            "influenced_answers": self.influenced_answers,
            "clicked_questions": self.clicked_questions if experimental_phase == "intervention" else [],
            "durations": self.durations.copy()
        }

        # Use session-specific filename
        filename = os.path.join(OUTPUT_DIR, f"{self.session_id}_results.jsonl")
        
        try:
            with open(filename, "a") as o:
                o.write(json.dumps(trial_data) + "\n")
        except Exception as e:
            print(f"Error saving trial: {e}")
            
        # Reset durations for next trial
        self.durations = {}

    # THIS SHOULD BE REMOVED BEFORE LAUNCHING
    def debug_jump(self, target_index: int):
        self.index = target_index
        if target_index >= 16:
            self.mid_instruction_type = "part3"
        elif target_index >= 8:
            self.mid_instruction_type = "part2"
        
        self.reset_for_next_arg()
        return rx.redirect("/mid-instructions")
    
    def skip_demographics(self):
        self.age = "25"
        self.gender = "other"
        self.education = "none"
        self.native_english = "Other"
        self.formal_training = "Not sure"
        self.formal_training_details = ""
        self.demographics_error = ""
        self.update_metadata()
        return rx.redirect("/instructions")

    def toggle_experimental_group(self):
        if self.experimental_group == "experimental":
            self.experimental_group = "control"
        else:
            self.experimental_group = "experimental"
    
    def goto_last_questions(self):
        return rx.redirect("/last-questions")
    
    def goto_debriefing(self):
        return rx.redirect("/debriefing")
    # THIS SHOULD BE REMOVED BEFORE LAUNCHING

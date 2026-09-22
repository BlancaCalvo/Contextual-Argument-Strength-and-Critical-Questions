import reflex as rx
from ...state import ExperimentState
from ...ui.style import Theme as Th

def step_indicator(step_number, title, active_phase, current_phase_index):
    """
    Renders a single step in the vertical stepper.
    step_number: 1, 2, 3
    title: "Initial Rating", etc.
    active_phase: the current phase string from state
    current_phase_index: 0, 1, 2 (mapped from active_phase)
    """
    
    # Determine state: completed, active, or pending
    # We map phase string to index: rating1=0, chat=1, rating2=2
    step_index = step_number - 1
    
    is_completed = step_index < current_phase_index
    is_active = step_index == current_phase_index
    
    # Define styles using rx.cond since we are dealing with Vars
    color = rx.cond(
        is_active,
        Th.PRIMARY,
        rx.cond(is_completed, "white", "gray") # Text color inside circle for completed is white
    )
    
    circle_bg = rx.cond(
        is_completed,
        Th.SUCCESS,
        "transparent"
    )
    
    circle_border = rx.cond(
        is_active,
        f"2px solid {Th.PRIMARY}",
        rx.cond(
            is_completed,
            f"2px solid {Th.SUCCESS}",
            "2px solid gray"
        )
    )
    
    text_color = rx.cond(
        is_active,
        Th.PRIMARY,
        "gray"
    )
    
    font_weight = rx.cond(
        is_active,
        "bold",
        "normal"
    )

    return rx.hstack(
        # Circle
        rx.center(
            rx.cond(
                is_completed,
                rx.icon(tag="check", color="white", size=16),
                rx.text(str(step_number), color=color, font_weight="bold", font_size="0.8rem")
            ),
            width="2rem",
            height="2rem",
            border_radius="50%",
            bg=circle_bg,
            border=circle_border,
            flex_shrink=0
        ),
        # Text
        rx.text(title, color=text_color, font_weight=font_weight),
        align_items="center",
        spacing="3"
    )

def vertical_stepper():
    state = ExperimentState
    
    # Map phase to index
    # rating1 -> 0
    # chat -> 1
    # rating2 -> 2
    phase_idx = rx.cond(
        state.is_attention_check, 0,
        rx.cond(
            state.phase == "rating1", 0,
            rx.cond(state.phase == "chat", 1, 2)
        )
    )

    return rx.vstack(
        step_indicator(1, "Initial Rating", state.phase, phase_idx),
        # Connector line
        rx.box(width="2px", height="2rem", bg="lightgray", margin_left="1rem"),
        step_indicator(2, "Discussion", state.phase, phase_idx),
        # Connector line
        rx.box(width="2px", height="2rem", bg="lightgray", margin_left="1rem"),
        step_indicator(3, "Final Rating", state.phase, phase_idx),
        
        align_items="start",
        spacing="1"
    )

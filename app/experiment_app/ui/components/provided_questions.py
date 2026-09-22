import reflex as rx
from ...state import ExperimentState
from ..style import style, card_style, text_style

def question_item(question: str, index: int):
    """Renders a single question that can be toggled to show its answer."""
    # We need to get the answer from the state based on position
    # The answer list is in state.arguments[state.index].answers
    # We can assume the order matches.
    
    return rx.vstack(
        rx.box(
            rx.text(question, **text_style(color=style["color"], size="1rem")),
            on_click=lambda: ExperimentState.toggle_question(index),
            cursor="pointer",
            padding="1rem",
            bg=rx.cond(ExperimentState.open_questions.contains(index), "#e0e7ff", "#f1f5f9"), # Indigo 50 vs Slate 100
            border_radius="0.5rem",
            width="100%",
            _hover={"bg": "#e2e8f0"}
        ),
        rx.cond(
            ExperimentState.open_questions.contains(index),
            rx.box(
                rx.text(
                     ExperimentState.arguments[ExperimentState.index].answers[index],
                     **text_style(color=style["color"], size="1rem")
                ),
                padding="1rem",
                bg="#f8fafc",
                border_left="4px solid #6366f1", # Indigo 500 border
                width="100%",
                margin_top="0.5rem"
            )
        ),
        width="100%",
        spacing="2"
    )

def provided_questions_view():
    """Renders the list of provided questions for the current argument."""
    state = ExperimentState
    return rx.vstack(
        rx.text("Click on a question to reveal the answer:", **text_style(size="1rem", color="#64748b")),
        rx.text(
            f"Questions Opened: {state.open_questions.length()}/{state.MAX_QUESTIONS}",
            color="#64748b",
            font_size="0.8rem",
            text_align="right",
            width="100%",
        ),
        rx.cond(
            state.open_questions.length() >= state.MAX_QUESTIONS,
            rx.text(
                f"Question limit reached ({state.MAX_QUESTIONS}/{state.MAX_QUESTIONS}). You may finish the evaluation.",
                color="crimson",
                font_size="0.9rem",
                font_weight="bold",
                text_align="center",
                width="100%",
                padding_y="0.5rem"
            ),
        ),
        rx.foreach(
            state.arguments[state.index].critical_questions,
            lambda q, i: question_item(q, i)
        ),
        width="100%",
        spacing="3"
    )

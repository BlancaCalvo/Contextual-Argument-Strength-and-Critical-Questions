import reflex as rx
from ...state import ExperimentState
from ..style import style, primary_button_style, Theme, text_style

def chat_bubble(text, is_user):
    return rx.box(
        rx.text(text, color="white" if is_user else style["color"]),
        bg=Theme.PRIMARY if is_user else style["background_color"],
        padding="0.75rem 1rem",
        border_radius="1rem 1rem 0 1rem" if is_user else "1rem 1rem 1rem 0",
        max_width="80%",
        align_self="flex-end" if is_user else "flex-start",
        box_shadow="0 1px 2px 0 rgb(0 0 0 / 0.05)"
    )

def chat_box(history=None, input_value=None, on_change=None, on_submit=None, show_questions_asked=True, height="auto", min_height="200px"):
    state = ExperimentState
    
    # Use provided props or default to state
    history = history if history is not None else state.chat_history
    input_value = input_value if input_value is not None else state.chat_input
    on_change = on_change if on_change is not None else state.set_chat_input
    on_submit = on_submit if on_submit is not None else state.ask_llm

    chat_content = rx.vstack(
        rx.foreach(
            history,
            lambda msg: rx.vstack(
                chat_bubble(msg.user, True),
                chat_bubble(msg.assistant, False),
                width="100%",
                spacing="2"
            )
        ),
        width="100%",
        padding="1rem",
        spacing="4",
    )

    return rx.vstack(
        rx.text(f"You can ask up to {state.MAX_QUESTIONS} questions to challenge the argument:", **text_style(size="1rem", color="#64748b")),
        rx.cond(
            height == "auto",
            rx.box(
                chat_content,
                min_height=min_height,
                width="100%",
                style={"border": f"1px solid #e2e8f0", "border_radius": "0.5rem"}
            ),
            rx.scroll_area(
                chat_content,
                height=height,
                type="always",
                scrollbars="vertical",
                style={"border": f"1px solid #e2e8f0", "border_radius": "0.5rem"}
            ),
        ),
        rx.cond(
            show_questions_asked,
            rx.text(
                f"Questions Asked: {state.questions_asked}/{state.MAX_QUESTIONS}",
                color="#64748b",
                font_size="0.8rem",
                text_align="right",
                width="100%",
            ),
        ),
        rx.cond(
            (state.questions_asked >= state.MAX_QUESTIONS) & show_questions_asked,
            rx.text(
                f"Question limit reached ({state.MAX_QUESTIONS}/{state.MAX_QUESTIONS}). You may finish the discussion.",
                color="crimson",
                font_size="0.9rem",
                font_weight="bold",
                text_align="center",
                width="100%",
            ),
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Type your question here...", 
                        value=input_value,
                        on_change=on_change,
                        width="100%",
                        border_radius="0.5rem",
                        border="1px solid #e2e8f0",
                        padding="0.5rem 1rem",
                        color="black",
                        class_name="age-input",
                        background_color="white",
                        border_color="gray"
                    ),
                    rx.button(
                        "Send", 
                        type="submit",
                        **primary_button_style()
                    ),
                    width="100%",
                    spacing="2"
                ),
                on_submit=on_submit,
                width="100%"
            ),
        ),
        width="100%",
        spacing="4"
    )

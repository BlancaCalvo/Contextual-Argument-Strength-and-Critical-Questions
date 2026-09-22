import reflex as rx
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style, Theme
from ...state import ExperimentState
from ..components.rating_scale import rating_scale
from ..components.chat_box import chat_box

def tutorial_step_box(step_index: int, title: str, content: str, position_props: dict, has_next=True):
    state = ExperimentState
    return rx.cond(
        state.tutorial_step == step_index,
        rx.box(
            rx.vstack(
                rx.text(title, font_weight="bold", font_size="1.1rem"),
                rx.text(content, font_size="1rem"),
                rx.hstack(
                    rx.spacer(),
                    rx.cond(
                        has_next,
                        rx.button("Next", on_click=state.next_tutorial_step, size="3", color_scheme="indigo"),
                        rx.button("Ready! Start Experiment", on_click=rx.redirect("/argument"), size="3", color_scheme="green")
                    ),
                    width="100%"
                ),
                spacing="3",
                align_items="start"
            ),
            padding="1.5rem",
            bg="white",
            border=f"2px solid {Theme.PRIMARY}",
            border_radius="1rem",
            box_shadow="0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            z_index="1000",
            position="absolute",
            width="350px",
            **position_props
        )
    )

def example_page():
    state = ExperimentState
    
    # Placeholder data for the tutorial
    example_situation = "Jess, a close colleague of yours, tired of night-and-weekend shifts, is considering switching to a daytime office job with a lower starting salary for more predictable hours. Alex, another colleague, argues:"
    example_argument = "Either accept lower pay now or keep missing weekends and holidays."

    return rx.box(
        rx.center(
            rx.vstack(
                # Step 0: Instructions Intro
                rx.box(
                    rx.vstack(
                        rx.heading("How it works", **heading_style("lg")),
                        rx.text(
                            "Before we start, let's walk through an example. For each argument, you will follow a specific sequence, let's see it!",
                            **text_style()
                        ),
                        rx.divider(),
                        spacing="4",
                    ),
                    padding="2rem",
                    bg="white",
                    border_radius="1rem",
                    width="100%",
                    margin_bottom="2rem"
                ),

                # Main Experiment Card (Layout matched to argument_page.py)
                rx.box(
                    rx.vstack(
                        # Situation & Argument Box
                        rx.box(
                            rx.vstack(
                                # Situation Box
                                rx.box(
                                    rx.text("Situation:", font_weight="bold", **text_style(size="0.9rem", color="gray")),
                                    rx.text(example_situation, **text_style(size="1.1rem")),
                                    bg=Theme.SITUATION_BLUE,
                                    padding="1rem",
                                    border_radius="0.5rem",
                                    width="100%",
                                    margin_y="0.5rem",
                                    border="1px solid #bfdbfe",
                                    opacity=rx.cond(state.tutorial_step >= 1, "1", "0.3"),
                                ),
                                # Argument Box
                                rx.box(
                                    rx.text("Argument:", font_weight="bold", **text_style(size="0.9rem", color="gray")),
                                    rx.text(example_argument, **text_style(color=style["color"], size="1.125rem")),
                                    bg=style["background_color"],
                                    padding="1.5rem",
                                    border_radius="0.5rem",
                                    width="100%",
                                    margin_y="0.5rem",
                                    border=f"1px solid #e2e8f0",
                                    opacity=rx.cond(state.tutorial_step >= 1, "1", "0.3"),
                                ),
                                tutorial_step_box(
                                    1, 
                                    "The Situation & Argument", 
                                    "In every trial, you'll first read a context (the Situation) and a claim (the Argument). Start by reading these carefully.", 
                                    {"top": "2rem", "right": "-30rem"}
                                ),
                                width="100%"
                            ),
                            position="relative",
                            width="100%"
                        ),

                        # First Rating
                        rx.box(
                            rx.vstack(
                                rx.text("Step 1: Initial Rating", font_weight="bold", **text_style(size="1.1rem")),
                                rx.text("How would you rate this argument?", **text_style(size="0.9rem")),
                                rating_scale(
                                    value=[state.tutorial_rating_before],
                                    on_change=lambda v: [], # Valid empty event
                                    show_label=state.show_rating_label,
                                    on_hover=state.set_show_rating_label,
                                    color_scheme="indigo"
                                ),
                                opacity=rx.cond(state.tutorial_step >= 2, "1", "0.3"),
                                spacing="2",
                                width="100%",
                                align_items="start"
                            ),
                            tutorial_step_box(
                                2, 
                                "Initial Impression", 
                                "Next, you'll provide your first rating of the argument's strength based on your initial intuition.", 
                                {"top": "0rem", "right": "-30rem"}
                            ),
                            margin_top="1rem",
                            width="100%",
                            position="relative"
                        ),

                        # Chat Box
                        rx.box(
                            rx.vstack(
                                rx.heading("Step 2: Questioning", **heading_style("sm")),
                                chat_box(
                                    history=state.tutorial_chat_history,
                                    input_value=state.tutorial_chat_input,
                                    on_change=state.set_tutorial_chat_input,
                                    on_submit=lambda: [], # Valid empty event
                                    show_questions_asked=False,
                                    height="auto"
                                ),
                                opacity=rx.cond(state.tutorial_step >= 3, "1", "0.3"),
                                spacing="4",
                                width="100%"
                            ),
                            tutorial_step_box(
                                3, 
                                "Challenge the Argument", 
                                f"In the chat, you can ask questions about the context that might weaken or strengthen the argument. Try to find holes in the argument asking from 1 to {ExperimentState.MAX_QUESTIONS} questions. Remember you are challenging the argument, not deciding what the person should do.", 
                                {"top": "0rem", "right": "-30rem"}
                            ),
                            tutorial_step_box(
                                4, 
                                "Rules of the chat", 
                                "If you do not ask a question about the context, the chat will refuse to answer. If the question is about the context but the chat does not have the information you are asking for, the question won't count towards the limit.\nDo NOT use any AI tools. Ask ONLY questions.",
                                {"top": "0rem", "right": "-30rem"}
                            ),
                            margin_top="2rem",
                            width="100%",
                            position="relative"
                        ),

                         # Second Rating
                        rx.box(
                            rx.vstack(
                                rx.text("Step 3: Final Rating", font_weight="bold", **text_style(size="1.1rem")),
                                rx.text("Re-evaluate after questioning:", **text_style(size="0.9rem")),
                                rating_scale(
                                    value=[state.tutorial_rating_after],
                                    on_change=lambda v: [], # Valid empty event
                                    show_label=state.show_rating_label,
                                    on_hover=state.set_show_rating_label,
                                    color_scheme="indigo"
                                ),
                                rx.vstack(
                                    rx.text("Indicate which answers have influenced your rating, if any:", **text_style(size="0.9rem")),
                                    rx.vstack(
                                        rx.foreach(
                                            state.tutorial_influenced_answers_options_with_metadata,
                                            lambda opt: rx.checkbox(
                                                opt["text"],
                                                on_change=lambda checked: state.toggle_tutorial_influenced_answer(opt["source"], opt["index"]),
                                                checked=state.influenced_answers.contains(opt["id"]),
                                                color_scheme="indigo",
                                            )
                                        ),
                                        align_items="start",
                                        spacing="2",
                                    ),
                                    width="100%",
                                    align_items="start",
                                    padding_y="0.5rem"
                                ),
                                opacity=rx.cond(state.tutorial_step >= 5, "1", "0.3"),
                                spacing="2",
                                width="100%",
                                align_items="start"
                            ),
                            tutorial_step_box(
                                5, 
                                "Final Evaluation", 
                                "After gathering more information, you'll rate the argument a second time. Your rating might change or stay the same depending on what you've learned. Also, tell us what information has influenced your rating.", 
                                {"top": "0rem", "right": "-30rem"}
                            ),
                            margin_top="2rem",
                            width="100%",
                            position="relative"
                        ),

                        spacing="4",
                        width="100%"
                    ),
                    **card_style(),
                    width="100%",
                    max_width="1000px",
                    position="relative"
                ),

                # Intro and Outro bubbles still absolute in outer container but adjusted
                tutorial_step_box(
                    0, 
                    "Let's start!", 
                    "Click Next to begin.", 
                    {"top": "2rem", "right": "-5rem"}
                ),
                tutorial_step_box(
                    6, 
                    "Ready to Start?", 
                    "You will now see 18 real arguments. Good luck!", 
                    {"bottom": "15rem", "right": "-5rem"},
                    has_next=False
                ),

                width="100%",
                max_width="1400px",
                position="relative", # Needed for absolute intro/outro bubbles
                padding_bottom="10rem"
            ),
            width="100%",
            **container_style(max_width="100%")
        ),
        bg=style["background_color"],
        min_height="100vh",
        width="100%",
        on_mount=state.reset_tutorial
    )

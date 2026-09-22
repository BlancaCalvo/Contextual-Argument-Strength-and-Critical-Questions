import reflex as rx
from ...state import ExperimentState
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style

def instructions_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.heading("Experiment Instructions", 
                        **heading_style("xl"), 
                        align_items="center"
                    ),
                    rx.text(
                        "Welcome! You will participate in a study evaluating arguments.",
                        **text_style(size="1.125rem"),
                        align_items="center"
                    ),
                    rx.divider(margin_y="1.5rem"),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("star", size=24, color=style["color"]),
                            rx.text("You will see 18 distinct arguments.", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.icon("message-circle", size=24, color=style["color"], flex_shrink=0),
                            rx.vstack(
                                rx.text(
                                    "Please read the situation and the argument given. Then ",
                                    rx.text.strong("rate the strength of this argument between 1 (the argument does not hold) and 4 (this is a strong argument)."),
                                    **text_style()
                                ),
                                rx.text(
                                    "Once you have rated it, proceed to the next step, where you will be allowed to ask questions about the exact context in which this argument is being used. Here you should ",
                                    rx.text.strong("ask questions which allow you to challenge the argument’s strength"),
                                    " in this concrete context.",
                                    **text_style()
                                ),
                                rx.text(
                                    "Ask only questions whose answers could change your perceived strength of the argument. That is, if you think that certain answers could make the argument less valid, ask the questions. Keep in mind you are assessing the strength of the argument, not deciding what the person should do. Try to be objective and not rely on your assumptions about the context.",
                                    **text_style()
                                ),
                                rx.text(
                                    "You will have to ask ",
                                    rx.text.strong(f"a minimum of 1 question and a maximum of {ExperimentState.MAX_QUESTIONS} questions"),
                                    ".",
                                    **text_style()
                                ),
                                rx.text(
                                    "Then, you will get a ",
                                    rx.text.strong("second opportunity to rate the argument’s strength"),
                                    ". This time, you should consider the argument’s strength taking into account the information you have gathered through your questions.",
                                    **text_style()
                                ),
                                rx.text(
                                    "You should complete this study in one go. Do not overthink your questions. You are not allowed to go back to change any rating nor to ask more questions. If you get any error just refresh the page, you will not lose your previous answers.",
                                    **text_style()
                                ),
                                rx.text(
                                    rx.text.strong("Do NOT use any AI tools."),
                                    " Your submission will be rejected if you do so.",
                                    **text_style()
                                ),
                                rx.text(
                                    "Proceed to see an example.",
                                    **text_style()
                                ),
                                spacing="3",
                                align_items="start",
                                width="100%"
                            ),
                            align_items="start",
                            spacing="4",
                            width="100%"
                        ),
                        align_items="start",
                        spacing="4",
                        width="100%",
                        padding_y="1rem"
                    ),
                    rx.divider(margin_y="1.5rem"),
                    rx.button(
                        "See An Example", 
                        on_click=rx.redirect("/example"),
                        **primary_button_style(),
                        width="100%"
                    ),
                    # THIS SHOULD BE REMOVED BEFORE LAUNCHING
                    # rx.divider(margin_y="0.5rem", border_color="red"),
                    # rx.text("DEBUG CONTROLS", color="red", font_weight="bold", font_size="0.8rem"),
                    # rx.hstack(
                    #     rx.button("Jump to Part 2 (Arg 7)", on_click=lambda: ExperimentState.debug_jump(6), size="2", color_scheme="red", variant="outline"),
                    #     rx.button("Jump to Part 3 (Arg 13)", on_click=lambda: ExperimentState.debug_jump(12), size="2", color_scheme="red", variant="outline"),
                    #     rx.button("Jump to Arg 18", on_click=lambda: ExperimentState.debug_jump(17), size="2", color_scheme="red", variant="outline"),
                    #     rx.button("Jump to Debriefing", on_click=ExperimentState.goto_debriefing, size="2", color_scheme="red", variant="outline"),
                    #     spacing="2",
                    #     width="100%",
                    #     justify_content="center"
                    # ),
                    # THIS SHOULD BE REMOVED BEFORE LAUNCHING
                    spacing="4",
                    align_items="start",
                    width="100%"
                ),
                **card_style(),
                width="100%",
                max_width="1400px",
            ),
            **container_style(max_width="1600px")
        ),
        bg=style["background_color"],
        min_height="100vh",
        width="100%",
        on_mount=ExperimentState.init_session
    )



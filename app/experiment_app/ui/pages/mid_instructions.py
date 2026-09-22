import reflex as rx
from ...state import ExperimentState
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style

def mid_instructions_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.cond(
                        ExperimentState.experimental_group == "experimental",
                        rx.cond(
                            ExperimentState.mid_instruction_type == "part2",
                            rx.heading("New Instructions: Part 2", **heading_style("xl")),
                            rx.heading("New Instructions: Part 3", **heading_style("xl"))
                        ),
                        rx.heading("Progress Update", **heading_style("xl"))
                    ),
                    rx.divider(margin_y="1.5rem"),
                    
                    # Content for Experimental Group - Part 2 (Arguments 9-16)
                    rx.cond(
                        (ExperimentState.experimental_group == "experimental") & (ExperimentState.mid_instruction_type == "part2"),
                        rx.vstack(
                            rx.text(
                                "For the next 6 arguments you won't have to ask questions.",
                                **text_style(size="1.125rem")
                            ),
                            rx.text(
                                f"Instead, you will have questions provided. Click on the questions to read the answer. You will only be able to see the answer of {ExperimentState.MAX_QUESTIONS} questions, choose wisely.",
                                **text_style(size="1.125rem")
                            ),
                            spacing="4"
                        )
                    ),

                    # Content for Experimental Group - Part 3 (Arguments 17-24)
                    rx.cond(
                        (ExperimentState.experimental_group == "experimental") & (ExperimentState.mid_instruction_type != "part2"),
                        rx.vstack(
                            rx.text(
                                "You have finished the 6 arguments with provided questions.",
                                **text_style(size="1.125rem")
                            ),
                            rx.text(
                                f"Now you will get the opportunity to write your own {ExperimentState.MAX_QUESTIONS} questions again.",
                                **text_style(size="1.125rem")
                            ),
                            spacing="4"
                        )
                    ),

                    # Content for Control Group
                    rx.cond(
                        ExperimentState.experimental_group != "experimental",
                        rx.vstack(
                            rx.cond(
                                ExperimentState.mid_instruction_type == "part2",
                                rx.text(
                                    "You have completed a third of the experiment!",
                                    **text_style(size="1.125rem")
                                ),
                                rx.text(
                                    "You have completed two thirds of the experiment!",
                                    **text_style(size="1.125rem")
                                )
                            ),
                            spacing="4"
                        )
                    ),
                    
                    rx.divider(margin_y="1.5rem"),
                    rx.button(
                        "Understood", 
                        on_click=rx.redirect("/argument"),
                        **primary_button_style(),
                        width="100%"
                    ),
                    spacing="4",
                    align_items="start",
                    width="100%"
                ),
                **card_style(),
                width="100%",
                max_width="600px",
            ),
            **container_style()
        ),
        bg=style["background_color"],
        min_height="100vh",
        width="100%"
    )

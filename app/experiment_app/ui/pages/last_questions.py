import reflex as rx
from ...state import ExperimentState
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style

def last_questions_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.heading("Final Questions", 
                        **heading_style("xl"), 
                        align_items="center"
                    ),
                    rx.text(
                        "Please answer these final questions before finishing the experiment. Your feedback is very important to us.",
                        **text_style(size="1.125rem"),
                        align_items="center"
                    ),
                    rx.divider(margin_y="1.5rem"),
                    
                    rx.vstack(
                        # Question 1: Instruction Clarity
                        rx.vstack(
                            rx.text("How clear were the instructions provided at the beginning of the experiment?", font_weight="bold", **text_style()),
                            rx.radio_group(
                                ["Very Unclear", "Unclear", "Clear", "Very Clear"],
                                value=ExperimentState.last_q1,
                                on_change=ExperimentState.set_last_q1,
                                direction="row",
                                spacing="4",
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),
                        
                        # Question 2: AI Helpfulness
                        rx.vstack(
                            rx.text("Did you find the chatbot's answers helpful for evaluating the argument's strength?", font_weight="bold", **text_style()),
                            rx.radio_group(
                                ["Very Unhelpful", "Unhelpful", "Helpful", "Very Helpful"],
                                value=ExperimentState.last_q2,
                                on_change=ExperimentState.set_last_q2,
                                direction="row",
                                spacing="4",
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),
                        
                        # Feedback Box
                        rx.vstack(
                            rx.text("Do you have any other comments or feedback about the experiment? (Optional)", font_weight="bold", **text_style()),
                            rx.text_area(
                                placeholder="Write your comments here...",
                                on_change=ExperimentState.set_feedback,
                                width="100%",
                                height="150px",
                                color="black",
                                background_color="white",
                                class_name="text-area-input"
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),
                        
                        spacing="6",
                        width="100%",
                        padding_y="1rem"
                    ),
                    
                    rx.divider(margin_y="1.5rem"),
                    
                    rx.cond(
                        ExperimentState.last_questions_error,
                        rx.text(
                            ExperimentState.last_questions_error, 
                            color="red", 
                            font_weight="bold",
                            margin_bottom="1rem"
                        ),
                    ),
                    
                    rx.button(
                        "Finish", 
                        on_click=ExperimentState.submit_last_questions,
                        **primary_button_style(),
                        width="100%"
                    ),
                    
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
        on_mount=[ExperimentState.init_session, ExperimentState.check_demographics]
    )

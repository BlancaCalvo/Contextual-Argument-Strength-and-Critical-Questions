import reflex as rx
from ...state import ExperimentState
from ..components.rating_scale import rating_scale
from ..components.chat_box import chat_box
from ..components.timer import countdown_timer
from ..components.stepper import vertical_stepper
from ..components.provided_questions import provided_questions_view
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style, situation_color, Theme

def argument_page():
    state = ExperimentState
    # Attention Check conditional content
    situation_label = state.current_situation
    argument_label = state.current_argument_text
    
    # Progress calculation — guard against division by zero (total_steps=0 before init_if_needed loads arguments)
    current_step = state.current_step
    total_steps = state.total_steps
    progress = rx.cond(total_steps > 0, (current_step / total_steps) * 100, 0)

    return rx.box(
        rx.center(
            rx.hstack(
                # Sidebar (Stepper) - Strictly to the left
                rx.box(
                    vertical_stepper(),
                    rx.cond(
                        (state.phase == "chat") & ((state.experimental_group == "control") | ((state.index < 6) | (state.index >= 12))),
                        rx.box(
                            # rx.text("Time Remaining", font_weight="bold", color="gray", font_size="0.8rem"),
                            # rx.text(state.time_left_label, font_size="2rem", font_weight="bold", color="darkgrey"),
                            rx.text("Questions Asked", font_weight="bold", color="gray", font_size="0.8rem", margin_top="1rem"),
                            rx.text(
                                state.questions_asked.to_string() + "/" + state.MAX_QUESTIONS.to_string(),
                                font_size="2rem",
                                font_weight="bold",
                                color=rx.cond(
                                    state.questions_asked >= state.MAX_QUESTIONS,
                                    "crimson",
                                    "darkgrey"
                                )
                            ),
                            margin_top="2rem",
                            border_top="1px solid #e2e8f0",
                            padding_top="1rem",
                        )
                    ),
                    width="200px",
                    padding_right="2rem",
                    display=["none", "none", "block"],
                    position="sticky",
                    top="2rem",
                ),
                
                # Main Content Column (Progress + Card)
                rx.vstack(
                    # Progress Bar (hidden during attention check to mimic step 1 exactly)
                    rx.cond(
                        ~state.is_attention_check,
                        rx.box(
                            rx.progress(value=progress, width="100%", color_scheme="indigo"),
                            width="100%",
                            padding_bottom="1rem"
                        )
                    ),
                    
                    # Main Card
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.heading(f"Argument", **heading_style("md")),
                                rx.spacer(),
                                rx.cond(
                                    ~state.is_attention_check,
                                    rx.text(f"Question {state.current_step} of {state.total_steps}", **text_style()),
                                ),
                                on_mount=ExperimentState.init_if_needed, 
                                width="100%",
                                align_items="center",
                                padding_bottom="0.5rem"
                            ),
                            rx.divider(),
                            
                            # Content Column
                            rx.vstack(
                                # Situation Box
                                rx.box(
                                    rx.text("Situation:", font_weight="bold", **text_style(size="0.9rem", color="gray")),
                                    rx.text(situation_label, **text_style(size="1.1rem")),
                                    bg=rx.cond(state.index % 2 == 0, Theme.SITUATION_BLUE, Theme.SITUATION_PURPLE),
                                    padding="1rem",
                                    border_radius="0.5rem",
                                    width="100%",
                                    margin_y="0.5rem",
                                    border="1px solid #bfdbfe"
                                ),
                                # Argument Box
                                rx.box(
                                    rx.text("Argument:", font_weight="bold", **text_style(size="0.9rem", color="gray")),
                                    rx.text(argument_label, **text_style(color=style["color"], size="1.125rem")),
                                    bg=rx.cond(state.index % 2 == 0, style["background_color"], Theme.BACKGROUND_ALT),
                                    padding="1.5rem",
                                    border_radius="0.5rem",
                                    width="100%",
                                    margin_y="0.5rem",
                                    border=f"1px solid #e2e8f0"
                                ),
                                rx.cond(
                                    (state.phase == "rating1") | state.is_attention_check,
                                    rx.vstack(
                                        rx.text("How would you rate this argument?", **text_style(size="1.1rem")),
                                        rating_scale(
                                            value=rx.cond(state.is_attention_check, [state.attention_check_rating], [state.temp_rating]),
                                            on_change=state.set_temp_rating,
                                            show_label=state.show_rating_label,
                                            on_hover=state.set_show_rating_label,
                                            color_scheme=rx.cond(
                                                rx.cond(state.is_attention_check, state.attention_check_selected, state.rating_before_selected), 
                                                "indigo", 
                                                "gray"
                                            )
                                        ),
                                        rx.button(
                                            rx.cond(state.is_attention_check, "Confirm & Continue", "Confirm Rating"), 
                                            on_click=rx.cond(state.is_attention_check, state.submit_attention_check, state.submit_rating_before), 
                                            disabled=~rx.cond(state.is_attention_check, state.attention_check_selected, state.rating_before_selected),
                                            **primary_button_style()
                                        ),
                                        spacing="4",
                                        width="100%",
                                        align_items="start"
                                    )
                                ),
                                rx.cond(
                                    (state.phase == "chat") & ~state.is_attention_check,
                                    rx.vstack(
                                        rx.hstack(
                                            rx.text("Questioning Phase", **heading_style("sm")),
                                            rx.spacer(),
                                            # countdown_timer(end_time=state.timer_end, on_tick=state.tick),
                                            width="100%",
                                            align_items="center"
                                        ),
                                        
                                        rx.cond(
                                            (state.experimental_group == "experimental") & (state.index >= 6) & (state.index < 12),
                                            provided_questions_view(),
                                            chat_box()
                                        ),
                                        # THIS PIECE OF CODE SHOULD BE REMOVED BEFORE LAUNCHING
                                        # rx.divider(margin_y="0.5rem", border_color="red"),
                                        # rx.text("DEBUG: FULL CONTEXT", color="red", font_weight="bold", font_size="0.8rem"),
                                        # rx.text(state.current_context, color="red", font_size="0.8rem"),
                                        # THIS PIECE OF CODE SHOULD BE REMOVED BEFORE LAUNCHING
                                        rx.cond(
                                            state.discussion_error != "",
                                            rx.text(state.discussion_error, color="crimson", font_weight="bold", font_size="0.9rem")
                                        ),
                                        rx.button(
                                            "Finish Questioning", 
                                            on_click=ExperimentState.force_finish_chat,
                                            **primary_button_style(bg="gray")
                                        ),
                                        width="100%",
                                        spacing="4"
                                    )
                                ),
                                rx.cond(
                                    (state.phase == "rating2") & ~state.is_attention_check,
                                    rx.vstack(
                                        rx.text("Re-evaluate the argument after the discussion:", **text_style(size="1.1rem")),
                                        rating_scale(
                                            value=[state.temp_rating],
                                            on_change=state.set_temp_rating,
                                            show_label=state.show_rating_label,
                                            on_hover=state.set_show_rating_label,
                                            color_scheme=rx.cond(state.rating_after_selected, "indigo", "gray")
                                        ),
                                        rx.cond(
                                            state.influenced_answers_options_with_metadata.length() > 0,
                                            rx.vstack(
                                                rx.text("Indicate which answers have influenced your rating, if any:", **text_style(size="1.1rem")),
                                                rx.vstack(
                                                    rx.foreach(
                                                        state.influenced_answers_options_with_metadata,
                                                        lambda opt: rx.checkbox(
                                                            opt["text"],
                                                            on_change=lambda checked: state.toggle_influenced_answer(opt["source"], opt["index"]),
                                                            checked=state.influenced_answers.contains(opt["id"]),
                                                            color_scheme="indigo",
                                                        )
                                                    ),
                                                    align_items="start",
                                                    spacing="2",
                                                ),
                                                width="100%",
                                                align_items="start",
                                                padding_y="0.5rem",
                                            )
                                        ),
                                        rx.button(
                                            "Confirm & Continue", 
                                            on_click=state.submit_rating_after, 
                                            disabled=~state.rating_after_selected,
                                            **primary_button_style()
                                        ),
                                        spacing="4",
                                        width="100%",
                                        align_items="start"
                                    )
                                ),
                                spacing="4",
                                width="100%"
                            ),
                        ),
                        **card_style(),
                        width="100%",
                        # max_width="800px",  # Removed restriction to let it fill
                    ),
                    width="100%",
                    # max_width="800px", # Removed restriction
                ),
                align_items="start",
                width="100%",
                max_width="1600px", # Increased from 1200px
                spacing="4"
            ),
            width="100%",
            **container_style(max_width="100%")
        ),
        bg=style["background_color"],
        min_height="100vh",
        width="100%"
    )

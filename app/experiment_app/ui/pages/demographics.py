import reflex as rx
from ...state import ExperimentState
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style

def demographics_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.heading("Participant Information", 
                        **heading_style("xl"), 
                        align_items="center"
                    ),
                    rx.text(
                        "Please provide the following information to help us better understand our study participants. All data is anonymized.",
                        **text_style(size="1.125rem"),
                        align_items="center"
                    ),
                    rx.divider(margin_y="1rem"),
                    
                    rx.vstack(
                        # Age
                        rx.vstack(
                            rx.text("Age", font_weight="bold", **text_style()),
                            rx.input(
                                placeholder="Enter your age...",
                                on_change=ExperimentState.set_age,
                                width="100%",
                                color="black",
                                background_color="white",
                                class_name="age-input",
                                border_color="gray"
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),
                        
                        # Gender
                        rx.vstack(
                            rx.text("Gender", font_weight="bold", **text_style()),
                            rx.radio_group(
                                ["female", "male", "other", "do not want to say"],
                                on_change=ExperimentState.set_gender,
                                direction="row",
                                spacing="4",
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),
                        
                        # Education
                        rx.vstack(
                            rx.text("What is your highest level of education? If you are currently a student, please choose the level you are currently working towards.", font_weight="bold", **text_style()),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Select your highest level of education",
                                    class_name="select-trigger"
                                ),
                                rx.select.content(
                                    rx.select.item("No education", value="no_education"),
                                    rx.select.item("Primary School", value="primary_school"),
                                    rx.select.item("Secondary School (up to 16 years old)", value="secondary_school"),
                                    rx.select.item("Higher Secondary or Further Education", value="higher_secondary"),
                                    rx.select.item("University Degree or equivalent", value="university_degree"),
                                    rx.select.item("Master's Degree or equivalent", value="masters_degree"),
                                    rx.select.item("Doctorate", value="doctorate"),
                                    class_name="select-content"
                                ),
                                on_change=ExperimentState.set_education,
                                color="black",
                                width="100%"
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),
                        
                        # Language
                        # rx.vstack(
                        #     rx.text("Language Background", font_weight="bold", **text_style()),
                        #     rx.radio_group(
                        #         ["Native English", "Other"],
                        #         on_change=ExperimentState.set_native_english,
                        #         direction="row",
                        #         spacing="4",
                        #     ),
                        #     align_items="start",
                        #     width="100%",
                        #     spacing="2",
                        # ),
                        
                        # Logic Training
                        rx.vstack(
                            rx.text("Have you previously received any formal training in logic, argumentation, or critical thinking?", font_weight="bold", **text_style()),
                            rx.radio_group(
                                ["Yes", "No", "Not sure"],
                                on_change=ExperimentState.set_formal_training,
                                direction="row",
                                spacing="4",
                            ),
                            align_items="start",
                            width="100%",
                            spacing="2",
                        ),

                        rx.cond(
                            ExperimentState.formal_training == "Yes",
                            rx.vstack(
                                rx.text("What kind of training have you received? (e.g. a logics bachelor course, a PhD in argumentation, a critical thinking short course)", font_weight="bold", **text_style()),
                                rx.input(
                                    placeholder="Enter details...",
                                    on_change=ExperimentState.set_formal_training_details,
                                    width="100%",
                                    color="black",
                                    class_name="age-input",
                                    background_color="white"
                                ),
                                align_items="start",
                                width="100%",
                                spacing="2",
                            ),
                            rx.fragment(),
                        ),
                        
                        spacing="6",
                        width="100%",
                        padding_y="1rem"
                    ),
                    
                    rx.divider(margin_y="1.5rem"),
                    
                    rx.cond(
                        ExperimentState.demographics_error,
                        rx.text(
                            ExperimentState.demographics_error, 
                            color="red", 
                            font_weight="bold",
                            margin_bottom="1rem"
                        ),
                    ),
                    
                    rx.button(
                        "Next", 
                        on_click=ExperimentState.submit_demographics,
                        # is_disabled=~ExperimentState.demographics_filled,
                        **primary_button_style(),
                        width="100%"
                    ),
                    
                    # THIS SHOULD BE REMOVED BEFORE LAUNCHING
                    # rx.divider(margin_y="0.5rem", border_color="red"),
                    # rx.text("DEBUG CONTROLS", color="red", font_weight="bold", font_size="0.8rem"),
                    # rx.hstack(
                    #     rx.button(
                    #         "Skip Demographics",
                    #         on_click=ExperimentState.skip_demographics,
                    #         size="2",
                    #         color_scheme="red",
                    #         variant="outline"
                    #     ),
                    #     rx.button(
                    #         rx.text(f"Group: {ExperimentState.experimental_group}"),
                    #         on_click=ExperimentState.toggle_experimental_group,
                    #         size="2",
                    #         color_scheme="red",
                    #         variant="outline"
                    #     ),
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
        on_mount=[ExperimentState.init_session, ExperimentState.check_consent]
    )

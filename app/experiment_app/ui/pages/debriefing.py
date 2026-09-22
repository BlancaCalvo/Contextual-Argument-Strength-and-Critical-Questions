import reflex as rx
from ...state import ExperimentState
from ..style import Theme, style, container_style, card_style, heading_style, text_style, primary_button_style

def debriefing_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.heading("Participant Debriefing Information", 
                        **heading_style("xl"), 
                        align_items="center"
                    ),
                    rx.text(
                        "Thanks again for taking part in this research project! This final page allows you to learn a bit more about the study and share any feedback you may have.",
                        **text_style(),
                        #margin_bottom="1.5rem"
                    ),
                    
                    rx.divider(margin_y="1.5rem"),
                    
                    rx.vstack(
                        rx.heading("What is the purpose of this research?", size="4", margin_bottom="0.5rem"),
                        rx.text(
                            "The purpose of this experiment is to study the ability of participants to ask questions that are useful to challenge the strength of an argument. Therefore, we will be looking at how helpful were the questions you asked for your rating task.",
                            **text_style()
                        ),
                        rx.text(
                            "We will also look at how you improved your asking ability throughout the experiment, observing if you performed differently at the beginning and the end of the experiment. Finally, we will see if your ratings were more similar to other participants when you asked better questions.",
                            **text_style()
                        ),
                        rx.text(
                            "Get in touch to find out more about our research (bcalvofigueras001@dundee.ac.uk).",
                            **text_style(),
                            font_weight="bold"
                        ),
                        
                        rx.heading("How will we treat this data?", size="4", margin_top="1.5rem", margin_bottom="0.5rem"),
                        rx.text(
                            "As outlined in the “Participant Information Sheet”, your data and responses will be treated in the strictest confidence. After you click the ‘Finish’ button below, it will not be possible to withdraw from this study anymore. Your data will be saved anonymously and privately on our servers. Before the data gets published, a manual evaluation will be performed to ensure the data does not contain sensitive or identifiable information. Researchers are obliged to retain data for up to 10 years post-publication, however, anonymised data can be kept indefinitely. This is so the researcher can take part in open practice and other researchers can access the data to confirm the conclusions of published work. Similarly, consent forms are held for as long as the data is held.",
                            **text_style()
                        ),
                        
                        rx.heading("Do you have more questions?", size="4", margin_top="1.5rem", margin_bottom="0.5rem"),
                        rx.text(
                            "Please email us at bcalvofigueras001@dundee.ac.uk.",
                            **text_style()
                        ),
                        
                        rx.box(
                            rx.hstack(
                                rx.icon("info", size=20, color=Theme.PRIMARY),
                                rx.text(
                                    "Please click the \"Finish\" button below to end this experiment. Thanks again for your participation!",
                                    font_weight="bold",
                                    color=Theme.TEXT_PRIMARY,
                                ),
                                spacing="3",
                                align_items="center",
                            ),
                            bg=Theme.BACKGROUND_ALT,
                            padding="1rem",
                            border_radius="0.5rem",
                            border=f"1px solid {Theme.BORDER}",
                            margin_top="1.5rem",
                            width="100%"
                        ),
                        
                        spacing="4",
                        align_items="start",
                        width="100%",
                        padding_y="1rem"
                    ),
                    
                    rx.divider(margin_y="1.5rem"),
                    
                    rx.button(
                        "Finish", 
                        on_click=ExperimentState.submit_debriefing,
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

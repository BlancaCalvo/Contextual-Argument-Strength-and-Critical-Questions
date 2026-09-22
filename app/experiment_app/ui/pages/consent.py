import reflex as rx
from ...state import ExperimentState
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style

def consent_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.heading("Consent Declaration", 
                        **heading_style("xl"), 
                        align_items="center"
                    ),
                    rx.divider(margin_y="1.5rem"),
                    rx.text(
                        "By continuing forward from this page, you acknowledge your understanding of the following:",
                        **text_style(size="1.125rem"),
                        align_items="center"
                    ),
                    
                    rx.vstack(
                        rx.hstack(
                            rx.icon("dot", size=20, color=style["color"]),
                            rx.text("I agree to participate in this study.", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.icon("dot", size=20, color=style["color"]),
                            rx.text("I may withdraw from this study at any time (simply close the browser).", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.icon("dot", size=20, color=style["color"]),
                            rx.text("I understand that, due to anonymisation, once the study is completed (once you click the “Finish” button at the end of the study), data will not be able to be withdrawn.", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.icon("dot", size=20, color=style["color"]),
                            rx.text("I agree for the data provided by my participation to be used as part of this study (providing confidentiality guidelines are followed).", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.icon("dot", size=20, color=style["color"]),
                            rx.text("I am 18 years old or older.", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.icon("dot", size=20, color=style["color"]),
                            rx.text("I do not have any language disorder.", **text_style()),
                            align_items="center",
                            spacing="3",
                        ),
                        align_items="start",
                        spacing="3",
                        width="100%",
                        padding_y="1rem"
                    ),
                    #rx.divider(margin_y="1.5rem"),
                    rx.vstack(
                        rx.text("If you consent, please tick the box below:", font_weight="bold", **text_style()),
                        rx.checkbox(
                            "I consent to take part in this study.",
                            on_change=ExperimentState.set_consent_accepted,
                            size="3",
                        ),
                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    rx.text(
                        "If you don’t consent, please simply close your browser to terminate this session. Thank you very much for your time. If you have any other questions about the consent, please email bcalvofigueras001@dundee.ac.uk.",
                        **text_style(),
                        margin_top="1rem",
                    ),
                    rx.divider(margin_y="1.5rem"),
                    rx.cond(
                        ExperimentState.consent_error,
                        rx.text(
                            ExperimentState.consent_error,
                            color="red",
                            font_weight="bold",
                            margin_bottom="1rem"
                        ),
                    ),
                    rx.button(
                        "Next",
                        on_click=ExperimentState.submit_consent,
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
        on_mount=[ExperimentState.capture_url_params, ExperimentState.init_session]
    )

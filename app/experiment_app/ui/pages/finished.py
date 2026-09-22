import reflex as rx
from ..style import style, container_style, card_style, heading_style, text_style, primary_button_style
from ...state import ExperimentState

def finished_page():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.heading("Thank You!", **heading_style("xl")),
                    rx.text(
                        "You have completed the experiment.",
                        **text_style(size="1.125rem")
                    ),
                    rx.text(
                        "Your responses have been recorded successfully.",
                        **text_style()
                    ),
                    rx.divider(margin_y="2rem"),
                    rx.text(
                        "You may now close this window.",
                        **text_style(color=style["color"])
                    ),
                    rx.button(
                        "Exit",
                        on_click=lambda: rx.window_alert("You can now close this tab."),
                        **primary_button_style()
                    ),
                    spacing="4",
                    align_items="center",
                    text_align="center",
                    width="100%"
                ),
                **card_style(),
                width="100%",
                max_width="600px",
            ),
            **container_style()
        ),
        height="100vh",
        justify="center",
        align="center",
        on_mount=ExperimentState.finish_session
    )

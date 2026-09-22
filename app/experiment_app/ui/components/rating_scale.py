import reflex as rx
from ..style import text_style, style

def rating_scale(value, on_change, show_label, on_hover, color_scheme="indigo"):
    return rx.vstack(
        rx.hstack(
            rx.text("1: Not supported", **text_style(size="0.875rem")),
            rx.spacer(),
            rx.text("2: Weak", **text_style(size="0.875rem")),
            rx.spacer(),
            rx.text("3: Reasonable", **text_style(size="0.875rem")),
            rx.spacer(),
            rx.text("4: Strong", **text_style(size="0.875rem")),
            width="100%"
        ),
        rx.box(
            rx.cond(
                show_label,
                rx.badge(
                    value[0].to_string(),
                    variant="solid",
                    color_scheme=color_scheme,
                    position="absolute",
                    top="-2.5rem",
                    left="50%",
                    transform="translateX(-50%)",
                    font_size="1rem",
                    padding_x="0.75rem",
                    border_radius="full",
                    z_index="10",
                    transition="all 0.1s"
                )
            ),
            rx.slider(
                min=1, 
                max=4, 
                step=0.5, 
                value=value,
                on_change=on_change,
                on_mouse_enter=on_hover(True),
                on_mouse_leave=on_hover(False),
                width="100%",
                color_scheme=color_scheme,
                cursor="pointer"
            ),
            position="relative",
            width="100%",
            padding_top="1.5rem"
        ),
        rx.hstack(
            rx.foreach(
                [1, 2, 3, 4],
                lambda i: rx.text(f"{i}", **text_style(size="0.75rem", color=style["color"]))
            ),
            justify="between",
            width="100%",
            padding_x="10px"
        ),
        spacing="2",
        width="100%",
        bg=style["background_color"],
        padding="1rem",
        border_radius="0.5rem"
    )

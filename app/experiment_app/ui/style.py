import reflex as rx

# Theme Colors
class Theme:
    PRIMARY = "#6366f1"       # Indigo 500
    PRIMARY_HOVER = "#4f46e5" # Indigo 600
    BACKGROUND = "#f8fafc"    # Slate 50
    SURFACE = "#ffffff"       # White
    TEXT_PRIMARY = "#1e293b"  # Slate 800
    TEXT_SECONDARY = "#64748b"# Slate 500
    BORDER = "#e2e8f0"        # Slate 200
    SUCCESS = "#10b981"       # Emerald 500
    ERROR = "#ef4444"         # Red 500
    BACKGROUND_ALT = "#fffbeb" # Amber 50
    SITUATION_BLUE = "#f0f9ff"
    SITUATION_PURPLE = "#f5f3ff"

# Common Styles
style = {
    "font_family": "Inter, system-ui, sans-serif",
    "background_color": Theme.BACKGROUND,
    "color": Theme.TEXT_PRIMARY,
}

# Component Styles

def container_style(max_width="800px"):
    return {
        "max_width": max_width,
        "padding": "2rem",
        "margin": "0 auto",
        "min_height": "100vh",
        "display": "flex",
        "flex_direction": "column",
        "justify_content": "center",
    }

def card_style():
    return {
        "bg": Theme.SURFACE,
        "padding": "2rem",
        "border_radius": "1rem",
        "box_shadow": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        "border": f"1px solid {Theme.BORDER}",
    }

def heading_style(size="lg"):
    sizes = {
        "sm": "1.25rem",
        "md": "1.5rem",
        "lg": "2.25rem",
        "xl": "3rem",
    }
    return {
        "font_weight": "700",
        "letter_spacing": "-0.025em",
        "color": Theme.TEXT_PRIMARY,
        "font_size": sizes.get(size, "2.25rem"),
        "margin_bottom": "1rem",
    }

def text_style(color=Theme.TEXT_SECONDARY, size="1rem"):
    return {
        "color": color,
        "font_size": size,
        "line_height": "1.6",
    }

def primary_button_style(bg=Theme.PRIMARY):
    return {
        "bg": bg,
        "color": "white",
        "padding": "0.75rem 1.5rem",
        "border_radius": "0.5rem",
        "font_weight": "600",
        "_hover": {"bg": Theme.PRIMARY_HOVER if bg == Theme.PRIMARY else "darkgray"}, # Simple logic
        "cursor": "pointer",
        "transition": "all 0.2s",
    }

def secondary_button_style():
    return {
        "bg": "transparent",
        "color": Theme.TEXT_PRIMARY,
        "padding": "0.75rem 1.5rem",
        "border_radius": "0.5rem",
        "font_weight": "600",
        "border": f"1px solid {Theme.BORDER}",
        "_hover": {"bg": Theme.BACKGROUND},
        "cursor": "pointer",
        "transition": "all 0.2s",
        "transition": "all 0.2s",
    }

def situation_color(s_id: str):
    """Returns a pastel background color based on situation ID."""
    # Simple consistent mapping using modulo or predefined list
    colors = [
        "#f0f9ff", # Sky 50
        "#fdf2f8", # Pink 50
        "#f0fdf4", # Green 50
        "#fff7ed", # Orange 50
        "#f5f3ff", # Violet 50
        "#fff1f2", # Rose 50
        "#ecfeff", # Cyan 50
        "#f0fdfa", # Teal 50
    ]
    try:
        idx = int(s_id) % len(colors)
        return colors[idx]
    except:
        return colors[0]

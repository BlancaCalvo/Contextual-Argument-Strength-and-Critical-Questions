import reflex as rx
from .state import ExperimentState

# Import your pages
from .ui.pages.instructions import instructions_page
from .ui.pages.consent import consent_page
from .ui.pages.demographics import demographics_page
from .ui.pages.mid_instructions import mid_instructions_page
from .ui.pages.argument_page import argument_page
from .ui.pages.finished import finished_page
from .ui.pages.last_questions import last_questions_page
from .ui.pages.debriefing import debriefing_page
from .ui.pages.example_page import example_page
from .state import ExperimentState

# Create the Reflex app with your custom state
app = rx.App(
    theme = rx.theme(
        appearance="light",
        has_background=True,
    ),
    stylesheets=["/custom.css"],
    style={
        "background_color": "white",
        "color": "black"
    }
)

# Register your pages with routes
app.add_page(consent_page, route="/")
app.add_page(demographics_page, route="/demographics")
app.add_page(instructions_page, route="/instructions")
app.add_page(mid_instructions_page, route="/mid-instructions")
app.add_page(argument_page, route="/argument")
app.add_page(last_questions_page, route="/last-questions")
app.add_page(debriefing_page, route="/debriefing")
app.add_page(example_page, route="/example")
app.add_page(finished_page, route="/finished")

# Compile the app so Reflex knows your pages

# Compile the app so Reflex knows your pages
app._compile()

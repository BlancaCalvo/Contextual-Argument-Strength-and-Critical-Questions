import reflex as rx

def countdown_timer(end_time, on_tick):
    return rx.moment(interval=1000, on_change=on_tick, display="none")

import reflex as rx 

@rx.page()
def index():
    return rx.center(rx.heading("Hello Reflex! 👋"))

app = rx.App()
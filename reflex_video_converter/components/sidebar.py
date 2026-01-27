import reflex as rx


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.icon("video", class_name="w-8 h-8 text-white"),
                class_name="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg",
            ),
            rx.el.h1(
                "Video to MP4",
                class_name="text-xl font-bold text-gray-900 tracking-tight",
            ),
            class_name="flex items-center gap-3 px-6 py-8",
        ),
        rx.el.div(
            rx.el.p(
                "Simple video conversion",
                class_name="text-sm text-gray-500 px-6",
            ),
            class_name="flex-1",
        ),
        class_name="hidden md:flex flex-col w-72 h-screen bg-white border-r border-gray-100 fixed left-0 top-0 z-20",
    )
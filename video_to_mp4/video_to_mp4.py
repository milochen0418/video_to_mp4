import reflex as rx
from video_to_mp4.components.upload_zone import upload_zone
from video_to_mp4.components.job_list import job_list


def index() -> rx.Component:
    return rx.el.div(
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("video", class_name="w-7 h-7 text-white"),
                        class_name="w-11 h-11 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg",
                    ),
                    rx.el.h1(
                        "Video to MP4",
                        class_name="text-2xl font-bold text-gray-900 tracking-tight",
                    ),
                    class_name="flex items-center gap-3 mb-8",
                ),
                rx.el.div(
                    upload_zone(),
                    rx.el.div(class_name="h-6"),
                    job_list(),
                    class_name="flex flex-col pb-12",
                ),
                class_name="max-w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6",
            ),
            class_name="min-h-screen bg-gray-50/50",
        ),
        rx.toast.provider(),
        class_name="font-['Inter'] min-h-screen bg-gray-50",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ],
)
app.add_page(index, route="/")
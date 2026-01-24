import reflex as rx
from reflex_video_converter.components.sidebar import sidebar
from reflex_video_converter.components.upload_zone import upload_zone
from reflex_video_converter.components.capacity_indicator import capacity_card
from reflex_video_converter.components.job_list import job_list


def index() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("video", class_name="w-6 h-6 text-indigo-600"),
                        rx.el.h1(
                            "VidConvert",
                            class_name="text-lg font-bold text-gray-900 ml-2",
                        ),
                        class_name="flex items-center",
                    ),
                    rx.icon("menu", class_name="w-6 h-6 text-gray-500"),
                    class_name="md:hidden flex justify-between items-center p-4 bg-white border-b border-gray-100 mb-6",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h1(
                            "Dashboard", class_name="text-2xl font-bold text-gray-900"
                        ),
                        rx.el.p(
                            "Manage your video conversions and files.",
                            class_name="text-gray-500 mt-1",
                        ),
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("bell", class_name="w-5 h-5"),
                            class_name="w-10 h-10 rounded-full bg-white border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50 transition-colors relative",
                        ),
                        class_name="flex gap-3",
                    ),
                    class_name="flex justify-between items-start mb-8 px-4 sm:px-0",
                ),
                rx.el.div(
                    rx.el.div(
                        upload_zone(),
                        rx.el.div(class_name="h-6"),
                        job_list(),
                        class_name="lg:col-span-2 flex flex-col",
                    ),
                    rx.el.div(
                        capacity_card(),
                        rx.el.div(
                            rx.el.h3(
                                "Quick Tips",
                                class_name="font-semibold text-gray-900 mb-3",
                            ),
                            rx.el.ul(
                                rx.el.li(
                                    "• MP4 is best for web compatibility",
                                    class_name="text-sm text-gray-600 mb-2",
                                ),
                                rx.el.li(
                                    "• Keep uploads under 5GB for speed",
                                    class_name="text-sm text-gray-600 mb-2",
                                ),
                                rx.el.li(
                                    "• Use WiFi for large transfers",
                                    class_name="text-sm text-gray-600",
                                ),
                                class_name="pl-2",
                            ),
                            class_name="bg-indigo-50/50 p-6 rounded-2xl border border-indigo-100 mt-6",
                        ),
                        class_name="lg:col-span-1",
                    ),
                    class_name="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8 px-4 sm:px-0 pb-12",
                ),
                class_name="max-w-6xl mx-auto pt-4 md:pt-8",
            ),
            class_name="md:ml-72 min-h-screen bg-gray-50/50",
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
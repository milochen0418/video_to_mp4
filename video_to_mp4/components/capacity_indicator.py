import reflex as rx
from video_to_mp4.states.app_state import AppState


def capacity_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("hard-drive", class_name="w-5 h-5 text-indigo-600"),
                rx.el.h3("Storage Capacity", class_name="font-semibold text-gray-900"),
                class_name="flex items-center gap-2 mb-4",
            ),
            rx.el.div(
                rx.el.span(
                    f"{AppState.used_capacity_gb:.1f} GB",
                    class_name="text-2xl font-bold text-gray-900",
                ),
                rx.el.span(
                    f" / {AppState.MAX_CAPACITY_GB:.0f} GB",
                    class_name="text-sm font-medium text-gray-500 ml-1",
                ),
                class_name="flex items-baseline mb-2",
            ),
            rx.el.div(
                rx.el.div(
                    class_name=rx.cond(
                        AppState.is_uploading,
                        f"h-full rounded-full {AppState.usage_color} transition-all duration-1000 animate-pulse",
                        f"h-full rounded-full {AppState.usage_color} transition-all duration-500",
                    ),
                    style={"width": f"{AppState.usage_percentage}%"},
                ),
                class_name="w-full h-3 bg-gray-100 rounded-full overflow-hidden mb-3",
            ),
            rx.el.div(
                rx.el.p(
                    f"{AppState.remaining_capacity_gb:.1f} GB Remaining",
                    class_name="text-xs font-medium text-gray-500",
                ),
                rx.cond(
                    AppState.usage_percentage > 90,
                    rx.el.span(
                        "Near Limit",
                        class_name="text-xs font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded-full",
                    ),
                    rx.el.span(
                        "Healthy",
                        class_name="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full",
                    ),
                ),
                class_name="flex justify-between items-center",
            ),
            class_name="bg-white p-6 rounded-2xl shadow-sm border border-gray-100",
        ),
        class_name="w-full",
    )
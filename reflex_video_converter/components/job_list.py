import reflex as rx
from reflex_video_converter.states.app_state import AppState, FileJob


def status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        (
            "Complete",
            rx.el.span(
                "Complete",
                class_name="px-2 py-1 rounded-md bg-green-50 text-green-700 text-xs font-bold",
            ),
        ),
        (
            "Processing",
            rx.el.span(
                "Processing",
                class_name="px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-bold animate-pulse",
            ),
        ),
        (
            "Queued",
            rx.el.span(
                "Queued",
                class_name="px-2 py-1 rounded-md bg-gray-100 text-gray-600 text-xs font-bold",
            ),
        ),
        (
            "Error",
            rx.el.span(
                "Error",
                class_name="px-2 py-1 rounded-md bg-red-50 text-red-700 text-xs font-bold",
            ),
        ),
        rx.el.span(
            "Unknown",
            class_name="px-2 py-1 rounded-md bg-gray-50 text-gray-500 text-xs font-bold",
        ),
    )


def job_row(job: FileJob) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.icon("file-video", class_name="w-8 h-8 text-indigo-200 mr-3"),
                rx.el.div(
                    rx.el.p(
                        job["filename"],
                        class_name="text-sm font-semibold text-gray-900",
                    ),
                    rx.el.div(
                        rx.el.span(job["size_str"], class_name="mr-1"),
                        rx.cond(
                            job["converted_size_str"],
                            rx.el.span(
                                "→ " + job["converted_size_str"],
                                class_name="text-green-600 font-medium mr-2",
                            ),
                            None,
                        ),
                        rx.el.span(
                            f" • {job['resolution']} • {job['quality']}",
                            class_name="text-indigo-500 font-medium ml-1",
                        ),
                        class_name="text-xs text-gray-500 flex items-center",
                    ),
                    rx.cond(
                        job["error_message"],
                        rx.el.p(
                            job["error_message"],
                            class_name="text-xs text-red-500 mt-1 max-w-xs truncate",
                        ),
                        None,
                    ),
                    class_name="flex flex-col",
                ),
                class_name="flex items-center",
            ),
            class_name="px-4 py-4 whitespace-nowrap",
        ),
        rx.el.td(status_badge(job["status"]), class_name="px-4 py-4 whitespace-nowrap"),
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    class_name="h-1.5 rounded-full bg-indigo-600 transition-all duration-500",
                    style={"width": f"{job['progress']}%"},
                ),
                class_name="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden",
            ),
            class_name="px-4 py-4 whitespace-nowrap",
        ),
        rx.el.td(
            job["uploaded_at"],
            class_name="px-4 py-4 whitespace-nowrap text-sm text-gray-500",
        ),
        rx.el.td(
            rx.match(
                job["status"],
                (
                    "Complete",
                    rx.el.div(
                        rx.el.a(
                            rx.icon("download", class_name="w-4 h-4 text-indigo-600"),
                            href=rx.get_upload_url(job["converted_filename"]),
                            download=job["converted_filename"],
                            class_name="p-2 hover:bg-indigo-50 rounded-lg transition-colors border border-transparent hover:border-indigo-100 block",
                            title="Download",
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="w-4 h-4 text-red-400"),
                            on_click=lambda: AppState.remove_job(job["id"]),
                            class_name="p-2 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100",
                            title="Delete",
                        ),
                        class_name="flex gap-1 justify-end items-center",
                    ),
                ),
                (
                    "Error",
                    rx.el.div(
                        rx.el.button(
                            rx.icon("refresh-cw", class_name="w-4 h-4 text-orange-500"),
                            on_click=lambda: AppState.retry_job(job["id"]),
                            class_name="p-2 hover:bg-orange-50 rounded-lg transition-colors border border-transparent hover:border-orange-100",
                            title="Retry",
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="w-4 h-4 text-red-400"),
                            on_click=lambda: AppState.remove_job(job["id"]),
                            class_name="p-2 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100",
                            title="Delete",
                        ),
                        class_name="flex gap-1 justify-end",
                    ),
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("trash-2", class_name="w-4 h-4 text-gray-400"),
                        on_click=lambda: AppState.remove_job(job["id"]),
                        class_name="p-2 hover:bg-gray-100 rounded-lg transition-colors",
                        title="Cancel",
                    ),
                    class_name="flex justify-end",
                ),
            ),
            class_name="px-4 py-4 whitespace-nowrap text-right",
        ),
        class_name="hover:bg-gray-50/50 transition-colors border-b border-gray-50 last:border-0",
    )


def job_list() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3("Recent Activity", class_name="text-lg font-bold text-gray-900"),
            rx.el.button(
                "Clear All",
                class_name="text-sm font-semibold text-gray-400 hover:text-gray-600",
            ),
            class_name="flex justify-between items-center mb-6",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th(
                            "File Name & Settings",
                            class_name="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider",
                        ),
                        rx.el.th(
                            "Status",
                            class_name="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider",
                        ),
                        rx.el.th(
                            "Progress",
                            class_name="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider",
                        ),
                        rx.el.th(
                            "Uploaded",
                            class_name="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider",
                        ),
                        rx.el.th(
                            "Actions",
                            class_name="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider",
                        ),
                    )
                ),
                rx.el.tbody(rx.foreach(AppState.recent_jobs, job_row)),
                class_name="w-full",
            ),
            class_name="overflow-x-auto",
        ),
        class_name="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-100",
    )
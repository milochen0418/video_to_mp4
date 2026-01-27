import reflex as rx
from video_to_mp4.states.app_state import AppState


def settings_panel() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AppState.show_resolution_help | AppState.show_quality_help,
            rx.el.div(
                on_click=AppState.close_help,
                class_name="fixed inset-0 z-0",
            ),
            rx.el.span(),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Resolution",
                    class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("circle_help", class_name="w-4 h-4"),
                        on_click=AppState.toggle_resolution_help,
                        class_name="ml-2 text-gray-400 hover:text-gray-600 transition-colors",
                        aria_label="Resolution help",
                        type="button",
                    ),
                    rx.cond(
                        AppState.show_resolution_help,
                        rx.el.div(
                            "Resolution controls output dimensions. 'Original' keeps the source size; 4K/1080p/720p/480p scale the video.",
                            class_name="absolute right-0 mt-2 w-64 text-xs text-gray-700 bg-white border border-gray-200 rounded-lg shadow-lg p-3 z-20",
                        ),
                        rx.el.span(),
                    ),
                    class_name="relative",
                ),
                class_name="flex items-center mb-2",
            ),
            rx.el.div(
                rx.foreach(
                    AppState.resolution_options,
                    lambda res: rx.el.button(
                        res,
                        on_click=lambda: AppState.set_resolution(res),
                        class_name=rx.cond(
                            AppState.selected_resolution == res,
                            "px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white transition-all shadow-sm",
                            "px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all",
                        ),
                    ),
                ),
                class_name="flex flex-wrap gap-2",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Quality Preset",
                    class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("circle_help", class_name="w-4 h-4"),
                        on_click=AppState.toggle_quality_help,
                        class_name="ml-2 text-gray-400 hover:text-gray-600 transition-colors",
                        aria_label="Quality preset help",
                        type="button",
                    ),
                    rx.cond(
                        AppState.show_quality_help,
                        rx.el.div(
                            "Quality presets control compression: Standard (faster, smaller), High (balanced), Maximum (best quality, slowest).",
                            class_name="absolute right-0 mt-2 w-64 text-xs text-gray-700 bg-white border border-gray-200 rounded-lg shadow-lg p-3 z-20",
                        ),
                        rx.el.span(),
                    ),
                    class_name="relative",
                ),
                class_name="flex items-center mb-2",
            ),
            rx.el.div(
                rx.foreach(
                    AppState.quality_options,
                    lambda q: rx.el.button(
                        q,
                        on_click=lambda: AppState.set_quality(q),
                        class_name=rx.cond(
                            AppState.selected_quality == q,
                            "px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white transition-all shadow-sm",
                            "px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all",
                        ),
                    ),
                ),
                class_name="flex flex-wrap gap-2",
            ),
        ),
        class_name="bg-gray-50/50 rounded-xl p-4 border border-gray-100",
    )


def upload_zone() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AppState.show_confirm_dialog,
            rx.el.div(
                rx.el.div(
                    on_click=AppState.close_confirm,
                    class_name="fixed inset-0 bg-black/40 z-40",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            "Confirm conversion",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        rx.el.p(
                            "You are about to convert the following file(s) to MP4:",
                            class_name="text-sm text-gray-600 mt-1",
                        ),
                        rx.el.ul(
                            rx.foreach(
                                AppState.pending_files,
                                lambda name: rx.el.li(
                                    name,
                                    class_name="text-sm text-gray-700",
                                ),
                            ),
                            class_name="mt-3 max-h-40 overflow-y-auto space-y-1 border border-gray-100 rounded-lg p-3 bg-gray-50",
                        ),
                        rx.el.div(
                            rx.el.div(
                                rx.el.span(
                                    "Resolution:",
                                    class_name="text-xs uppercase tracking-wider text-gray-500",
                                ),
                                rx.el.span(
                                    AppState.selected_resolution,
                                    class_name="text-sm font-medium text-gray-900",
                                ),
                                class_name="flex justify-between",
                            ),
                            rx.el.div(
                                rx.el.span(
                                    "Quality:",
                                    class_name="text-xs uppercase tracking-wider text-gray-500",
                                ),
                                rx.el.span(
                                    AppState.selected_quality,
                                    class_name="text-sm font-medium text-gray-900",
                                ),
                                class_name="flex justify-between mt-2",
                            ),
                            rx.el.div(
                                rx.el.span(
                                    "Output:",
                                    class_name="text-xs uppercase tracking-wider text-gray-500",
                                ),
                                rx.el.span(
                                    "MP4",
                                    class_name="text-sm font-medium text-gray-900",
                                ),
                                class_name="flex justify-between mt-2",
                            ),
                            class_name="mt-4",
                        ),
                        rx.el.div(
                            rx.el.button(
                                "Cancel",
                                on_click=AppState.close_confirm,
                                class_name="px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50",
                            ),
                            rx.el.button(
                                "Confirm & Convert",
                                on_click=AppState.confirm_upload,
                                class_name="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700",
                            ),
                            class_name="mt-6 flex justify-end gap-3",
                        ),
                        class_name="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 w-full max-w-lg",
                    ),
                    class_name="fixed inset-0 z-50 flex items-center justify-center p-4",
                ),
            ),
            rx.el.span(),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Upload Video", class_name="text-lg font-bold text-gray-900"
                    ),
                    rx.el.p(
                        "Convert videos to MP4",
                        class_name="text-sm text-gray-500",
                    ),
                ),
                class_name="mb-6",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Input",
                        class_name="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3",
                    ),
                    rx.upload.root(
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "cloud-upload",
                                    class_name="w-10 h-10 text-indigo-500 mb-4",
                                ),
                                rx.el.p(
                                    "Drag & drop video files here",
                                    class_name="text-lg font-semibold text-gray-900 mb-1",
                                ),
                                rx.el.p(
                                    "or click to browse files",
                                    class_name="text-sm text-gray-500 mb-6",
                                ),
                                rx.el.div(
                                    rx.el.span(
                                        "Supported: AVI, MOV, MKV, WMV, WEBM",
                                        class_name="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-medium",
                                    ),
                                    class_name="flex justify-center",
                                ),
                                class_name="flex flex-col items-center justify-center text-center z-10 relative",
                            ),
                            class_name="border-2 border-dashed border-indigo-200 bg-indigo-50/30 hover:bg-indigo-50/50 rounded-2xl p-10 transition-all duration-300 cursor-pointer group hover:border-indigo-400 w-full",
                        ),
                        id="upload_box",
                        border="0px",
                        padding="0px",
                        accept={
                            "video/*": [
                                ".avi",
                                ".mov",
                                ".mkv",
                                ".wmv",
                                ".mp4",
                                ".webm",
                            ]
                        },
                        multiple=True,
                        class_name="w-full",
                    ),
                    class_name="bg-white rounded-2xl border border-gray-100 p-5",
                ),
                rx.el.div(
                    rx.el.h3(
                        "Output",
                        class_name="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3",
                    ),
                    settings_panel(),
                    rx.el.p(
                        "Output format: MP4",
                        class_name="text-xs text-gray-500 mt-3",
                    ),
                    class_name="bg-white rounded-2xl border border-gray-100 p-5",
                ),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-6",
            ),
            rx.el.div(
                rx.cond(
                    AppState.is_uploading,
                    rx.el.button(
                        rx.el.div(
                            rx.spinner(size="2"),
                            rx.el.span("Processing...", class_name="ml-2"),
                            class_name="flex items-center",
                        ),
                        disabled=True,
                        class_name="w-full py-3 bg-gray-100 text-gray-400 font-semibold rounded-xl cursor-not-allowed flex justify-center items-center",
                    ),
                    rx.el.button(
                        "Convert to MP4",
                        on_click=AppState.open_confirm(rx.upload_files("upload_box")),
                        class_name="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-lg shadow-indigo-200 transition-all duration-200 transform hover:-translate-y-0.5",
                    ),
                ),
                class_name="mt-6",
            ),
            class_name="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-100 h-full flex flex-col",
        ),
        class_name="w-full",
    )
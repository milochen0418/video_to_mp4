import reflex as rx


def sidebar_item(text: str, icon: str, active: bool = False) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name=f"w-5 h-5 mr-3 {rx.cond(active, 'text-indigo-600', 'text-gray-500')}",
        ),
        rx.el.span(
            text,
            class_name=f"font-medium {rx.cond(active, 'text-indigo-900', 'text-gray-600')}",
        ),
        class_name=f"\n            flex items-center px-4 py-3 rounded-xl cursor-pointer transition-all duration-200\n            {rx.cond(active, 'bg-indigo-50 shadow-sm border border-indigo-100', 'hover:bg-gray-50')}\n        ",
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.icon("video", class_name="w-8 h-8 text-white"),
                class_name="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg",
            ),
            rx.el.h1(
                "VidConvert",
                class_name="text-xl font-bold text-gray-900 tracking-tight",
            ),
            class_name="flex items-center gap-3 px-6 py-8",
        ),
        rx.el.nav(
            rx.el.div(
                rx.el.p(
                    "MENU",
                    class_name="px-4 text-xs font-bold text-gray-400 mb-2 tracking-wider",
                ),
                rx.el.div(
                    sidebar_item("Dashboard", "layout-dashboard", active=True),
                    sidebar_item("My Files", "folder"),
                    sidebar_item("Analytics", "bar-chart-2"),
                    class_name="space-y-1",
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                rx.el.p(
                    "SETTINGS",
                    class_name="px-4 text-xs font-bold text-gray-400 mb-2 tracking-wider",
                ),
                rx.el.div(
                    sidebar_item("Preferences", "settings"),
                    sidebar_item("Billing", "credit-card"),
                    class_name="space-y-1",
                ),
            ),
            class_name="flex-1 px-4 overflow-y-auto",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("user", class_name="w-5 h-5 text-indigo-600"),
                    class_name="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center border-2 border-white shadow-sm",
                ),
                rx.el.div(
                    rx.el.p("Pro User", class_name="text-sm font-bold text-gray-900"),
                    rx.el.p("Free Plan", class_name="text-xs text-gray-500"),
                    class_name="flex flex-col",
                ),
                class_name="flex items-center gap-3",
            ),
            class_name="p-4 border-t border-gray-100 bg-gray-50/50",
        ),
        class_name="hidden md:flex flex-col w-72 h-screen bg-white border-r border-gray-100 fixed left-0 top-0 z-20",
    )
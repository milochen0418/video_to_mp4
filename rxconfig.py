import reflex as rx

config = rx.Config(
	app_name="video_to_mp4",
	plugins=[rx.plugins.TailwindV3Plugin()],
	disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)

from .simple_tags import StandaloneTag


class Static(StandaloneTag):
    tags = {"static"}

    def __init__(self, environment):
        super().__init__(environment)
        # environment.extend(vite_metadata_prefix="", vite_metadata=None)
        environment.extend(staticfiles_prefix="", staticfiles=None)

    def render(self, static_file):
        # static_dir = self.environment.staticfiles[static_key]
        static_dir = self.environment.staticfiles["public"]["uripath"]
        return f"{static_dir}{static_file}"

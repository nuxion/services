from typing import Dict, Optional
from urllib.parse import urljoin

from jinja2 import Environment
from jinja2.utils import markupsafe

from .simple_tags import StandaloneTag

scripts_attrs = {"type": "module", "async": "", "defer": ""}


def generate_script_tag(
    src: str, attrs: Optional[Dict[str, str]] = None
) -> str:
    """Generates an HTML script tag."""
    attrs_str: str = ""
    if attrs is not None:
        for key, value in attrs.items():
            if value:
                attrs_str += f"{key}={value} "
            else:
                attrs_str += f"{key} "

    return f'<script {attrs_str.strip()} src="{src}"></script>'


def generate_stylesheet_tag(href: str) -> str:
    """
    Generates and HTML <link> stylesheet tag for CSS.
    Arguments:
        href {str} -- CSS file URL.
    Returns:
        str -- CSS link tag.
    """
    return '\t<link rel="stylesheet" href="{href}" />'.format(href=href)


def generate_react_hmr():
    return f"""
        <script type="module">
        import RefreshRuntime from '{cls.generate_vite_server_url()}@react-refresh'
        RefreshRuntime.injectIntoGlobalHook(window)
        window.$RefreshReg$ = () => {{}}
        window.$RefreshSig$ = () => (type) => type
        window.__vite_plugin_react_preamble_installed__=true
        </script>
                """


class ViteDev(StandaloneTag):
    tags = {"vite_dev"}

    def __init__(self, environment):
        super().__init__(environment)
        # environment.extend(vite_metadata_prefix="", vite_metadata=None)
        environment.extend(vite_dev_mod_prefix="", vite_dev_mode=None)
        environment.extend(vite_dev_server_prefix="", vite_dev_server=None)

    @staticmethod
    def generate_vite_server_url(vite_dev_srv: str, path: Optional[str] = None):
        return urljoin(
            vite_dev_srv, path if path is not None else "")

    def render(self, script_name="main.js"):
        _url = f"{self.environment.vite_dev_server}/{script_name}"
        tags = []
        if self.environment.vite_dev_mode:
            tag = generate_script_tag(_url, {"type": "module"})
            tags.append(tag)
        if self.environment.vite_react_mode:
            tag = generate_react_hmr()
            tags.append(tag)
        return markupsafe.Markup("\n".join(tags))


class ViteAsset(StandaloneTag):
    tags = {"vite_asset"}

    def __init__(self, environment):
        super().__init__(environment)
        # environment.extend(vite_metadata_prefix="", vite_metadata=None)
        environment.extend(vite_manifest_prefix="", vite_manifest=None)
        environment.extend(vite_dev_mod_prefix="", vite_dev_mode=None)

    def render(self, asset_name="main.js"):
        if not self.environment.vite_dev_mode:
            m = self.environment.vite_manifest[asset_name]
            tags = []
            asset = m["file"]
            tag = generate_script_tag(asset, attrs=scripts_attrs)
            tags.append(tag)
            if m.get("css"):
                for css in m.get("css"):
                    tags.append(
                        generate_stylesheet_tag(css)
                    )

            return markupsafe.Markup("\n".join(tags))
        return markupsafe.Markup()

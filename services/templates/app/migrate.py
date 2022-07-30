from services.base import MigrationSpec


class Migrate(MigrationSpec):
    package_dir = "{{ data.app_name }}"
    version_table = "{{ data.app_name }}_version"

import importlib
from typing import Optional

from alembic import command
from alembic.config import Config as AlembicConfig
from services.utils import get_package_dir


def alembic_config(dburi: str,
                   *,
                   ini_section="alembic",
                   version_table: str,
                   # models_name: List[str],
                   migrations_pkg="services") -> AlembicConfig:
    """
    :param dburi: full dsn of the SQL connection
    :param version_table: table name used to register migrations versions
    :models_name: 
    """
    # dir_ = get_package_dir(migrations_pkg)
    # alembic_file = f"{dir_}/alembic.ini"
    # TODO: add base path
    alembic_file = "alembic.ini"
    # this is need for alembic to register models
    models_module = importlib.import_module(f"{migrations_pkg}.models")
    # models = [importlib.import_module(mod) for mod in models_name]

    alembic_cfg = AlembicConfig(alembic_file, ini_section=ini_section)
    # alembic_cfg.set_main_option("script_location", migrations_pkg)
    alembic_cfg.set_main_option("version_table", version_table)
    # alembic_cfg.set_main_option("target_metadata", version_table)
    alembic_cfg.set_main_option("sqlalchemy.url", dburi)
    return alembic_cfg


class Migration:
    def __init__(self, dburi: str, *, package_dir: str, version_table: str):
        self.dburi = dburi
        self.package_dir = package_dir
        self.version_table = version_table

    def upgrade(self, to="head"):
        cfg = alembic_config(
            self.dburi,
            version_table=self.version_table,
            ini_section=self.package_dir,
            migrations_pkg=self.package_dir)

        command.upgrade(cfg, to)

    def downgrade(self, to="head-1"):
        cfg = alembic_config(
            self.dburi,
            version_table=self.version_table,
            ini_section=self.package_dir,
            migrations_pkg=self.package_dir)

        command.downgrade(cfg, to)

    def revision(self,
                 rev_id: Optional[str] = None,
                 message: Optional[str] = None,
                 sql: bool = False,
                 head: str = "head",
                 branch_label: Optional[str] = None,
                 version_path: Optional[str] = None,
                 depends_on: Optional[str] = None,
                 autogenerate=True
                 ):
        """
        :param rev_id: optional to specify a revision id
        :param message: to be used as message
        :param sql: to print in the stdout the sql generated
        :param head:  head revision to build the new revision upon as a parent
        :param depends_on:  optional list of "depends on" identifiers
        """

        cfg = alembic_config(
            self.dburi,
            version_table=self.version_table,
            ini_section=self.package_dir,
            migrations_pkg=self.package_dir)

        command.revision(
            cfg,
            message=message,
            rev_id=rev_id,
            autogenerate=autogenerate,
            sql=sql,
            head=head,
            depends_on=depends_on,
            branch_label=branch_label,
            version_path=version_path,

        )

from sqlalchemy.orm import registry as sql_registry

# equivalent to Base = declarative_base()

registry = sql_registry()
Base = registry.generate_base()

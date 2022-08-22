# Release

Based on https://devblogs.microsoft.com/devops/release-flow-how-we-do-branching-on-the-vsts-team/

The `main` branch is the development branch. Each release MUST go into `release/<version>`. 

Semantic version MUST be used for each release. 

The source of truth for the package is the version attribute in `pyproject.toml`. 

Using poetry could be updated doing:

```
poetry version preminor 
```

After `pyproject.toml` is updated, `./scripts/update_versions.sh` should be run to update `services/__version__py` file. 

Finally python package should be published into pypy.org


# Release checklist

- [ ] Update `pyproject.toml` and `pomofloat/__init__.py`.
- [ ] Add a Debian changelog entry and verify package metadata.
- [ ] Update `CHANGELOG.md` and README usage notes.
- [ ] Run the test suite and `pomofloat --version`.
- [ ] Build with `dpkg-buildpackage -us -uc -b` when Debian tooling is available.
- [ ] Review the generated artifacts and release notes.
- [ ] Create the annotated version tag and publish the release only from a
      trusted maintainer environment.

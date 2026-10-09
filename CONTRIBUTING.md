# Contributing

Thanks for helping improve Pomofloat. Small, focused pull requests are easiest
to review.

1. Create a branch from the default branch.
2. Keep changes scoped and preserve the existing UI, timer, icon, and Wayland
   behavior unless the change explicitly targets one of them.
3. Run `.venv/bin/python -m pytest` and check `.venv/bin/pomofloat --version`.
4. Update the changelog for user-visible changes.
5. Open a pull request using the provided template.

Please do not commit generated virtual environments, Debian build output, or
user settings. By contributing, you agree that your work is provided under
the repository's MIT license.

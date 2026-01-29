# Release Process

Follow these steps for a new release.

1. Run tests:

   ```bash
   pytest
   ```

2. Update version in `src/mac_cleaner/__version__.py`.

3. Update `CHANGELOG.md` with release notes.

4. Verify CLI/GUI/Web basics:

   ```bash
   mac-cleaner --version
   mac-cleaner analyze
   mac-cleaner gui
   mac-cleaner web
   ```

5. Commit and tag:

   ```bash
   git add .
   git commit -m "release: vX.Y.Z"
   git tag vX.Y.Z
   ```

6. Build package:

   ```bash
   python -m build
   ```

7. Publish to PyPI:

   ```bash
   python -m twine upload dist/*
   ```

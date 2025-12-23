# Epoch SemVer guide

FireCoast uses an epoch-based semantic version in the `VERSION` file with the format `epoch.major.minor.patch`.

## Component meanings
- **Epoch**: Marketing-level milestone that signals a new era for the product. Only increase for rare, highly visible shifts. Never decrease or remove.
- **Major**: Breaking API or behavior changes. Can increase more frequently than epoch.
- **Minor**: Backwards-compatible feature additions.
- **Patch**: Backwards-compatible bug fixes and small adjustments.

## When to bump
Choose the smallest component that reflects the change:
- Bug fix or internal refactor without new surface area → bump **patch**.
- New backwards-compatible capability → bump **minor**, reset patch to 0.
- Breaking change or migration requirement → bump **major**, reset minor/patch to 0.
- Large marketing/architectural moment → bump **epoch**, reset major/minor/patch to 0.

Do not decrease any component. If you bump a higher-order component, reset all lower ones to zero.

## How to update the VERSION file
1. Open `VERSION` at the repo root. It contains the current version string.
2. Parse it with the helper (optional):
   ```python
   from pathlib import Path
   from services.versioning import read_version_file

   current = read_version_file(Path("VERSION"))
   print(current)  # e.g., 1.0.0.0
   ```
3. Determine the correct bump (see above) and write the new value back to `VERSION` with the four-part string (e.g., `1.2.0.0`).
4. Commit the change alongside the feature/fix so the update flow can advertise the new release.

## Notes for Codex tasks
- Follow the bump rules above when a change warrants a version increment.
- If unsure, prefer the smallest bump that accurately reflects the change.
- Never modify the epoch component unless the change is a significant public milestone.

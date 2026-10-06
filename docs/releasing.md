# Release guide

```{admonition} This document is only relevant for svganim release managers.
:class: seealso

A guide for maintainers who are doing a svganim release.
```

A release publishes the package on [PyPI](https://pypi.org/project/svganim/). The
documentation on Read the Docs rebuilds on its own with every push to `main`, so
it needs no step.

## One-time setup

Publishing uses [trusted publishing](https://docs.pypi.org/trusted-publishers/),
so there is no API token to store. It only works while these two settings exist:

- On PyPI, a trusted publisher for the project `svganim` with owner
  `aleixalcacer`, repository `svganim`, workflow `publish.yml` and environment
  `pypi`.
- On GitHub, under Settings, Environments, an environment named `pypi`.

If the workflow name or the environment changes, update both places.

## Making a release

1. Bump the version of the project using a valid bump rule (`patch`, `minor`,
   `major`) according to the changes since the last release:

   ```bash
   uv version --bump patch
   ```

   This edits `pyproject.toml` and `uv.lock`. PyPI never accepts the same
   version twice, so every release needs a new one.

2. Commit the changes, push them and wait for the CI to pass:

   ```bash
   git commit -a -m "Getting ready for release $(uv version --short)"
   git push
   ```

3. Create the tag and the release on GitHub. The tag is created from `main`:

   ```bash
   gh release create v$(uv version --short) --generate-notes
   ```

   You can also [create a release](https://github.com/aleixalcacer/svganim/releases)
   on the web, with a tag named `v` followed by the version, such as `v0.1.1`.

4. Publishing the release runs the [Publish workflow](https://github.com/aleixalcacer/svganim/actions/workflows/publish.yml),
   which builds the package with `uv build` and uploads it to PyPI through
   trusted publishing, so no API token is involved. Check that it finishes, then
   install the new version in a clean environment and import it:

   ```bash
   uv run --no-project --with svganim==X.Y.Z python -c "import svganim"
   ```

```{note}
Only publishing the release triggers the upload. Pushing a tag or saving a draft
release does nothing.
```

## If the publication fails

PyPI never accepts the same version twice, so what to do depends on how far the
upload got:

- If the workflow failed before uploading anything, for example because of a
  misconfigured publisher, fix the cause and re-run the failed jobs from the
  Actions tab. The release does not need to be created again.
- If PyPI already has files for that version, bump to the next one and make a new
  release. A version cannot be replaced, not even after deleting it.

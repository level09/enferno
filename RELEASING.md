# Releasing

A change to Enferno is described in several places. Each release, update every place the change touches, so the README, docs, website and announcements never disagree.

## Checklist

1. **Code checks**: `uv run ruff check --fix . && uv run ruff format .` and `uv run pytest`. For UI changes, click through `/dashboard/` and `/users/` as an admin.
2. **Version**: bump `pyproject.toml`, run `uv lock`, and add a `CHANGELOG.md` entry with upgrade notes.
3. **Agent docs**: `AGENTS.md` and `.agents/skills/enferno-dev/` when a pattern, route, command or rule changed.
4. **README.md**: "What's in the box" and "How your agent checks its work".
5. **Docs** (`docs/`, published at docs.enferno.io by Mintlify from `master`): the page for each feature that changed.
6. **Website** (enferno.io, a separate repo deployed to the Cloudflare Pages project `enferno-io`): the version in the hero, the stack tags, the checks and commands it shows, and the FAQ. Deploy from a folder that holds only the site files:

   ```bash
   npx wrangler pages deploy <dir> --project-name enferno-io --branch main
   ```

7. **Drift check**: search the README, `docs/` and the website for the previous version number and for any file, command or library the release removed or renamed.
8. **Release**: tag `vX.Y.Z`, then publish the release with its notes from the changelog and a linked announcement:

   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z - Headline" --notes-file notes.md --discussion-category Announcements
   ```

9. **Announcements**: if an older announcement no longer matches the project, add a note to its top pointing to the current state.

## Reaching users

Starring a repository sends no notifications. Only watchers hear about a release, so a release worth sharing also needs a post outside GitHub that links to it. The README asks readers to watch for releases (Watch, Custom, Releases).

# Sheria Wazi: an AI-run Kenyan law explainer site

Every Monday (and on demand) a GitHub Action runs this pipeline:

1. **ingest**: downloads the Acts listed in `sources.yml` and saves dated snapshots in `sources/`.
2. **draft**: for each topic in `topics.yml` with no article yet, Claude writes one using only the stored text, with a verbatim quote for every legal claim.
3. **verify**: code checks that each quote appears word for word in the source, and that no number appears without a quote. A second Claude pass checks each quote really supports its claim. Passes go to `content/articles/`; failures go to `held/` with reasons. Articles whose source changed are rechecked and marked `needs-recheck` if they fail.
4. **build**: renders the static site into `dist/` and deploys it to GitHub Pages.
5. **report**: summary on the run page and in `reports/latest.md`.

## Setup (about 15 minutes)

1. Create a GitHub repo and push this folder to the `main` branch.
2. Repo Settings > Pages > Source: **GitHub Actions**.
3. Settings > Secrets and variables > Actions: add secret `ANTHROPIC_API_KEY`.
4. Add a variable `SITE_BASE`: `/your-repo-name` for the default URL, or leave empty with a custom domain.
5. Edit `sources.yml`: paste the Kenya Law URL for each Act (HTML or PDF). Read Kenya Law's reuse terms first. Articles only quote short passages.
6. Edit the contact string in `pipeline/ingest.py`, then run Actions > pipeline > Run workflow.

## Moving from samples to verified articles

The five sample articles have `status: unverified` and are shown with a red "Draft" badge. To replace them with pipeline-written ones, add their topics to `topics.yml` (the format is in that file) and delete the sample file. Once all are replaced, set the repo variable `PUBLISH_UNVERIFIED` to `false` so nothing unchecked is published.

## Notes

- Held articles are never published. Fix the topic or sources, delete `held/<slug>.json`, and the next run tries again.
- To record an advocate's review, set `reviewed_by: "Name, Advocate"` in an article's frontmatter. The badge will show it.
- Model: set repo variable `CLAUDE_MODEL` to change it (default `claude-sonnet-5-5`).
- Test locally: `pip install -r requirements.txt`, then `python -m pipeline.build_site` and open `dist/index.html`.

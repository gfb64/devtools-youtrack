# Adoption publishing fixture

This trial fixture proves a small documentation-first publishing path. Git is
authoritative; the YouTrack article is the human-readable copy.

| Item | Expected result |
| --- | --- |
| Source | Markdown in this repository |
| Update | Reuse the existing article ID |
| Conflict | Detect and report before overwrite |

The companion [child article]({{CHILD_ARTICLE_URL}}) contains the workflow
example and diagram.

```sh
git show {{SOURCE_COMMIT}}:docs/knowledge/adoption-publishing-parent.md
```

![Representative YouTrack screen](trial-screen.png)

## Source record

- Repository: `git@github.com:gfb64/devtools-youtrack.git`
- Path: `docs/knowledge/adoption-publishing-parent.md`
- Commit: `{{SOURCE_COMMIT}}`


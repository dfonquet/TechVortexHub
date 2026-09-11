# Custom-domain deployment

Target: https://danielfonque.com/

## Architecture

`.github/workflows/deploy-pages.yml` uploads **only the contents of
`My_Website/`** as the GitHub Pages artifact root. No framework, build tool,
iframe, or homepage redirect is involved. Repository-root files and unrelated
workflows are not part of the published artifact. Existing files within
`My_Website/`, including downloadable lab material, remain included.

`My_Website/index.html` is the canonical homepage. `daftiel.html` remains a
full identical compatibility copy, including its original section IDs.
Both declare `https://danielfonque.com/` as canonical. When editing the home
page, update `index.html` and copy it to `daftiel.html`; the deployment checks
that the two files are identical to prevent drift.

Relative asset paths are unchanged. Secondary-page Home links use `../`
and contact links use `../#contact`, resolving to the canonical root page.

Expected published paths:

- `/`
- `/daftiel.html` (compatibility, including fragment links)
- `/Projects/projects.html`
- `/Projects/ccie-sp-labs.html`
- `/Blog/blog.html`
- `/Blog/archive.html`
- `/Blog/<existing-article>.html`

## Manual activation after review

The inspected setup publishes `main` from `/` using the branch-based Pages
builder, with no custom domain. No settings have been changed by this work.

1. Review these changes before committing or pushing them.
2. Coordinate the cutover: in repository **Settings > Pages**, select
   **GitHub Actions** as the publishing source.
3. Set **danielfonque.com** as the custom domain in Pages settings. Domain
   verification, DNS configuration and HTTPS readiness are owner-managed
   prerequisites; this change does not configure them.
4. Once the reviewed workflow is on `main`, run **Deploy portfolio to GitHub
   Pages** manually if a matching push did not already trigger it.
5. Check the deployment and certificate readiness, then enable/enforce HTTPS
   in Pages settings when GitHub makes it available.

The workflow uses the standard `GITHUB_TOKEN`, read-only repository access,
Pages deployment permission and an OIDC token. `configure-pages` explicitly
disables automatic enablement. No settings API, DNS API or Cloudflare service
is called. No `CNAME` file is needed for an Actions-based Pages deployment;
the custom domain must be set in repository settings.

## Compatibility checks at cutover

- Lightweight legacy HTML redirects now cover both `/My_Website/...` and
  `/TechVortexHub/My_Website/...`. See the mapping and limitations below.
- Giscus currently maps discussions by pathname. The new article paths may
  therefore resolve to different discussion threads. Review an explicit
  discussion mapping/migration before cutover if existing comments must be
  retained. Discussion settings and content are unchanged here.
- Web-Stat remains installed with the same account and script. Check the
  new domain in its dashboard after cutover; old and new paths may be
  counted separately.
- Canonical, Open Graph, Twitter image and JSON-LD URLs now target the new
  domain. They assume the domain is active; coordinate publishing accordingly.
- This workflow has not been executed remotely during preparation. Deployment
  requires the manual Pages-source/domain setup above.

## Local preview

Run from the repository root:

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory My_Website
```

Open `http://127.0.0.1:8765/` to test the same directory layout as the artifact.

References:

- [Official Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

## Legacy public entry points

There are 28 small redirect pages: 14 previously published HTML entry points
under each of two prefixes. These files contain only a title, canonical URL,
immediate HTML meta refresh and clickable fallback link. They include no site
content, CSS, images, analytics or JavaScript. The main site is not mirrored.
They are inside `My_Website/`, so the existing artifact upload includes them.

| Published compatibility prefix | Source directory |
| --- | --- |
| `/My_Website/` | `My_Website/My_Website/` |
| `/TechVortexHub/My_Website/` | `My_Website/TechVortexHub/My_Website/` |

Append each entry below to either prefix. All targets are absolute HTTPS URLs
on `danielfonque.com`, going directly to content rather than another redirect.

| Legacy entry suffix | Canonical destination path |
| --- | --- |
| `Blog/archive.html` | `/Blog/archive.html` |
| `Blog/blog.html` | `/Blog/blog.html` |
| `Blog/campus-floor-connectivity-design.html` | `/Blog/campus-floor-connectivity-design.html` |
| `Blog/ccie-sp-multicast-asm.html` | `/Blog/ccie-sp-multicast-asm.html` |
| `Blog/ccie-sp-ospf-isis-sr-mpls-migration.html` | `/Blog/ccie-sp-ospf-isis-sr-mpls-migration.html` |
| `Blog/gitlab-ci-network-configuration.html` | `/Blog/gitlab-ci-network-configuration.html` |
| `Blog/ios-xr-network-state-collection-engine.html` | `/Blog/ios-xr-network-state-collection-engine.html` |
| `Blog/junos-troubleshooting-field-notes.html` | `/Blog/junos-troubleshooting-field-notes.html` |
| `Blog/netdevops-controlled-change-ios-xr.html` | `/Blog/netdevops-controlled-change-ios-xr.html` |
| `Blog/netlab-core-eve-ng-golden-image.html` | `/Blog/netlab-core-eve-ng-golden-image.html` |
| `Blog/route-target-rd-l3vpn.html` | `/Blog/route-target-rd-l3vpn.html` |
| `Projects/ccie-sp-labs.html` | `/Projects/ccie-sp-labs.html` |
| `Projects/projects.html` | `/Projects/projects.html` |
| `daftiel.html` | `/` |

Coverage comes from all 14 HTML entry points in the previously published
repository: the homepage linked by README, both Projects pages, Blog and
Archive, and all nine articles linked by the current navigation/archive.
This includes the existing engineering articles shared through the portfolio;
no enumeration of unrelated LinkedIn posts or private content is needed.
No redirects are added for raw images, downloadable lab files or other assets.

### Expected GitHub redirect behavior

Configure the custom domain on **TechVortexHub itself**, as planned. The
expected project-site mapping replaces its site base
`https://dfonquet.github.io/TechVortexHub/` with `https://danielfonque.com/`.
The repository prefix is removed; the remaining file path is preserved.
For example, the expected chain is:

```text
https://dfonquet.github.io/TechVortexHub/My_Website/Blog/blog.html
  -> https://danielfonque.com/My_Website/Blog/blog.html
  -> https://danielfonque.com/Blog/blog.html
```

The first hop is GitHub's domain redirect. The second is our HTML redirect.
GitHub does not infer that the source directory `My_Website/` should also be
removed just because the artifact now publishes its contents at the root.
The fully prefixed compatibility pages additionally handle direct requests
such as `https://danielfonque.com/TechVortexHub/My_Website/Blog/blog.html`.

This differs from a project **inheriting a user/organization site's domain**:
GitHub documents that an inherited project remains under its repository name
(e.g. `www.octocat.com/octo-project`). Setting a custom domain on the individual
project overrides that inheritance. See
[GitHub's domain inheritance documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages#using-a-custom-domain-across-multiple-repositories).

The exact first-hop HTTP status and Location header for this repository cannot
be observed before the domain is configured. The project-specific mapping
above is the expected behavior, not a completed live-cutover test; both path
variants are covered so the compatibility layer does not depend on retaining
or removing the repository prefix.

### Redirect limitations and cutover verification

- These static files are served as HTML (normally HTTP 200), not server-side
  301 responses. Meta refresh performs the immediate navigation; the ordinary
  link remains usable if automatic refresh is disabled.
- The redirects use fixed canonical destinations. Query strings are not
  forwarded, and fragment/section preservation should not be relied on across
  meta-refresh implementations. Old section links still reach the correct
  page, but may arrive at its top. No JavaScript has been added for this.
- No broad 404 handler, rewrite rule, recursive directory copy or redirect to
  another compatibility URL is involved.
- Domain/DNS activation is still required. Until then, following these stubs
  points at the planned domain, not the currently published GitHub site.
- After activation, inspect the actual GitHub first hop, for example:

```sh
curl -I https://dfonquet.github.io/TechVortexHub/My_Website/daftiel.html
curl -I https://dfonquet.github.io/TechVortexHub/My_Website/Blog/blog.html
```

Then open each legacy URL in a browser to check the HTML refresh, and verify
its fallback link with automatic refresh disabled. `curl -L` follows HTTP
redirects only; it does not execute HTML meta refresh.

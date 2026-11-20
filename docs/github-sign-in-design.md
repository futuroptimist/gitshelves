# GitHub sign-in: design and security review

**Status: proposal only.** This document does not authorize implementation,
GitHub registration, secret changes, or deployment. Review it before any of
those steps. It builds on the separately proposed anonymous daily public
commit preview; neither sign-in nor its approval is required to ship that
preview.

## Goal and scope

Keep prominent anonymous username search. Add optional **Sign in with GitHub**
and, once GitHub has established the user's identity, **Show my public
commits** and **Sign out**. Signing in does not start a commit search. “Show my
public commits” submits the verified login through exactly the same anonymous
public-search path as typing a username: last 30 UTC days, public
default-branch commits indexed by GitHub, a bounded sample, logarithmic daily
stacks. Do not call these all GitHub contributions. **Clear activity** resets
the preview without changing sign-in; **Sign out** ends the local session,
cancels pending identity/preview work and clears the account label and preview,
without discarding imported local data.

No email access, repository access for the identity flow, private
contributions, installations, webhook, background sync, account database,
durable profile or activity storage, personal access tokens, or GitHub API
calls from browser JavaScript. Existing offline/STL behavior stays local.
Static Sites cannot host the callback: on a static export or a host that has
not opted in, hide sign-in and preserve existing behavior; do not emulate
authentication locally.

## Provider decision

| Option                                | What it buys                                                                                                                             | Risks and constraints                                                                                                                                                                                                                                                                              |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Anonymous only                        | No credentials, cookies, provider setup or sensitive callback                                                                            | Does not provide real sign-in. Keep it available and use it as the rollback.                                                                                                                                                                                                                       |
| Dedicated GitHub OAuth App, no scopes | Smallest identity integration; server-side authorization-code flow supports PKCE S256; no app installation                               | No-scope access is public read; a reused app can inherit old scopes, and a token can outlive the callback absent revocation/expiry. Needs an app and client secret for each enabled environment.                                                                                                   |
| GitHub App, identity only             | GitHub recommends GitHub Apps generally; fine-grained configuration, and expiring user tokens can bound residual access if cleanup fails | Additional registration choices and app permission drift; default metadata and sign-in without installation must be verified. Never install the app or generate a private key/installation token for this feature. Expiring flows may return a refresh token; it too must never be stored or used. |

**Recommendation for first review:** use a new, dedicated no-scope OAuth App
per enabled environment, not an existing general-purpose app. Require
confirmed per-token cleanup and test the provider behavior before activating
any environment. Explicitly send empty requested scope and independently
require the exchange response to establish that granted scope is empty
before using the token. GitHub documents inherited access for omitted scope;
do not assume an empty request overrides a prior grant. Confirm the exact
response and scope semantics against a fresh, owner-controlled _staging_
app before production. GitHub also offers [expiring OAuth App tokens](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#expiring-access-tokens).
For this proposal require the no-refresh response path, explicitly trading
off provider-enforced short expiry if cleanup fails. Unexpected expiry or
refresh fields, a missing or nonempty granted scope, or consent asking for
extra permissions are stop conditions. If immediate revocation, narrow authorization, or
consent cannot be demonstrated, keep the feature off and bring the
GitHub App alternative back for security review; do not silently fall back.

Sources: [OAuth web flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#web-application-flow),
[scope descriptions](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps),
[GitHub App vs. OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps),
[GitHub App user token flow](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app),
and [OAuth security best current practice](https://www.rfc-editor.org/rfc/rfc9700.html#section-2.1).

## Boundaries and proposed request flow

1. **Opt-in.** Serve auth only from the container backend and only when
   explicitly enabled. An exact, canonical HTTPS origin and a fixed
   callback path form the registered redirect URI; use that exact URI in
   both authorize and exchange. Use GitHub's [exact callback matching](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#redirect-urls) with wildcard matching disabled.
   Never derive it from a request, forwarded
   headers, or a return URL. Enforce the exact public host at the trusted
   TLS ingress and at the app boundary, reject ambiguous paths and
   duplicate routing/security headers, and prevent bypass of that ingress.
   Do not accept CORS or a cross-origin callback grant to the frontend.
2. **Start.** Accept a same-origin POST with exact Origin and bounded request.
   Generate a cryptographic nonce, one-time browser binding, and independent
   PKCE verifier; store the verifier server-side for at most 5 minutes. Sign
   the state over the browser binding and nonce using a process-generated
   HMAC key; compare in constant time. Send only an S256 challenge to
   the fixed GitHub authorize endpoint. Request account selection when
   supported so the user can see which GitHub identity is being used. Use a
   secure, host-only,
   HttpOnly, SameSite=Lax, Path=/ binding cookie with a \_\_Host- prefix.
   Never include a local session ID, submitted username, or destination in
   state. Starting again invalidates the previous attempt. A top-level GET
   GitHub callback legitimately has no same-origin Origin; the browser
   binding, state, exact host/path and PKCE are its controls.
3. **Callback.** Require exactly one well-formed code and state, or recognize a
   bounded denial without echoing provider detail. Reject duplicates and
   ambiguity. Consume the signed, unexpired, browser-bound transaction
   atomically before exchanging; simultaneous requests get one attempt
   total. Only fixed official HTTPS endpoints on github.com and
   api.github.com are permitted. Require TLS certificate verification,
   refuse redirects, and send outbound credentials only to intended
   endpoints. Bound DNS/connect/read and end-to-end deadlines, response
   size, concurrency and rate; never automatically retry a code exchange.
4. **Resolve identity and destroy the GitHub token.** Exchange the code
   server-to-server. On a valid no-scope token, call the fixed authenticated
   GitHub /user endpoint once; use its validated login only. A profile may
   contain public fields such as a user-listed email: do not inspect, store,
   return or use them, and never call an email endpoint. Reject contradictory
   scope information.
   Never retain provider credentials in a browser, session, DB, cache,
   tracing, or log. Whether identity succeeds or not, attempt to delete any
   usable issued access token via GitHub's [Delete an app token](https://docs.github.com/en/rest/apps/oauth-applications#delete-an-app-token)
   endpoint with its documented app credentials and body. Successful 204
   cleanup is required before creating a local session. This does **not**
   delete the grant or sign the user out of GitHub. A lost exchange
   response, provider failure, or crash can leave a token outstanding:
   report only a sanitized operational error, create no session, do not
   store the token for later retries, and follow the owner incident
   procedure (disable the feature and use GitHub's revocation controls).
   An unexpected refresh token is a stop even after access-token cleanup:
   do not store or use it, do not infer its revocation from the 204, and
   require owner review and grant-level revocation as appropriate.
   Do not claim the token or grant is gone when cleanup was not confirmed.
5. **Session and logout.** Rotate any prior session on successful login.
   Use an opaque high-entropy token in a second \_\_Host- Secure, HttpOnly,
   SameSite=Lax, Path=/ cookie. Store only an in-memory session identifier,
   validated public login, expiry (at most 1 hour, not sliding) and a
   random logout CSRF token. The same-origin session endpoint returns
   only the public login and CSRF token, with no-store and no CORS.
   Logout is a bounded POST with exact Origin plus the token. Atomically
   invalidate the local session and associated pending flow, expire both
   cookies, and ensure an in-flight callback cannot revive a signed-out
   session. Link session rotation and pending transactions to one bounded
   browser-session family. Keep its generation stable across concurrent starts
   and recheck it under lock at callback insertion. Logout atomically advances
   or invalidates the generation, including starts already pending at logout.
   A late Set-Cookie, even if its callback committed just before logout,
   cannot authenticate. The browser must ignore older account and lookup responses
   after sign-out.
   GitHub grant revocation is a separate user action; this
   identity-only preview does not assume a local session grants GitHub
   permissions or check upstream sessions on every page.
6. **Public lookup.** Reuse the separate anonymous lookup with no Cookie or
   Authorization header going to GitHub. Restrict GitHub's query to public
   resources and match the validated login to returned author records. The
   anonymous service cannot read auth session state. Render the login/error
   as text, not HTML. Do not copy provider responses, credentials, or
   session identifiers into app storage, generated assets, or URLs.

### Proposed interface

| Same-origin request             | Contract                                                                                                                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /api/github-auth/start`   | Exact Origin; limits checked before allocating state. Set binding cookie and 303 a top-level form navigation to the fixed GitHub authorize endpoint; do not rely on a cross-origin fetch redirect. |
| `GET /api/github-auth/callback` | Registered fixed path. Consume a valid transaction exactly once. Redirect 303 to a clean fixed landing path on success or generic failure.                                                         |
| `GET /api/github-auth/session`  | Same-origin/no CORS, no-store. Returns only signed-out status or validated public login and a logout CSRF token. Never calls GitHub.                                                               |
| `POST /api/github-auth/logout`  | Exact Origin plus CSRF token, no provider call. Invalidate the session family and expire cookies.                                                                                                  |

No browser-to-GitHub API fetch. The one intentional cross-origin browser
navigation is GitHub's top-level authorization page. Implement UI auth
availability from the same-origin session endpoint; missing/disabled routes
must not provoke GitHub calls. All auth responses and the callback redirect
are explicitly noncacheable.

### Security and failure review

| Risk                                                         | Required behavior and verification                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Login CSRF, intercepted code, replay or race                 | Signed browser-bound state, one-time use, S256 verifier, fixed callback, atomic consume, fresh local session, no session after sign-out race. Test invalid, expired, other-browser, duplicate and concurrent callbacks; none may create a new session.                                                                                                           |
| Logout CSRF, cookie theft or session fixation                | Exact Origin, POST-only logout with token, fresh opaque session, TLS and host-only cookies, no-store identity, CSP/asset boundary review and no third-party scripts on auth surfaces. Test absent/wrong Origin or token, pre-login session reuse, expired sessions, cookie attributes and actual invalidation.                                                   |
| Leaking authorization codes, headers, tokens or profile data | Callback immediately redirects to a clean fixed local path, with no HTML/assets, no-store and no-referrer. Disable request targets with queries, sensitive headers and bodies in app, proxy, ingress, telemetry and error logs; review buffering, cache and tracing behavior. Validate with synthetic markers and sanitized evidence, never genuine credentials. |
| OAuth scopes drift or private data leak                      | New dedicated registration, no requested permissions, verify granted scopes, fixed identity request and per-token deletion, independently anonymous commit requests, no user-controlled egress URL. Test token shape/scope, malformed upstream, redirect, timeout, 429/5xx and failed cleanup; no private lookup or local session.                               |
| Denial of service, process restart or deployment rollout     | Small bounded stores, expiring entries, per-instance concurrency and request budgets, approved ingress rate limits and observable error counters without identifiers. Rate limits affect auth only, not anonymous search. Crash or restart clears flows and sessions; prompt to retry, do not relax checks.                                                      |

For the MVP use **one serving process/replica**, not sticky sessions or a
stateless bearer cookie: process-local state gives true single-use consumption
and immediate logout, whereas signing a self-contained browser cookie alone
does neither. A multi-replica rollout requires separately reviewed shared
atomic state with TTL and revocation semantics; do not enable auth on an
existing multi-replica rollout or modify infrastructure as a side effect of
this design. Rolling restarts may briefly overlap even at one replica; auth
must not be enabled in that shape unless a controlled nonoverlapping rollout
is approved and verified. No unnamed proxy/ingress behavior should be assumed safe.

## Review, implementation and activation gates

1. **Owner/design review now:** confirm the identity-only UX, dedicated
   OAuth App recommendation, residual-token policy, single-replica constraint
   and the separation from anonymous preview. Security reviewer signs off on
   the threat table and acceptance tests or requests changes.
2. **Implementation later, only on approval:** small, default-disabled
   PR after the anonymous preview, with separate auth handlers. Test in
   a reusable pinned container against mocked TLS provider and ingress,
   including disabled static export and anonymous search with no auth
   traffic, full sign-in and rollback, browser-cookie and logout races,
   log redaction, wrong host/origin and header handling, store saturation,
   restart and simultaneous replay. No real GitHub credentials in CI.
3. **Owner activation after vetted implementation:** owner alone registers
   a dedicated staging app, configures exact callback, secret injection,
   HTTPS host, proxy log redaction and opt-in, and approves deployment.
   Proposed inputs (names only): `GITSHELVES_GITHUB_OAUTH_ENABLED` (default
   off), `GITSHELVES_GITHUB_OAUTH_ORIGIN` (exact HTTPS origin),
   `GITSHELVES_GITHUB_OAUTH_CLIENT_ID`, and
   `GITSHELVES_GITHUB_OAUTH_CLIENT_SECRET` (server-only, injected from
   owner-managed secret storage). Do not
   commit these values or expose the secret through Vite or the browser.
   Reproduce the no-scope consent and 204 cleanup on staging with a
   consenting account, prove the real proxy boundary and absence of
   sensitive logging, confirm anonymous availability with auth disabled,
   and record sanitized evidence. No production activation until owner
   reviews that evidence, confirms an appropriate single-replica target,
   and supplies separate authorization for the production app and
   deployment. Unresolved provider or ingress proof means leave it off.

If disabled or misconfigured, no auth routes capable of an upstream call,
no sign-in UI, and no impairment to anonymous search or local import. An invalid opt-in configuration
disables auth with a reason-only startup diagnostic rather than taking down
the preview service.
Rollback is owner-controlled opt-out and restart to clear local sessions;
if provider cleanup is uncertain, owner verifies/revokes authorization at
GitHub as appropriate. No automatic deployment, credential or settings
changes.

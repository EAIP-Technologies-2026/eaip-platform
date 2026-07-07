# Getting Support

Thanks for using EAIP! This document explains **where to get help**, **what to expect**, and **how to file an effective request**.

---

## Quick Triage

| You want to…                                 | Go here                                                                  |
| -------------------------------------------- | ------------------------------------------------------------------------ |
| Ask a usage question                         | [GitHub Discussions › Q&A](<https://github.com/subham1902/eaip-platform/discussions/categories/q-a>) |
| Report a bug                                 | [New Bug Report](<https://github.com/subham1902/eaip-platform/issues/new?template=bug_report.yml>) |
| Request a feature                            | [New Feature Request](<https://github.com/subham1902/eaip-platform/issues/new?template=feature_request.yml>) |
| Report a security vulnerability              | See [`SECURITY.md`](SECURITY.md) — **do not file a public issue**        |
| Discuss design / RFCs                        | [GitHub Discussions › Ideas](<https://github.com/subham1902/eaip-platform/discussions/categories/ideas>) |
| Real-time chat                               | `#eaip` on the community Slack *(invite link in Discussions pinned post)* |
| Commercial support / SLA                     | `hello@eaip.dev`                                                         |

## Before You Open an Issue

1. **Search first.** Most questions have already been asked. Check open *and* closed issues and Discussions.
2. **Read the docs** — `README.md`, [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md), and [`ARCHITECTURE.md`](ARCHITECTURE.md).
3. **Use a supported version.** See [`SECURITY.md`](SECURITY.md#supported-versions).
4. **Produce a minimal reproducer.** Strip everything that is not essential.
5. **Include the basics:**
   - EAIP version (`eaip --version` once available; otherwise commit SHA)
   - Python version (`python --version`)
   - OS and architecture
   - Exact command(s) and full stack trace / logs (use code fences)

A good bug report saves multiple round-trips. A great bug report often leads to a fix in hours instead of weeks.

## Response Expectations

EAIP is primarily a **community-supported open-source project**. There is no implicit SLA for community channels. That said, the maintainers aim for:

| Channel                      | First Response *(target)* |
| ---------------------------- | ------------------------- |
| GitHub Discussions           | 3 business days           |
| GitHub Issues (bugs)         | 5 business days           |
| Security reports             | 2 business days *(see [`SECURITY.md`](SECURITY.md))* |
| Pull Requests                | 5 business days           |

If you need guaranteed response times, prioritised fixes, private support channels, or training, see **Commercial Support** below.

## Issue Lifecycle

```
new → triage → accepted → in-progress → fixed → released → closed
                ↓
            needs-info → (stale after 30d) → closed
```

- Issues labelled `needs-info` will auto-close after **30 days** of inactivity. Reopen anytime with the requested details.
- Issues labelled `wontfix` include an explanation; design discussion is welcome but the decision usually stands.

## Commercial Support

Paid support is available for organisations that need:

- Guaranteed response and resolution SLAs.
- Architecture reviews and adoption consulting.
- Custom feature engineering and prioritised roadmap influence.
- Long-term security maintenance for older versions.

Contact `hello@eaip.dev` for a conversation.

## Code of Conduct

All support channels are governed by our [Code of Conduct](CODE_OF_CONDUCT.md). Be kind, be patient, assume good intent.

---

If you can't find what you need, open a Discussion thread — we'd rather hear from you than have you stuck.

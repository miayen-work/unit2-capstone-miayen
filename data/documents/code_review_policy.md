# Code Review Process

Every pull request at Cloudly requires at least one approval before merging. The author
opens a PR against `main`, assigns at least one reviewer from their team, and links any
related ticket.

Reviewers check for correctness, test coverage, and adherence to the style guide. Reviewers
are expected to leave an initial review - either approving, requesting changes, or asking
questions - within 2 business days (48 hours) of the PR being opened. Larger PRs (500+ lines)
may take longer, but the author should split them into smaller PRs where possible.

Once a PR has an approval and passing CI, the author is responsible for merging it. Reverts
require a follow-up ticket explaining why.

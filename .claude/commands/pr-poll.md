Squash-merge PR #$ARGUMENTS to completion, resolving any blockers along the way.

## Steps

1. **Get PR status**: Run `gh pr view $ARGUMENTS --json state,mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,headRefName,baseRefName,title` to understand the current state.

2. **Check for merge conflicts**: If `mergeable` is `CONFLICTING`, pull the latest base branch and rebase:
   - `git fetch origin`
   - `git checkout <head-branch>`
   - `git rebase origin/<base-branch>`
   - Resolve any conflicts (read the conflicting files, understand both sides, pick the correct resolution)
   - `git push --force-with-lease`
   - Re-check PR status after pushing

3. **Check CI status**: If `statusCheckRollup` shows any failing checks:
   - Identify which checks failed using `gh pr checks $ARGUMENTS`
   - For each failure, fetch the logs: `gh run view <run-id> --log-failed`
   - Diagnose the root cause (test failures, lint errors, build errors, type errors)
   - Fix the issues in code, commit with a descriptive message, and push
   - Wait for CI to re-run: poll `gh pr checks $ARGUMENTS` every 30 seconds until all checks pass or fail again
   - If checks fail again, repeat the diagnose-fix-push cycle (max 3 attempts)

4. **Check review status**: If `reviewDecision` is `CHANGES_REQUESTED`:
   - Read the review comments: `gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/reviews`
   - Read individual review comments: `gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments`
   - Address each piece of feedback by making the requested changes
   - Commit and push the fixes
   - Leave a comment summarizing what was addressed: `gh pr comment $ARGUMENTS --body "..."`

5. **Squash and merge**: Once all checks pass, no conflicts, and reviews are approved (or no reviews required):
   - `gh pr merge $ARGUMENTS --squash --auto` to enable auto-merge, OR
   - `gh pr merge $ARGUMENTS --squash` to merge immediately if everything is green
   - Confirm the merge succeeded by checking `gh pr view $ARGUMENTS --json state`

6. **Clean up**: After successful merge:
   - `git checkout <base-branch>`
   - `git pull`
   - Delete the local branch: `git branch -d <head-branch>`

## Important

- Always use `--squash` for the merge strategy
- Never force-push to main/master
- If you encounter an issue you cannot resolve after 3 attempts, stop and report the status to the user
- When fixing CI failures, run the failing tests locally first to verify your fix before pushing
- Preserve the PR title as the squash commit message

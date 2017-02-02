

# Contributing to loginsight-export

The loginsight-export project team welcomes contributions from the community. If you wish to contribute code and you have not
signed our contributor license agreement (CLA), our bot will update the issue when you open a Pull Request. For any
questions about the CLA process, please refer to our [FAQ](https://cla.vmware.com/faq).

## Contribution Flow

This is a rough outline of what a contributor's workflow looks like:

- Fork the repository.
- Create a topic branch from where you want to base your work
- Make commits of logical units
- Run tests with `tox` locally
- Push your changes to a topic branch in your fork of the repository
- Submit a pull request


### Staying In Sync With Upstream

When your branch gets out of sync with the vmware/master branch, use the following to update:

``` shell
git checkout my-new-feature
git fetch -a
git pull --rebase upstream master
git push --force-with-lease origin my-new-feature
```

### Updating pull requests

If your pull request fails to pass continuous integration or needs changes based on code review,
push additional commits into the branch and update the pull request.

Avoid squashing or amending commits that have already been pushed. Never force-push.

If yup update a pull request and are ready for re-review, add a comment.

### Code Style

pytest checks for pep8 and pyflakes complaince as part of continuous integration.

### Formatting Commit Messages

We follow the conventions on [How to Write a Git Commit Message](http://chris.beams.io/posts/git-commit/).

Keep explainations of _what_ changed to a single sentence. `git` already does a very good job of that. Spend a few more sentences justifying _the reason_ for the change.

Be sure to include any related GitHub issue references in the commit message.  See
[GFM syntax](https://guides.github.com/features/mastering-markdown/#GitHub-flavored-markdown) for referencing issues
and commits.


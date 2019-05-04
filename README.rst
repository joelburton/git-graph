Git Graph
=========

Create digraph from this Git repository.

Create "teaching-style" commit graphviz diagram of Git repository.
This does not show unreachable commits (except the single one)

This will include:

- commits, with friendly name, friendly commit, sha-id
- branch pointers (with visual distinction for tracking branches)
- HEAD pointer (with visual distinction for detached HEAD)
- tags

Requirements
------------

- Python libraries:
  - pygit2
  - graphviz  

Currently, script uses AppleScript to open "Skim", a Mac PDF viewer.
This can be trivially changed to use your favorite way to open your
favorite PDF viewer.

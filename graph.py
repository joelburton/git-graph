"""Create digraph from this Git repository.

Create "teaching-style" commit graphviz diagram of Git repository.
This does not show unreachable commits (except the single one)

This will include:

- commits, with friendly name, friendly commit, sha-id
- branch pointers (with visual distinction for tracking branches)
- HEAD pointer (with visual distinction for detached HEAD)
- tags
"""

__author__ = "Joel Burton <joel@joelburton.com>"
__version__ = "1.0"

import sys
import applescript
import pygit2
import graphviz

STATUSES_TO_SHOW_IN_INDEX = {
 pygit2.GIT_STATUS_INDEX_DELETED: "del",
 pygit2.GIT_STATUS_INDEX_MODIFIED: "mod",
 pygit2.GIT_STATUS_INDEX_NEW: "new",
 pygit2.GIT_STATUS_INDEX_RENAMED: "mv",
}

NODE_STYLE_HEAD = dict(
    style="filled", 
    shape="doubleoctagon", 
    fontsize="12")
NODE_STYLE_HEAD_ATTACHED = dict(**NODE_STYLE_HEAD, color='goldenrod')
NODE_STYLE_HEAD_DETACHED = dict(**NODE_STYLE_HEAD, color="violet")

NODE_STYLE_INDEX = dict(shape="record", fontsize="10")

NODE_STYLE_BRANCH = dict(
    shape="octagon", 
    style="filled", 
    fontsize="12")
NODE_STYLE_BRANCH_LOCAL = dict(**NODE_STYLE_BRANCH, color='gold')
NODE_STYLE_BRANCH_REMOTE = dict(**NODE_STYLE_BRANCH, color='khaki') 
   
EDGE_STYLE_REF = dict(style="dashed")

EDGE_STYLE_MERGES = dict(fontsize="8", fontcolor='gray50')

NODE_STYLE_TAGS = dict(
    style="filled", 
    shape="house", 
    color="turquoise", 
    fontsize="12")

commits = {}

def sha(obj):
    """Return abbreviated SHA id for commit object."""
    return obj.hex[0:6]

def add_commits(id_obj):
    """Walk from this obj, and add all commits to commits-to-explore dict.

    `commits` dict is basically a `to_visit` set, except that since pygit2
    doesn't have stable identities for a commit, it won't treat the same
    commit as the same. So we store them in the dict by their SHA.
    """

    for commit in repo.walk(id_obj):
        commits[sha(commit)] = commit


# Create graphviz drawing & set aesthetic defaults for types

dot = graphviz.Digraph()
dot.attr('graph', rankdir='RL')  # time moves toward the right
dot.attr('edge', arrowsize="0.7", color='gray50')
dot.attr('node', color='gray50', margin="0.05,0.02")


repo = pygit2.Repository(".")

# show index of all files not current

in_index = "\\l".join([f"{fname} ({STATUSES_TO_SHOW_IN_INDEX[status]})" 
                            for fname, status 
                            in repo.status().items() 
                            if status in STATUSES_TO_SHOW_IN_INDEX])
if in_index:
    dot.node("index", f"index|{in_index}\\l", **NODE_STYLE_INDEX)


if not repo.head_is_unborn:
    # we have at least one commit; draw head

    if repo.head_is_detached:
        dot.node("HEAD", "HEAD", **NODE_STYLE_HEAD_DETACHED)
        # point to commit, and make sure we show that whole commit
        dot.edge("HEAD", sha(repo.head.target), **EDGE_STYLE_REF)
        add_commits(repo.head.peel().id)
    else:
        dot.node("HEAD", "HEAD", **NODE_STYLE_HEAD_ATTACHED)
        # point to branch
        dot.edge("HEAD", repo.head.resolve().shorthand, **EDGE_STYLE_REF)

# for each branch: create branch node, and gather all commits in branch

for branchname in repo.branches.remote:
    branch = repo.branches[branchname]
    dot.node(branchname, **NODE_STYLE_BRANCH_REMOTE)
    dot.edge(branchname, sha(branch.resolve().target), **EDGE_STYLE_REF)
    add_commits(branch.resolve().target)

for branchname in repo.branches.local:
    branch = repo.branches[branchname]
    dot.node(branchname, **NODE_STYLE_BRANCH_LOCAL)
    dot.edge(branchname, sha(branch.target), **EDGE_STYLE_REF)
    add_commits(branch.target)

# for every found commit, create node & edges to all parents of it

for commit in commits.values():
    csha = sha(commit)
    cmsg = (commit.message
              .split("\n")[0]         # only consider first line of commit msg
              .replace("&", "&amp;")  # symbols disallowed in graphviz labels
              .replace("<", "&lt;")
              .replace(">", "&gt;"))
    
    if ": " in cmsg:
        name, cmsg = cmsg.split(": ")
    else:
        name, cmsg = cmsg, " "

    cmsg = f'<font point-size="10" color="gray25"><i>{cmsg}</i></font>'
    sha_id = f'<font point-size="10" color="blue">{csha}</font>'

    label = f'<<b>{name}</b><br/>{cmsg}<br/>{sha_id}>'
    dot.node(csha, label)

    for i, parent in enumerate(commit.parents, 1):
        # only number parents if a merge commit, otherwise, it's just clutter
        if len(commit.parents) == 1:
            dot.edge(csha, sha(parent))
        else:
            dot.edge(csha, sha(parent), str(i), **EDGE_STYLE_MERGES)

# draw tags, pointing them to their commit

for refname in repo.references:
    if refname.startswith('refs/tags/'):
        ref = repo.lookup_reference(refname)
        dot.node(ref.shorthand)
        dot.edge(ref.shorthand, sha(ref.target), **EDGE_STYLE_REF)


# don't view; we want to render in Skim, not Apple Preview
dot.render('/tmp/g.dot', view=False)   

# Annoyingly, Skim doesn't reload on changes; force that
applescript.tell.app("Skim", 'open "tmp:g.dot.pdf"')
applescript.tell.app("Skim", """
tell document 1
  revert
end tell""")

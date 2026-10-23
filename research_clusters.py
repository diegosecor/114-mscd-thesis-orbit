"""Discover exploratory topic groups from full-dimensional thesis embeddings.

Spherical k-means uses cosine similarity, not PCA coordinates or catalogue tags.
Labels are extracted title terms, not generated claims about research quality.
"""
from collections import Counter
import math
import re

import numpy as np

STOP_WORDS = set("the a an and or of in on to for from with through using by as at into towards "
                 "design designing computational thesis research study approach framework system "
                 "based exploring exploration development new towards applications".split())


def cluster_profiles(ids, vectors, titles):
    """Return reproducible groups; empty and identical-vector corpora are valid.

    Sort by persistent ID, seed centers by farthest cosine distance, then refine
    normalized means. Group count is a heuristic (at most seven), not a finding.
    Labels summarize distinctive title vocabulary after clustering is complete.
    """
    if not ids:
        return {"membership": {}, "groups": [], "method": "spherical k-means"}
    order = sorted(range(len(ids)), key=lambda i: int(ids[i]))
    ids = [str(ids[i]) for i in order]
    titles = [titles[i] for i in order]
    matrix = np.asarray(vectors, dtype=float)[order]
    matrix /= np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
    count = min(7, max(1, round(math.sqrt(len(ids) / 2))))
    centers = [matrix[0]]
    for _ in range(1, count):
        distance = 1 - np.max(matrix @ np.asarray(centers).T, axis=1)
        candidate = int(np.argmax(distance))
        if distance[candidate] < 1e-10:
            break
        centers.append(matrix[candidate])
    centers = np.asarray(centers)
    previous = None
    for _ in range(80):
        assignments = np.argmax(matrix @ centers.T, axis=1)
        if previous is not None and np.array_equal(previous, assignments):
            break
        previous = assignments.copy()
        for index in range(len(centers)):
            members = matrix[assignments == index]
            if len(members):
                mean = members.mean(axis=0)
                centers[index] = mean / max(float(np.linalg.norm(mean)), 1e-12)
    terms = [set(re.findall(r"[a-z][a-z-]{2,}", title.lower())) - STOP_WORDS for title in titles]
    frequencies = Counter(term for words in terms for term in words)
    groups, membership = [], {}
    for index in sorted(set(assignments.tolist())):
        members = np.flatnonzero(assignments == index).tolist()
        weights = Counter(term for member in members for term in terms[member])
        keywords = sorted(weights, key=lambda term: (
            -weights[term] * math.log(1 + len(ids) / frequencies[term]), term))[:3]
        key = str(len(groups))
        member_ids = [ids[member] for member in members]
        groups.append({"id": key, "label": " / ".join(keywords) or "Untitled topic",
                       "keywords": keywords, "ids": member_ids, "count": len(members)})
        membership.update({member_id: key for member_id in member_ids})
    return {"membership": membership, "groups": groups, "method": "spherical k-means"}

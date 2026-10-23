"""Verify semantic groups without downloading a model or touching user data."""
import unittest
import numpy as np
from research_clusters import cluster_profiles


class ConstellationTests(unittest.TestCase):
    def test_empty_and_identical_vectors(self):
        self.assertEqual(cluster_profiles([], [], [])['groups'], [])
        result = cluster_profiles(['2', '1'], [[1, 0], [1, 0]], ['Timber robotics', 'Timber assembly'])
        self.assertEqual(len(result['groups']), 1)
        self.assertEqual(set(result['membership']), {'1', '2'})

    def test_groups_follow_vectors_and_ignore_input_order(self):
        ids = [str(index + 1) for index in range(8)]
        vectors = [[1, .01 * index, 0] for index in range(4)] + [[0, .01 * index, 1] for index in range(4)]
        titles = ['Timber robotic assembly'] * 4 + ['Immersive spatial sound'] * 4
        result = cluster_profiles(ids, vectors, titles)
        reversed_result = cluster_profiles(ids[::-1], vectors[::-1], titles[::-1])
        self.assertEqual(result, reversed_result)
        self.assertEqual(len(result['groups']), 2)
        self.assertEqual(result['membership']['1'], result['membership']['4'])
        self.assertNotEqual(result['membership']['1'], result['membership']['5'])
        self.assertEqual(sum(group['count'] for group in result['groups']), 8)
        self.assertTrue(all(group['keywords'] for group in result['groups']))

    def test_zero_vector_is_finite_and_covered(self):
        result = cluster_profiles(['1', '2'], np.zeros((2, 3)), ['A', 'B'])
        self.assertEqual(len(result['membership']), 2)

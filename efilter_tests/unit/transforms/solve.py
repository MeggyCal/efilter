# EFILTER Forensic Query Language
#
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
EFILTER test suite.
"""

__author__ = "Adam Sindelar <adamsh@google.com>"

from efilter import ast
from efilter import query as q

from efilter.protocols import superposition

from efilter.transforms import solve

from efilter_tests import mocks
from efilter_tests import testlib


class SolveTest(testlib.EfilterTestCase):
    def testQuery(self):
        """Get coverage test to shut up."""
        pass

    def testLiteral(self):
        self.assertEqual(
            solve.solve(q.Query("42"), {}, None).value,
            42)

    def testBinding(self):
        self.assertEqual(
            solve.solve(q.Query("foo"), {"foo": "bar"}, None).value,
            "bar")

    def testLet(self):
        self.assertEqual(
            solve.solve(
                q.Query("foo.bar"), {"foo": {"bar": "baz"}}, None).value,
            "baz")

    def testLetEach(self):
        self.assertEqual(
            solve.solve(
                q.Query("each Process.parent where (pid == 1)"),
                {"Process": {"parent": superposition.superposition(
                    mocks.Process(1, None, None),
                    mocks.Process(2, None, None))}},
                None).value,
            False)

    def testLetAny(self):
        self.assertEqual(
            solve.solve(
                q.Query("any Process.parent where (pid == 1)"),
                {"Process": {"parent": superposition.superposition(
                    mocks.Process(1, None, None),
                    mocks.Process(2, None, None))}},
                None).value,
            True)

    def testComponentLiteral(self):
        """This really isn't testable outside Rekall."""
        # TODO: This is a legacy piece of the AST that's going away soon.
        # Rekall, which currently relies on it, will be able to use IsInstance.

    def testIsInstance(self):
        self.assertEqual(
            solve.solve(
                q.Query("isa Process"),
                mocks.Process(None, None, None),
                mocks.MockApp()).value,
            True)

    def testComplement(self):
        self.assertEqual(
            solve.solve(
                q.Query("not pid"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            False)

    def testIntersection(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid and not pid"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            False)

    def testUnion(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid or not pid"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            True)

    def testSum(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid + 10 + 20"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            31)

    def testDifference(self):
        self.assertEqual(
            solve.solve(
                q.Query("(10 - pid) + 5"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            14)

    def testProduct(self):
        self.assertEqual(
            solve.solve(
                q.Query("5 * 5 * 5"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            125)

    def testQuotient(self):
        self.assertEqual(
            solve.solve(
                q.Query("10.0 / 4"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            2.5)

    def testEquivalence(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid == 1"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            True)

    def testMembership(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid in (1, 2)"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            True)

    def testRegexFilter(self):
        self.assertTrue(
            solve.solve(
                q.Query("name =~ 'ini.*'"),
                mocks.Process(1, "initd", None),
                mocks.MockApp()).value)

    def testStrictOrderedSet(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid > 2"),
                mocks.Process(1, None, None),
                mocks.MockApp()).value,
            False)

    def testPartialOrderedSet(self):
        self.assertEqual(
            solve.solve(
                q.Query("pid >= 2"),
                mocks.Process(2, None, None),
                mocks.MockApp()).value,
            True)

    def testContainmentOrder(self):
        self.assertEqual(
            solve.solve(
                q.Query(
                    # This guy doesn't (yet) have syntax in any of the parsers.
                    ast.ContainmentOrder(
                        ast.Literal((1, 2)),
                        ast.Literal((1, 2, 3)))),
                None, None).value,
            True)

    def testMatchTrace(self):
        """Make sure that matching branch is recorded where applicable."""
        result = solve.solve(
            q.Query("pid == 1 or pid == 2 or pid == 3"),
            mocks.Process(2, None, None),
            mocks.MockApp())

        self.assertEquals(
            q.Query(result.branch),
            q.Query("pid == 2"))

    def testDestructuring(self):
        result = solve.solve(
            q.Query("Process.pid == 1"), {"Process": {"pid": 1}}, None)
        self.assertEqual(True, result.value)

        # Using a let-any form should succeed even if there is only one linked
        # object.
        result = solve.solve(
            q.Query("any Process.parent where (Process.pid == 1 or "
                    "Process.command == 'foo')"),
            {"Process": {"parent": {"Process": {"pid": 1}}}},
            None)
        self.assertEqual(True, result.value)

    def testTypeOps(self):
        result = solve.solve(
            q.Query("isa Process"),
            mocks.Process(None, None, None),
            mocks.MockApp())

        self.assertEqual(True, result.value)
#! /usr/bin/env python3
import unittest
from hypothesis import given, example, reject
from hypothesis.strategies import dictionaries, text

from substitution import Substitution


class TestSubstitution(unittest.TestCase):
    @given(dictionaries(text(), text()))
    def test_creating_substitution(self, d):
        Substitution(d)

    @given(dictionaries(text(), text()), dictionaries(text(), text()))
    @example({'a': 'b'}, {'b': 'a'})
    @example({'a': 'b'}, {'a': 'c'})
    def test_combining_substitution(self, d1, d2):
        self.assertIsNone(
            Substitution({'a': 'b'}) & Substitution({'b': 'a'})
        )
        self.assertIsNone(
            Substitution({'a': 'b'}) & Substitution({'a': 'c'})
        )
        Substitution(d1) & Substitution(d2)

    @given(dictionaries(text(), text()), dictionaries(text(), text()))
    def test_update(self, d1, d2):
        try:
            Substitution(d1).update(Substitution(d2))
        except ValueError as e:
            excpected = [
                'Substitution disagree',
                'Circular substitution'
            ]
            for message in excpected:
                if e.args[0][:len(message)] == message:
                    reject()
                    break
            else:
                raise e
        self.assertRaises(
            ValueError,
            lambda: Substitution({'a': 'b'}).update(
                Substitution({'b': 'a'})
            )
        )


if __name__ == '__main__':
    unittest.main()

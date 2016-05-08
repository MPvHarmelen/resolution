#! /usr/bin/env python3
import unittest
from hypothesis import given, example, reject
from hypothesis.strategies import dictionaries, text

from substitution import Substitution
from sentence import Variable, Predicate, And, Or, Not, IFF, ForAll


class TestSubstitution(unittest.TestCase):
    def test_create(self):
        self.assertEqual(Substitution({'a': 'a'}), Substitution())
        self.assertEqual(
            Substitution({'a': 'b', 'b': 'c'}),
            Substitution({'a': 'c', 'b': 'c'}),
        )

    @given(dictionaries(text(), text()))
    def test_hyp_create(self, d):
        try:
            Substitution(d)
        except ValueError as e:
            excpected = [
                # 'Substitutions disagree',
                'Circular substitution'
            ]
            for message in excpected:
                if e.args[0][:len(message)] == message:
                    reject()
                    break
            else:
                raise e

    def test_combine(self):
        self.assertIsNone(
            Substitution({'a': 'b'}) & Substitution({'b': 'a'})
        )
        self.assertIsNone(
            Substitution({'a': 'b'}) & Substitution({'a': 'c'})
        )

    @given(dictionaries(text(), text()), dictionaries(text(), text()))
    @example({'a': 'b'}, {'b': 'a'})
    @example({'a': 'b'}, {'a': 'c'})
    def test_hyp_combine(self, d1, d2):
        try:
            s1 = Substitution(d1)
            s2 = Substitution(d2)
        except ValueError as e:
            excpected = [
                # 'Substitutions disagree',
                'Circular substitution'
            ]
            for message in excpected:
                if e.args[0][:len(message)] == message:
                    reject()
                    break
            else:
                raise e
        s1 & s2

    def test_update(self):
        self.assertRaises(
            ValueError,
            lambda: Substitution({'a': 'b'}).update(
                Substitution({'b': 'a'})
            )
        )

    @given(dictionaries(text(), text()), dictionaries(text(), text()))
    def test_hyp_update(self, d1, d2):
        try:
            Substitution(d1).update(Substitution(d2))
        except ValueError as e:
            excpected = [
                'Substitutions disagree',
                'Circular substitution'
            ]
            for message in excpected:
                if e.args[0][:len(message)] == message:
                    reject()
                    break
            else:
                raise e

    def test_substitue(self):
        s = Substitution({'a': 'a', 'b': 'c'})
        self.assertEqual(s['a'], 'a')
        self.assertEqual(s['b'], 'c')

        # Don't touch unknown objects
        self.assertEqual(s['e'], 'e')


class TestSentence(unittest.TestCase):
    def test_substitution(self):
        x = Variable('x')
        self.assertEqual(
            Predicate('Exists', x).substitute(Substitution({x: 's'})),
            Predicate('Exists', 's')
        )

    def test_simplified(self):
        x = Variable('x')
        happy = Predicate('Happy', x)
        notunhappy = Not(Predicate('Unhappy', x))
        self.assertEqual(
            ForAll(x, IFF(happy, notunhappy)).simplified(),
            ForAll(
                x,
                And(Or(Not(happy), notunhappy), Or(Not(notunhappy), happy))
            )
        )

    def test_negate_inwards(self):
        x = Variable('x')
        happy = Predicate('Happy', x)
        self.assertEqual(
            ForAll(
                x,
                Not(IFF(happy, Not(happy)))
            ).simplified().negate_inwards(),
            ForAll(
                x,
                Or(And(Not(happy), Not(happy)), And(happy, happy))
            )
        )


if __name__ == '__main__':
    unittest.main()

#! /usr/bin/env python3
import unittest
from hypothesis import given, example, reject
from hypothesis.strategies import dictionaries, text

from substitution import Substitution
from sentence import Variable, Function, Predicate, And, Or, Not, IFF, ForAll
from sentence import Exists


class TestSubstitution(unittest.TestCase):

    def test_create(self):
        a, b, c = Variable('a'), Variable('b'), Variable('c')
        self.assertEqual(
            Substitution({a: a}),
            Substitution()
        )
        s = Substitution()
        s[a] = c
        s[b] = c
        self.assertEqual(s, Substitution({a: c, b: c}))
        self.assertEqual(
            Substitution({a: b, b: c}),
            Substitution({a: c, b: c}),
        )
        self.assertEqual(
            len(Substitution({a: b, b: a})),
            1
        )
        self.assertRaises(
            ValueError,
            lambda: Substitution({a: Function('F', a)})
        )
        self.assertRaises(
            ValueError,
            lambda: Substitution({a: Function('F', b), b: Function('F', a)})
        )
        self.assertEqual(
            Substitution({a: Function('F', b), b: 'x'}),
            Substitution({a: Function('F', 'x'), b: 'x'})
        )

    @given(dictionaries(text(), text()))
    def test_hyp_create(self, d):
        s = Substitution()
        for key, value in list(d.items()):
            del d[key]
            key = Variable(key)
            d[key] = s[key] = value
        self.assertEqual(s, Substitution(d))

    def test_combine(self):
        a, b, c = Variable('a'), Variable('b'), Variable('c')
        self.assertEqual(
            len(Substitution({a: b}) & Substitution({b: a})),
            1
        )
        self.assertIsNone(
            Substitution({a: b}) & Substitution({a: c})
        )

    a, b, c = Variable('a'), Variable('b'), Variable('c')

    # @given(dictionaries(text(), text()), dictionaries(text(), text()))
    # @example({a: b}, {b: a})
    # @example({a: b}, {a: c})
    # def test_hyp_combine(self, d1, d2):
    #     try:
    #         s1 = Substitution(d1)
    #         s2 = Substitution(d2)
    #     except ValueError as e:
    #         excpected = [
    #             # 'Substitutions disagree',
    #             'Circular substitution'
    #         ]
    #         for message in excpected:
    #             if e.args[0][:len(message)] == message:
    #                 reject()
    #                 break
    #         else:
    #             raise e
    #     s1 & s2

    # def test_update(self):
    #     a, b = Variable('a'), Variable('b')
    #     self.assertRaises(
    #         ValueError,
    #         lambda: Substitution({a: b}).update(
    #             Substitution({b: a})
    #         )
    #     )

    # @given(dictionaries(text(), text()), dictionaries(text(), text()))
    # def test_hyp_update(self, d1, d2):
    #     try:
    #         Substitution(d1).update(Substitution(d2))
    #     except ValueError as e:
    #         excpected = [
    #             'Substitutions disagree',
    #             'Circular substitution'
    #         ]
    #         for message in excpected:
    #             if e.args[0][:len(message)] == message:
    #                 reject()
    #                 break
    #         else:
    #             raise e

    def test_substitue(self):
        a, b, c = Variable('a'), Variable('b'), Variable('c')
        s = Substitution({a: a, b: c})
        self.assertEqual(s[a], a)
        self.assertEqual(s[b], c)

        # Don't touch unknown objects
        self.assertEqual(s['e'], 'e')


class TestSentence(unittest.TestCase):
    def test_substitution(self):
        x = Variable('x')
        y = Variable('y')
        self.assertEqual(
            Exists(
                y,
                Predicate('Equals', x, y)
            ).substitute(Substitution({x: 's'})),
            Exists(
                y,
                Predicate('Equals', 's', y)
            )
        )
        self.assertEqual(
            Exists(
                y,
                Predicate('Equals', Function('F', x), y)
            ).substitute(Substitution({x: 's'})),
            Exists(
                y,
                Predicate('Equals', Function('F', 's'), y)
            )
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
                Or(And(Not(happy)), And(happy))
            )
        )

    def test_cleaned(self):
        x = Variable('x')
        happy = Predicate('Happy', x)
        self.assertEqual(
            ForAll(
                x,
                Not(IFF(happy, Not(happy)))
            ).simplified().negate_inwards().cleaned(),
            ForAll(
                x,
                Or(Not(happy), happy)
            )
        )

    def test_unification(self):
        x = Variable('x')
        y = Variable('y')
        happyx = Predicate('Happy', x)
        angryx = Predicate('Angry', x)
        happyf = Predicate('Happy', Function('F', y))
        self.assertIsNone(
            angryx.unify(happyx)
        )
        self.assertEqual(happyx.unify(happyf), happyf.unify(happyx))
        self.assertEqual(
            happyx.unify(happyf),
            Substitution({x: Function('F', y)})
        )

    def test_contains(self):
        self.assertIn(
            'a',
            Predicate('Happy', 'a')
        )
        self.assertIn(
            'a',
            Predicate('Happy', Function('F', 'a'))
        )
        self.assertNotIn(
            'b',
            Predicate('Happy', 'a')
        )
        self.assertNotIn(
            'Happy',
            Predicate('Happy', 'a')
        )

if __name__ == '__main__':
    unittest.main()

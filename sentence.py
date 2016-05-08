from substitution import Substitution
from util import forgiving_join


class Variable(object):
    """
    A representation for a variable.

    The name is merely for humans. Two Variable objects x and y are only
    considered equal when x is y.
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "$" + str(self.name)


class Sentence(object):
    def __init__(self):
        self.content = None

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.content == other.content

    def __hash__(self):
        return hash(self.content) + hash(type(self))

    def substitute(self, subst):
        return type(self)(*[sentence(subst) for sentence in self.content])

    def copy(self):
        return type(self)(*self.content)

    def simplified(self):
        """
        Get a logical equivalent copy of this sentence using only And, Or, Not,
        Quantifier and Predicate.
        """
        return type(self)(*(cont.simplified() for cont in self.content))

    def cnf(self):
        """Convert sentence to conjunctive normal form"""
        standardized = self.simplified().negate_inwards()
        # Skolemize
        # Drop universal quantifiers
        # Distribute And over Or


class Quantifier(Sentence):
    SYMBOL = None

    def __init__(self, variable, sentence):
        self.content = (variable, sentence)

    def __repr__(self):
        return "{} {} [{}]".format(self.SYMBOL, self.content[0],
                                   self.content[1])

    def simplified(self):
        """
        Get a logical equivalent copy of this sentence using only And, Or, Not,
        Quantifier and Predicate.
        """
        return type(self)(self.content[0], self.content[1].simplified())

    def negate_inwards(self, negate, negative, positive):
        """
        Negate this sentence, pushing occurrences of Not inwards until they
        hit a Predicate.
        """
        if negate:
            return negative(
                self.content[0],
                self.content[1].negate_inwards(True)
            )
        else:
            return positive(
                self.content[0],
                self.content[1].negate_inwards(False)
            )


class ForAll(Quantifier):
    SYMBOL = "∀"

    def negate_inwards(self, negate=False):
        """
        Negate this sentence, pushing occurrences of Not inwards until they
        hit a Predicate.
        """
        return super(ForAll, self).negate_inwards(negate, Exists, ForAll)


class Exists(Quantifier):
    SYMBOL = "∃"

    def negate_inwards(self, negate=False):
        """
        Negate this sentence, pushing occurrences of Not inwards until they
        hit a Predicate.
        """
        return super(Exists, self).negate_inwards(negate, ForAll, Exists)


class IFF(Sentence):
    def __init__(self, formula1, formula2):
        self.content = frozenset((formula1, formula2))
        # The following happens when (formula1 is formula2) is True
        if len(self.content) == 1:
            self.content = (formula1, formula2)

    def __repr__(self):
        return "({} <=> {})".format(*self.content)

    def simplified(self):
        cont = tuple(self.content)
        return And(
            Implies(*cont).simplified(),
            Implies(*reversed(cont)).simplified()
        )

    # Not needed either
    # def unify(self, other):
    #     if isinstance(other, IFF):
    #         selfc = tuple(self.content)
    #         otherc = tuple(other.content)
    #         return selfc[0].unify(otherc[0]) & \
    #             selfc[1].unify(otherc[1]) or \
    #             selfc[0].unify(otherc[1]) & \
    #             selfc[1].unify(otherc[0])


class Implies(Sentence):
    def __init__(self, formula1, formula2):
        self.content = tuple((formula1, formula2))

    def __repr__(self):
        return "({} => {})".format(*self.content)

    def simplified(self):
        return Or(
            Not(self.content[0].simplified()),
            self.content[1].simplified()
        )

    # Not needed either
    # def unify(self, other):
    #     if isinstance(other, Implies):
    #         return self.content[0].unify(other.content[0]) & \
    #             self.content[1].unify(other.content[1])


class AssociativeCommutativeBinaryOperator(Sentence):
    CONNECTIVE = None

    def __init__(self, formula1, *formulas):
        formulas = (formula1, ) + formulas
        self.content = frozenset(formulas)

    def __repr__(self):
        return "(" + forgiving_join(self.CONNECTIVE, self.content) + ")"

    def negate_inwards(self, negate, negative, positive):
        if negate:
            return negative(
                *[cont.negate_inwards(True) for cont in self.content]
            )
        else:
            return positive(
                *[cont.negate_inwards(False) for cont in self.content]
            )

    # Not needed :D
    # def unify(self, other):
    #     if type(self) == type(other):
    #         selfc, otherc = set(self.content), set(other.content)
    #         substitution = Substitution()
    #         for selfsentence in selfc:
    #             for othersentence in otherc:
    #                 subst = selfsentence.unify(othersentence)
    #                 if subst:
    #                     otherc.pop(othersentence) # Not really correct
    #                     break
    #             else:
    #                 return
    #             substitution |= subst
    #         return substitution


class And(AssociativeCommutativeBinaryOperator):
    CONNECTIVE = " ∧ "

    def negate_inwards(self, negate=False):
        """
        Negate this sentence, pushing occurrences of Not inwards until they
        hit a Predicate.
        """
        return super(And, self).negate_inwards(negate, Or, And)


class Or(AssociativeCommutativeBinaryOperator):
    CONNECTIVE = " ∨ "

    def negate_inwards(self, negate=False):
        """
        Negate this sentence, pushing occurrences of Not inwards until they
        hit a Predicate.
        """
        return super(Or, self).negate_inwards(negate, And, Or)


class Not(Sentence):
    def __init__(self, sentence):
        self.content = (sentence, )

    def __repr__(self):
        return "¬{}".format(self.content[0])

    def unify(self, other):
        if isinstance(other, Not):
            return self.content[0].unify(other.content[0])

    def negate_inwards(self, negate=False):
        return self.content[0].negate_inwards(not negate)

    # def cnf(self):
    #     if isinstance(self.content, Not):
    #         # ¬¬A = A
    #         return self.content.content.cnf()
    #     elif isinstance(self.content, And):
    #         ...
    #     else:
    #         return self.content.cnf()


class Predicate(Sentence):
    def __init__(self, name, *arguments):
        self.content = tuple((name,) + arguments)

    def substitute(self, substitution):
        return Predicate(*(substitution[cont] for cont in self.content))

    def __repr__(self):
        return "{}({})".format(
            self.content[0],
            forgiving_join(", ", self.content[1:])
        )

    def unify(self, other):
        if isinstance(other, Predicate) and \
           self.content[0] == other.content[0] and \
           len(self.content) == len(other.content):
            substitution = Substitution()
            for selfc, otherc in zip(self.content[1:], other.content[1:]):
                if selfc != otherc:
                    if isinstance(selfc, Variable):
                        substitution[selfc] = otherc
                    elif isinstance(otherc, Variable):
                        substitution[otherc] = selfc
                    else:
                        return None
            return substitution

    def simplified(self):
        return self.copy()

    def negate_inwards(self, negate=False):
        if negate:
            return Not(self.copy())
        else:
            return self.copy()

    # def cnf(self):
    #     return self

from functools import wraps

import substitution as sub
from util import forgiving_join

# To do:
#   - Fix substitution:
#       - substituting a quantified variable
#       - see comments in substitution.py
#   - Think about whether I want to add Function functionality
#   - Add XOR, NOR


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


def recursive(f):
    @wraps(f)
    def inner(self, *args, **kwargs):
        return self.copy(
            f(sentence, *args, **kwargs)
            for sentence in self.content
        )
    return inner


class RecursiveObject(object):
    name = None
    content = None
    CONNECTIVE = None

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
            self.content == other.content and \
            self.name == other.name

    def __hash__(self):
        return hash(type(self)) + hash(self.name) + hash(self.content)

    def __contains__(self, something):
        if self == something:
            return True
        else:
            return any(
                something in cont if isinstance(cont, RecursiveObject)
                else something == cont
                for cont in self.content
            )

    def __repr__(self):
        rep = "({})".format(
            forgiving_join(self.CONNECTIVE, self.content)
        )
        if self.name is not None:
            rep = self.name + rep
        return rep

    def copy(self, content=None):
        content = self.content if content is None else content
        if self.name is None:
            return type(self)(*content)
        else:
            return type(self)(self.name, *content)


class Function(RecursiveObject):
    CONNECTIVE = ', '

    def __init__(self, name, *arguments):
        self.name = name
        self.content = arguments

    def free_variables(self):
        return {x for x in self.content if isinstance(x, Variable)} | \
            {x for s in (f.free_variables() for f in self.content
             if isinstance(f, Function)) for x in s}

    def substituted(self, dic):
        """
        Apply a substitution to this Function AND return whether anything was
        substituted.

        The substitution is handled as if it's a dict.
        """
        new_content = []
        substituted = False
        for cont in self.content:
            if isinstance(cont, Variable) and cont in dic:
                substituted = True
                cont = dic[cont]
            elif isinstance(cont, Function):
                cont, newsub = cont.substituted(dic)
                substituted |= newsub
            new_content.append(cont)
        return self.copy(new_content), substituted

    def unify(self, other):
        if isinstance(other, Function) and \
                self.name == other.name and \
                len(self.content) == len(other.content):
            substitution = sub.Substitution()
            for selfc, otherc in zip(self.content, other.content):
                if selfc != otherc:
                    if isinstance(selfc, Variable):
                        substitution[selfc] = otherc
                    elif isinstance(otherc, Variable):
                        substitution[otherc] = selfc
                    else:
                        return None
            return substitution


class Sentence(RecursiveObject):
    def free_variables(self):
        """Get all free variables of this sentence"""
        return {x for c in self.content for x in c.free_variables()}

    @recursive
    def substitute(self, subst):
        """Apply a substitution to this Sentence"""
        return self.substitute(subst)

    @recursive
    def simplified(self):
        """
        Get a logical equivalent copy of this sentence using only And, Or, Not,
        Quantifier and Predicate.
        """
        return self.simplified()

    @recursive
    def cleaned(self):
        """Remove any meaningless parts of this Sentence"""
        return self.cleaned()

    def cnf(self):
        """Convert sentence to conjunctive normal form"""
        standardized = self.simplified().negate_inwards()
        # Skolemize
        # Drop universal quantifiers
        # Distribute And over Or


class Quantifier(Sentence):
    SYMBOL = None

    def __init__(self, variable, sentence):
        self.name = variable
        self.content = (sentence, )

    def __repr__(self):
        return "{} {} [{}]".format(self.SYMBOL, self.name, self.content[0])

    def free_variables(self):
        frees = super(Quantifier, self).free_variables()
        frees.discard(self.name)
        return frees

    def substitute(self, subst):
        """
        Apply a substitution to this sentence
        """
        if self.name in subst:
            raise ValueError(
                "Can't substitute a quantified variable. ({}, {})"
                .format(self, subst)
            )
        return super(Quantifier, self).substitute(subst)

    def negate_inwards(self, negate, negative, positive):
        """
        Negate this sentence, pushing occurrences of Not inwards until they
        hit a Predicate.
        """
        if negate:
            return negative(
                self.name,
                self.content[0].negate_inwards(True)
            )
        else:
            return positive(
                self.name,
                self.content[0].negate_inwards(False)
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
    CONNECTIVE = ' <=> '

    def __init__(self, formula1, formula2):
        self.content = frozenset((formula1, formula2))
        # The following happens when (formula1 is formula2) is True
        if len(self.content) == 1:
            self.content = (formula1, formula2)

    def simplified(self):
        cont = tuple(self.content)
        return And(
            Implies(*cont).simplified(),
            Implies(*reversed(cont)).simplified()
        )


class Implies(Sentence):
    CONNECTIVE = ' => '

    def __init__(self, formula1, formula2):
        self.content = (formula1, formula2)

    def simplified(self):
        return Or(
            Not(self.content[0].simplified()),
            self.content[1].simplified()
        )


class AssociativeCommutativeBinaryOperator(Sentence):
    def __init__(self, formula1, *formulas):
        formulas = (formula1, ) + formulas
        self.content = frozenset(formulas)

    def simplified(self):
        # if len(self.content) == 1:
        #     return next(iter(self.content)).simplified()
        # else:
        return super(
            AssociativeCommutativeBinaryOperator,
            self
        ).simplified()

    def cleaned(self):
        if len(self.content) == 1:
            return next(iter(self.content)).cleaned()
        else:
            return super(AssociativeCommutativeBinaryOperator, self).cleaned()

    def negate_inwards(self, negate, negative, positive):
        # if len(self.content) == 1:
        #     # Delete myself
        #     return next(iter(self.content)).negate_inwards(negate)
        if negate:
            return negative(
                *[cont.negate_inwards(True) for cont in self.content]
            )
        else:
            return positive(
                *[cont.negate_inwards(False) for cont in self.content]
            )


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
    CONNECTIVE = ', '

    def __init__(self, name, *arguments):
        self.name = name
        self.content = arguments

    def unify(self, other):
        if isinstance(other, Predicate) and \
                self.name == other.name and \
                len(self.content) == len(other.content):
            substitution = sub.Substitution()
            for selfc, otherc in zip(self.content, other.content):
                if selfc != otherc:
                    if isinstance(selfc, Variable):
                        substitution[selfc] = otherc
                    elif isinstance(otherc, Variable):
                        substitution[otherc] = selfc
                    elif isinstance(selfc, Function) and \
                            isinstance(otherc, Function):
                        substitution &= selfc.unify(otherc)
                    else:
                        return None
            return substitution

    free_variables = Function.free_variables

    def substitute(self, substitution):
        return self.copy(
            cont.substituted(substitution)[0] if isinstance(cont, Function)
            else substitution[cont]
            for cont in self.content
        )

    def simplified(self):
        return self.copy()

    def cleaned(self):
        return self.copy()

    def negate_inwards(self, negate=False):
        if negate:
            return Not(self.copy())
        else:
            return self.copy()

    # def cnf(self):
    #     return self

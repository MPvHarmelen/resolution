from substitution import Substitution


def forgiving_join(seperator, iterator):
    return seperator.join(str(it) for it in iterator)


class Variable(object):
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

    def __call__(self, subst):
        return type(self)(*[sentence(subst) for sentence in self.content])


class AssociativeCommutativeBinaryOperator(Sentence):
    CONNECTIVE = None

    def __init__(self, formula1, formula2, *formulas):
        formulas = (formula1, formula2) + formulas
        self.content = frozenset(formulas)

    def __repr__(self):
        return "(" + forgiving_join(self.CONNECTIVE, self.content) + ")"

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


class Or(AssociativeCommutativeBinaryOperator):
    CONNECTIVE = " ∨ "


class IFF(Sentence):
    def __init__(self, formula1, formula2):
        self.content = frozenset((formula1, formula2))
        # The following happens when (formula1 is formula2) is True
        if len(self.content) == 1:
            self.content = (formula1, formula2)

    def __repr__(self):
        return "(" + forgiving_join(" <=> ", self.content) + ")"

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

    # Not needed either
    # def unify(self, other):
    #     if isinstance(other, Implies):
    #         return self.content[0].unify(other.content[0]) & \
    #             self.content[1].unify(other.content[1])


class Not(Sentence):
    def __init__(self, formula):
        self.content = formula

    def __repr__(self):
        return "¬" + str(self.content)

    def unify(self, other):
        if isinstance(other, Not):
            return self.content.unify(other.content)


class Predicate(Sentence):
    def __init__(self, name, *arguments):
        self.content = tuple((name,) + arguments)

    def __repr__(self):
        return str(self.content[0]) + "(" + forgiving_join(
            ", ", self.content[1:]
        ) + ")"

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

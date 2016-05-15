import sentence
# To do:
#   - Think again about circular substitutions (it shouldn't be a problem,
#     because both are variables, just arbitrarily choose one)


class Substitution(dict):
    def __init__(self, *args, **kwargs):
        super(Substitution, self).__init__(*args, **kwargs)
        for key, value in list(self.items()):
            if key == value:
                del self[key]
        self.update()

    def __setitem__(self, key, value):
        if key != value:
            self.update({key: value})

    def __getitem__(self, key):
        return super(Substitution, self).get(key, key)

    def __bool__(self):
        return True

    def __and__(self, other):
        if isinstance(other, Substitution):
            try:
                self.update(other)
                return self
            except ValueError:
                return
        elif other is None:
            return
        else:
            return NotImplemented

    def update(self, *args, **kwargs):
        new = dict(self)
        new.update(*args, **kwargs)
        for key, value in self.items():     # I don't like always checking
            if not isinstance(key, sentence.Variable):
                raise ValueError("Only Variable may be substituted")
            if new[key] != value:
                raise ValueError("Substitutions disagree: {} is {} and"
                                 " {}".format(key, value, new[key]))
        new = self._compress(new)
        self.clear()
        super(Substitution, self).update(new)

    @staticmethod
    def _compress(dic):
        substituted = True
        while substituted:
            substituted = False
            for key, value in list(dic.items()):
                if key == value:
                    # Choosing either one of two variables isn't a problem
                    del dic[key]
                elif isinstance(value, sentence.Function):
                    if key in value:
                        # This is really a circular substitution
                        raise ValueError("Circular substitution")
                    else:
                        # substitute it
                        dic[key], subst = value.substituted(dic)
                        substituted |= subst
                elif value in dic:
                    substituted = True
                    dic[key] = dic[value]
        return dic

    def copy(self):
        return Substitution(self)

    def __repr__(self):
        return "Substitution(" + super(Substitution, self).__repr__() + ")"

    # def __or__(self, other):
    #     if isinstance(other, Substitution):
    #         ...
    #     elif other is None:
    #         return self
    #     else:
    #         return NotImplemented

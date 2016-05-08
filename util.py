def forgiving_join(seperator, iterator):
    """
    A join function that is more forgiving about the type of objects the
    iterator returns.
    """
    return seperator.join(str(it) for it in iterator)

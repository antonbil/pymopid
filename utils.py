def remove_slash_at_end(s):
    if s[-1:] == "/":
        s = s[:-1]
    return s


def remove_slash_at_start(s):
    if s[:1] == "/":
        s = s[1:]
    return s

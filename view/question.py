from clint.textui import puts, colored, indent, prompt
from view.element import Element


Q_MARK = '?'
TWO_DOTS = ':'


class Question(Element):

    def __init__(self, question: str, end_quote, valid_answer_check):
        super().__init__()

        self.question = question
        self.end_quote = end_quote
        self.valid_answer_check = valid_answer_check

    def run(self, page):
        is_valid = False
        val = None
        with indent(len(page.quote) + 1, quote=page.quote):
            while not is_valid:
                puts(colored.blue(self.question + self.end_quote), newline=False)
                val = input(' ')
                is_valid = self.valid_answer_check(val)
                if not is_valid:
                    puts(colored.red('INVALID NAME. This name already exist or contains invalid characters'))
        return val

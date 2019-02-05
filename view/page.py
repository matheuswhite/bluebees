from view.element import Element
from clint.textui import puts, colored

back_cmd = '/back'
exit_cmd = '/exit'


class Page:

    def __init__(self, arguments, quote='>>>'):
        self.arguments = arguments
        self.quote = quote
        self.element_results = {}
        self.last_result = None
        self.elements = []

    def __iadd__(self, other: Element):
        other.index = len(self.elements)
        self.elements.append(other)
        return self

    def run(self):
        x = 0
        while x < len(self.elements):
            result = self.elements[x].run(self)
            if result == back_cmd and x > 0:
                x -= 1
            elif result == back_cmd and x == 0:
                break
            elif result == exit_cmd:
                return
            else:
                x += 1
                self.last_result = result
                self.element_results[x] = result
        # puts(colored.green(f'Results: {self.element_results}'))

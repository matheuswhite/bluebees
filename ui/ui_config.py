from PyInquirer import style_from_dict, Token


default_style = style_from_dict({
    Token.Separator: '#6C6C6C',
    Token.QuestionMark: '#0080FF bold',
    Token.Selected: '#FF9D00 bold',
    Token.Pointer: '#FF9D00 bold',
    Token.Instruction: '#0080FF',
    Token.Answer: '#FF9D00',
    Token.Question: '#0080FF bold',
})
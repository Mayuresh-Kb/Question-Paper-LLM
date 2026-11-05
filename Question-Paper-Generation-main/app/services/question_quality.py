"""Conservative checks that stop obviously broken extracted questions.

These checks verify readable structure; academic correctness still requires the
teacher review shown in the product.
"""
import re


WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
BROKEN_RUN = re.compile(r"(?:[|~_^`]{4,}|\ufffd|\x00)")


def question_quality_issues(value: str) -> list[str]:
    text = value.strip()
    issues = []
    words = WORD.findall(text)
    visible = [char for char in text if not char.isspace()]
    letters = sum(char.isalpha() for char in visible)

    if len(text) < 12 or len(words) < 3:
        issues.append("Question text is too short to be meaningful.")
    if visible and letters / len(visible) < 0.25:
        issues.append("Question text contains too many unreadable symbols.")
    if BROKEN_RUN.search(text):
        issues.append("Question text contains broken OCR characters.")
    if re.search(r"\b(?:and|or|the|of|to|with|following|below|given)\s*[.?:-]*$", text, re.I):
        issues.append("Question text appears incomplete.")
    for opening, closing, name in (("(", ")", "parentheses"), ("[", "]", "brackets"), ("{", "}", "braces")):
        if abs(text.count(opening) - text.count(closing)) > 1:
            issues.append(f"Question text has unbalanced {name}.")
    return issues

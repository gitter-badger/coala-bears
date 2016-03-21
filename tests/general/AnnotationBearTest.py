from queue import Queue
import unittest

from bears.general.AnnotationBear import AnnotationBear
from coalib.results.SourceRange import SourceRange
from coalib.results.AbsolutePosition import AbsolutePosition
from coalib. results.HiddenResult import HiddenResult
from coalib.settings.Section import Section
from coalib.settings.Setting import Setting
from tests.LocalBearTestHelper import execute_bear


class AnnotationBearTest(unittest.TestCase):

    def setUp(self):
        self.section1 = Section("")
        self.section1.append(Setting('language', 'python3'))
        self.section1.append(Setting('language_family', 'python3'))
        self.uut1 = AnnotationBear(self.section1, Queue())
        self.section2 = Section("")
        self.section2.append(Setting('language', 'c'))
        self.section2.append(Setting('language_family', 'c'))
        self.uut2 = AnnotationBear(self.section2, Queue())

    def test_single_line_string(self):
        text = ["'from start till the end with #comments'\n", ]
        compare = (SourceRange.from_absolute_position(
                                    "F",
                                    AbsolutePosition(text, 0),
                                    AbsolutePosition(text, len(text[0])-2)),)
        with execute_bear(self.uut1, "F", text) as result:
            self.assertEqual(result[0].contents, compare)
            self.assertEqual(result[1].contents, ())

    def test_multiline_string(self):
        text = ["'''multiline string, #comment within it'''\n"]
        compare = (SourceRange.from_absolute_position(
                        "F",
                        AbsolutePosition(text, 0),
                        AbsolutePosition(text, len(text[0])-2)),)
        with execute_bear(self.uut1, "F", text) as result:
            self.assertEqual(result[0].contents, compare)
            self.assertEqual(result[1].contents, ())

    def test_single_line_comment(self):
        text = ["some #coment with 'string'\n", "and next line"]
        compare = (SourceRange.from_absolute_position(
                                    "F",
                                    AbsolutePosition(text, text[0].find('#')),
                                    AbsolutePosition(text, len(text[0])-1)),)
        with execute_bear(self.uut1, "F", text) as result:
            self.assertEqual(result[0].contents, ())
            self.assertEqual(result[1].contents, compare)

    def test_multiline_comment(self):
        text = ["some string /*within \n", "'multiline comment'*/"]
        compare = (SourceRange.from_absolute_position(
                                "F",
                                AbsolutePosition(text, text[0].find('/*')),
                                AbsolutePosition(text, len(''.join(text))-1)),)
        with execute_bear(self.uut2, "F", text) as result:
            self.assertEqual(result[0].contents, ())
            self.assertEqual(result[1].contents, compare)

    def test_string_with_comments(self):
        text = ["some #comment\n", "with 'string' in  next line"]
        comment_start = text[0].find('#')
        comment_end = len(text[0])-1
        string_start = ''.join(text).find("'")
        string_end = ''.join(text).find("'", string_start + 1)
        compare = [(SourceRange.from_absolute_position(
                                "F",
                                AbsolutePosition(text, string_start),
                                AbsolutePosition(text, string_end)),),
                   (SourceRange.from_absolute_position(
                                "F",
                                AbsolutePosition(text, comment_start),
                                AbsolutePosition(text, comment_end)),)]
        with execute_bear(self.uut1, "F", text) as result:
            self.assertEqual(result[0].contents, compare[0])
            self.assertEqual(result[1].contents, compare[1])

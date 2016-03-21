from coalib.parsing.StringProcessing.Core import (search_for,
                                                  search_in_between,
                                                  unescaped_search_in_between)
from coalib.bearlib.languages.LanguageDefinition import LanguageDefinition
from coalib.bears.LocalBear import LocalBear
from coalib.results.HiddenResult import HiddenResult
from coalib.results.SourceRange import SourceRange
from coalib.results.AbsolutePosition import AbsolutePosition


class AnnotationBear(LocalBear):

    def run(self, filename, file, language: str, language_family: str):
        """
        Finds out all the positions of strings and comments in a file.
        The Bear searches for valid comments and strings and yields their
        ranges as SourceRange objects in HiddenResults.

        :param language:        Language to be whose annotations are to be
                                searched.
        :param language_family: Language family whose annotations are to be
                                searched.
        :return:                Two HiddenResults first containing a tuple of
                                SourceRanges of strings and the second
                                containing a tuple of SourceRanges of comments.
        """
        lang_dict = LanguageDefinition(language, language_family)
        print(file)
        # Strings
        strings = dict(lang_dict["string_delimiters"])
        strings.update(lang_dict["multiline_string_delimiters"])
        strings_found = self.find_with_start_end(
                                    filename, file, strings, escape=True)
        # multiline Comments
        comments_found = self.find_with_start_end(
                filename, file, dict(lang_dict["multiline_comment_delimiters"]))
        # single-line Comments
        comments_found += self.find_singleline_comments(
                           filename, file, list(lang_dict["comment_delimiter"]))

        matches_found = strings_found + comments_found
        # Remove Nested
        matches_found = tuple(filter(
                              lambda arg: not starts_within_range(matches_found,
                                                                  arg),
                              matches_found))
        # Yield results
        strings_found = tuple(filter(lambda arg: arg in matches_found,
                                     strings_found))
        yield HiddenResult(self, strings_found)
        comments_found = tuple(filter(lambda arg: arg in matches_found,
                                      comments_found))
        yield HiddenResult(self, comments_found)

    @staticmethod
    def find_with_start_end(filename, file, annot, escape=False):
        """
        Gives all positions of annotations which have a start and end.

        :param filename: Name of the file on which bear is running.
        :param file:     Contents of the file in the form of tuple of lines.
        :param annot:    A dict containing start of annotation as key and end of
                         annotation as value.
        :param escape:   Variable to check wether to ignore escaped annotations.

        :return:         A tuple of SourceRanges giving the range of annotation.
        """
        text = ''.join(file)
        if escape:
            search_func = unescaped_search_in_between
        else:
            search_func = search_in_between
        found_pos = ()
        for annot_type in annot:
            found_pos += tuple(search_func(annot_type, annot[annot_type], text))
        if found_pos:
            found_pos = tuple(SourceRange.from_absolute_position(
                                filename,
                                AbsolutePosition(file, position.begin.range[0]),
                                AbsolutePosition(file, position.end.range[1]-1))
                              for position in found_pos)
        return found_pos

    @staticmethod
    def find_singleline_comments(filename, file, comments):
        """
        Finds all single-line comments.

        :param filename: Name of the file on which bear is running.
        :param file:     Contents of the file in the form of tuple of lines.
        :param comments: A list contatining different types of
                         single-line comments.
        :return:         A tuplle of SourceRange objects with start as start of
                         commentand end as end of line.
        """
        text = ''.join(file)
        single_comments = []
        for comment_type in comments:
            for found in search_for(comment_type, text):
                start = found.start()
                end = text.find('\n', start)
                end = len(text) - 1 if end == -1 else end
                single_comments.append(SourceRange.from_absolute_position(
                                                  filename,
                                                  AbsolutePosition(file, start),
                                                  AbsolutePosition(file, end)))
        return tuple(single_comments)


def starts_within_range(outside_ranges, inside_range):
    """
    Finds if a particular range starts inside a collection of given ranges.

    :param outside_ranges: SourceRange identifying range to be searched.
    :param inside_range:   A tuple SourceRange objects identifying ranges
                           to be searched in.
    :return:               True if inside_range is found inside any of the
                           ranges given by outside_ranges, else
                           False is returned.
    """
    for outside_range in outside_ranges:
        if inside_range == outside_range:
            continue

        # Special case of python language.
        # Where doc strings (""") and strings (") have a similar start.
        elif inside_range.start == outside_range.start:
            if inside_range.end < outside_range.end:
                return True

        elif (inside_range.start > outside_range.start and
              inside_range.start <= outside_range.end):
            return True
    return False

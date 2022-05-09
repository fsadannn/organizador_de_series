import re
# from pprint import pprint
from typing import List

from .scanner import Token, TokenType, grouping_d, tokenize
from .utils import Stack

chapter_number = re.compile('[0-9]{1,4}')
upperm = re.compile('[A-ZÁÉÍÓÚ].*?[A-ZÁÉÍÓÚ]')
more_2_letters = re.compile('[a-zA-ZñÑáéíóúÁÉÍÓÚ]{3,}')
more_2_digits = re.compile('[0-9]{3,}')

_CHAPTER_PROBABILITY_GAP = 0.6


def _padded_number(number: int, padding: int = 1) -> str:
    episode_text = str(number)

    while len(episode_text) <= padding:
        episode_text = '0' + episode_text

    return episode_text


class ChapterMetadata:
    def __init__(self, serie_name: List[Token], chapter_name: List[Token], episode: Token, season: Token) -> None:
        serie_name_str = ''
        for n, i in enumerate(serie_name):
            if i.type in (TokenType.StopWord, TokenType.KeepJoined) and n != 0:
                serie_name_str += ' ' + i.text.lower()
            elif len(i.text) < 3 or upperm.match(i.text):
                serie_name_str += ' ' + i.text
            elif len(i.text) >= 2:
                serie_name_str += ' ' + i.text[0].upper() + i.text[1:].lower()

        self.serie_name = serie_name_str.strip()

        self.chapter_name = ''

        if chapter_name is not None:
            chapter_name_str = ''

            for n, i in enumerate(chapter_name):
                if i.type in (TokenType.StopWord, TokenType.KeepJoined) and n != 0:
                    chapter_name_str += ' ' + i.text.lower()
                elif len(i.text) < 3 or upperm.match(i.text):
                    chapter_name_str += ' ' + i.text
                elif len(i.text) >= 2:
                    chapter_name_str += i.text[0].upper() + i.text[1:].lower()

            self.chapter_name = chapter_name_str.strip()

        self.episode = int(episode.text) if episode is not None else 0
        self.season = int(season.text) if season is not None else 0

    def episode_number(self, padding: int = 1) -> str:
        return _padded_number(self.episode, padding)

    def season_number(self, padding: int = 1) -> str:
        return _padded_number(self.season, padding)

    def __repr__(self) -> str:
        season = int(self.season != 0) * " season=\"" + \
            int(self.season != 0) * self.season_number() + \
            int(self.season != 0) * "\" "
        chapter_name = int(len(self.chapter_name) > 0) * " chapter_name=\"" + \
            self.chapter_name + int(len(self.chapter_name) > 0) * "\""
        return f'{self.__class__.__name__}< name="{self.serie_name}" episode="{self.episode_number()}"{season}{chapter_name} >'


class Processor:
    def __call__(self, name: str) -> ChapterMetadata:
        tokens: List[Token] = tokenize(name)
        # pprint(tokens)
        return self._process(tokens)

    def _process_group(self, open_token: Token, tokens_stack: Stack):
        # TODO: do something with the groups data
        # for now we just ignore data inside grouping
        token = open_token
        while not (token.type == TokenType.GroupingClose and token.text == grouping_d[open_token.text]) and not tokens_stack.empty:
            token: Token = tokens_stack.pop()
            if token.type == TokenType.GroupingOpen:
                self._process_group(token, tokens_stack)

    def _update_contexts(self, index: int, serie_context: Stack, alt_context: Stack):
        serie_context._stack.pop(index)

        while len(serie_context) > index:
            alt_context.push(serie_context.pop())

        alt_context._stack = alt_context._stack[::-1]

    def _get_chapter(self, chapter_candidates: List[Token], serie_context: Stack, alt_context: Stack) -> Token:
        if len(chapter_candidates) == 0:
            return None

        if len(chapter_candidates) == 1:
            chapter = chapter_candidates[0]
            weigh_of_not_only_number = 0.3
            weight_of_more_that_2_digits = 0.2
            weight_of_more_that_2_consecutive_letters = 0.3

            assert weigh_of_not_only_number + weight_of_more_that_2_digits + \
                weight_of_more_that_2_consecutive_letters < 1.01

            probability = int(chapter.type != TokenType.Number) * \
                weigh_of_not_only_number + int(bool(more_2_digits.search(chapter.text))) * weight_of_more_that_2_digits + int(
                    bool(more_2_letters.search(chapter.text))) * weight_of_more_that_2_consecutive_letters
            probability = 1 - probability

            if probability < _CHAPTER_PROBABILITY_GAP:
                return None

            index = serie_context._stack.index(chapter)
            self._update_contexts(index, serie_context, alt_context)

            return chapter

        candidate_weight: List[float] = []
        # smaller value better
        for candidate in chapter_candidates:
            # 0 if has only numbers
            is_only_number = int(candidate.type != TokenType.Number)
            # if has less than 3 digits the weight is 0, otherway is 1-1/len(digits)
            len_more_3 = int(len(candidate.text) > 3)
            len_weight = 1 - len_more_3 / \
                ((1 - len_more_3) + len_more_3 * len(candidate.text))
            # smaller values for tokens near the end
            position_weight = 1 / candidate.position
            # total weight is the sum of all weight we are considering
            weight = is_only_number + len_weight + position_weight

            candidate_weight.append(weight)

        sorted_candidates = sorted(
            zip(candidate_weight, chapter_candidates), key=lambda x: x[0])
        chapter = sorted_candidates[0][1]
        index = serie_context._stack.index(chapter)
        self._update_contexts(index, serie_context, alt_context)

        # pprint(list(zip(chapter_candidates, candidate_weight)))
        # print()

        return chapter

    def _process(self, tokens: List[Token]) -> ChapterMetadata:
        if len(tokens) == 0:
            return

        tokens_stack = Stack('Tokens')

        for i in tokens[::-1]:
            tokens_stack.push(i)

        serie_context = Stack('Serie Context')
        alt_context = Stack('Chapter Name Context')

        chapter_candidates: List[Token] = []
        has_found_chapter: bool = False
        chapter: Token = None
        season: Token = None

        while not tokens_stack.empty:
            context = alt_context if has_found_chapter else serie_context
            token: Token = tokens_stack.pop()

            if token.type == TokenType.NumberedEpisode:
                search_result = chapter_number.search(token.text)
                number = int(search_result.group())
                chapter = Token(
                    str(number), TokenType.Number, 1)
                has_found_chapter = True

            elif token.type == TokenType.EpisodeWord:
                if tokens_stack.empty:
                    continue

                token = tokens_stack.top()
                if token.type != TokenType.Number:
                    continue

                chapter = tokens_stack.pop()
                chapter = Token(chapter.text, chapter.type, 1)
                has_found_chapter = True

            elif token.type in (TokenType.SeasonEpisode, TokenType.ChapterSeason):
                search_result = token.type.value.search(token.text)
                number = int(search_result.groups()[0])
                season = Token(
                    str(number), TokenType.Number, 1)
                number = int(search_result.groups()[1])
                chapter = Token(
                    str(number), TokenType.Number, 1)
                has_found_chapter = True

            elif token.type in (TokenType.Number, TokenType.NumberedWord) and not has_found_chapter:
                chapter_candidates.append(token)
                context.push(token)

            elif token.type == TokenType.Dash and not tokens_stack.empty:
                next_token: Token = tokens_stack.top()

                if next_token.type != TokenType.KeepJoined:
                    # If dash are not succeeded bey a KeepJoined token the dash is ignored
                    continue

                next_token: Token = tokens_stack.pop()
                prev_token: Token = context.pop()

                new_token = Token(prev_token.text + token.text +
                                  next_token.text, TokenType.JoinedWord, prev_token.position)
                context.push(new_token)

            elif token.type == TokenType.GroupingOpen:
                self._process_group(token, tokens_stack)

            elif token.type in (TokenType.Date, TokenType.ScreenResolution, TokenType.VideoCodec):
                # this tokens are just ignored
                continue

            else:
                context.push(token)

        if not has_found_chapter and len(chapter_candidates) != 0:
            chapter = self._get_chapter(
                chapter_candidates, serie_context, alt_context)

        # pprint(serie_context._stack)
        # print()
        # pprint(alt_context._stack)
        # print()
        # print(chapter)
        # print(season)

        return ChapterMetadata(serie_context._stack, alt_context._stack, chapter, season)

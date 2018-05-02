import sys
import traceback
import json
from colorama import Fore, Style


TOP_FRAME = """
--------------------------------------------------------------
 {c_rate}{C_B}{BD}{title}{E} ({title_EN})
--------------------------------------------------------------
 {genre} | {nationality} | {date} 개봉
--------------------------------------------------------------
""".strip()

TIMELINE_FRAME = " " + """
{C_B}{start}{E} - {end} | {C_B}{avail_cap}{E} / {total_cap} | {cinfo} ({hinfo})
""".strip()

END_FRAME = """
--------------------------------------------------------------
""".strip() + "\n\n"

color_pack = {'C_B': Fore.LIGHTBLUE_EX,
              'C_Y': Fore.LIGHTYELLOW_EX,
              'C_R': Fore.LIGHTRED_EX,
              'C_G': Fore.LIGHTGREEN_EX,
              'BD': Style.BRIGHT,
              'E': Style.RESET_ALL
              }


class PearlError(Exception):
    def __init__(self, msg):
        self.msg = msg
        # Set custom exception handler for Exception printouts
        sys.excepthook = self.Exception_Handler

    def Exception_Handler(self, exception_type, exception, tb):

        # Error message format:
        err_msg = "\n".join([
                            "[*] PearlError on {tb_loc}",
                            "->  {err_msg}",
                            ])

        # Fabricate traceback message and print
        tbs = traceback.extract_tb(tb)

        tb_loc = []
        for tb in tbs:
            tb_loc.append(
                ': {filename}, Line {line}'.format(filename=tb[0],
                                                   line=tb[1],
                                                   code=tb[3]))
        tb_loc = ("\n" + " " * len('[*] PearlError on ')).join(tb_loc)

        err_msg = err_msg.format(err_msg=exception,
                                 tb_loc=tb_loc)
        print(err_msg)

    def __str__(self):
        return "{}".format(self.msg)


class Clip:
    def __init__(self, *args, **kwargs):
        self.data = []
        self._is_sorted = False
        self._contains_detail = False

        # If param is empty, then skip
        if not (len(args) + len(kwargs)):
            pass

        else:
            valid_keys = ('title', 'cinfo', 'hinfo', 'start', 'end',
                          'avail_cap', 'total_cap', 'rate')
            if set(kwargs.keys()) != set(valid_keys):
                raise PearlError(
                    'Invalid input param(s) for the class `Clip`.')

            self.data.append(kwargs)

    def __add__(self, other):
        if self._is_sorted or other._is_sorted:
            err = 'Cannot add <core.Clip> classes after the `sort` method.'
            raise PearlError(err)

        self.data += other.data
        return self

    def to_json(self):
        return json.dumps(self.data)

    def sort(self):
        # Sort item by ascending order
        self.data = sorted(self.data, key=lambda k: k['title'])

        # Within iteration, re-format previous data
        movies = []
        title = None
        mv = None
        for movie in self.data:
            if movie['title'] != title:
                movies.append(mv)

                title = movie.pop('title')
                rate = movie.pop('rate')

                mv = {
                    'title': title,
                    'rate': rate,
                    'timeline': [movie]
                }
            else:
                # Pop title and rate
                movie.pop('title')
                rate = movie.pop('rate')
                # Update rate if not None
                mv['rate'] = rate or mv['rate']
                mv['timeline'].append(movie)

        # Pop the first item, because it is `None`
        movies.pop(0)

        # Sort timeline in ascending order for every movie
        for movie in movies:
            tl = movie['timeline']
            movie['timeline'] = sorted(tl, key=lambda k: k['start'])
        # Disable __add__ method with other Clip classes
        self._is_sorted = True

        # Save data
        self.data = movies

    def show(self, detail=True):
        self.sort()

        # If detail flag is on, get detail information
        if detail:
            from pearl.parser import get_detail
            movie_details = get_detail(items=300)
            # Filter movies
            for movie in self.data:
                # Remove '(더빙) ' for the Megabox data
                title = movie['title'].replace('(더빙) ', '')
                if title in movie_details.keys():
                    movie['title_EN'] = \
                        movie_details[title]['title_EN']
                    movie['genre'] = \
                        movie_details[title]['genre']
                    movie['nationality'] = \
                        movie_details[title]['nationality']
                    movie['openDate'] = \
                        movie_details[title]['openDate']
                    movie['directors'] = \
                        movie_details[title]['directors']
                else:
                    movie['title_EN'] = ''
                    movie['genre'] = ''
                    movie['nationality'] = ''
                    movie['openDate'] = ''
                    movie['directors'] = ''

            # Set flag `True`
            self._contains_detail = True

        for movie in self.data:
            rate = movie['rate']
            if rate == 'ALL':
                rate = 'ALL | '
            elif rate == '12':
                rate = '{C_B}12{E} | '.format(**color_pack)
            elif rate == '15':
                rate = '{C_Y}15{E} | '.format(**color_pack)
            elif rate == '19':
                rate = '{C_R}19{E} | '.format(**color_pack)
            else:
                rate = ""

            # Print Top Frame
            print(TOP_FRAME.format(
                **movie,
                **color_pack,
                c_rate=rate,
                date=movie['openDate'].strftime("%Y.%m.%d.")))

            # Print Timelines
            for timeline in movie['timeline']:
                print(TIMELINE_FRAME.format(**timeline, **color_pack))

            # Print BottomLine
            print(END_FRAME)

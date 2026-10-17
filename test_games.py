# -*- coding: utf-8 -*-
from games.game_registry import get_game_info


def main():
    for info in get_game_info():
        print("-" * 50)
        for key in sorted(info.keys()):
            print("{0}: {1}".format(key, info[key]))


if __name__ == "__main__":
    main()

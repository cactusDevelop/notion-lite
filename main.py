"""
                                                      .::.       ^7
                                                  .^7JPB#&@#GJ^  .7&@BJ?JYYJ7~:
                                              .~YG#@@@@@@@@@@@@BG#@@@@@@@@@@@@&G7
                                            ^Y#@@@@@@@@@@@@@@@@@@@@@@@@G@@@@@@@@@G.
                                          Y#@@@@@@@@@@@@@@@@@@@@@@@@@@YG@@@&5&@@@@!
                                          5@@@@@@@@@@@@@@@@@@@@@@@@@@JY@@&Y7G@@@@@^
                                          :&@@@@@@@@@@@@@@@@@@@@@@@@??@@#JP@@#&@@?
                                          :G@@@@@@@@@@@@@@@#BB#@@@Y:7@@@@@&P5#@@J
                                            7B@@@@@@@@@@@@G..J&@@G.Y@@@@@GG&@#@B
                                             .?&@@@@@@@@@@J  ^#@@5B@@@@@@@@#!^G5
                                               :P@@@@@@@@&:  ~&@B#@@@@@@@@5.~G@?
                                        :~!7~    ?@@@@@@@@~ .#@@@@@@@@@@P^ J@@Y   .!7??JYPGBBBBP5?^
                                      :7JJJJJ?.   ~&@@@@@@7 5@@@@@@@@@&7  5@B!  :JG?^P@@@@@@@&&@@@@B?.
                    :~!7!~.          ^JJJ?JJJJ?!~: ~&@@@@@!7@@@@@@@@@G: 7GP! .7GB?:.Y#@@@&BPPG&@@@@@@^
                  :7JJJJJJJ!.       :JJJJ!JJ7JJJJ?77P@@@@@7#@@@@@@@@J 7B@BJJG@@5. ^P@#Y!7YG&@@@@@@@@J
                 ^JJJJJ??JJJ?^     :?JJJ?~J?~JJJJJJJJB@@@#P@@@@@@@B~~G@@@@@@@B!:JB&&B55B&@#PYYP&@@@?
               ~?JJJJJJ?^?J7JJ?!:  ~7^?Y!^J?J?7JJJJJJ5@@@&@@@@@@@Y!P@@@@@@@#YJG@@@@&@@@@@@&##&@@@@G
               .?JJJ?!?J77J!J?:7J~ .?.:??!JJJ7J?JJJJJJ#@@@@@@@@BJP@@@@@@@&BG#@@@@@@@@@@&BGPG&@@@@@&7
            .^~7JJJJJJ!!JJJ??J!.7Y^ ?7 ~JJJJJJ?.!JJJJJB@@@@@@&PP&@@@@@@@@&@@@@@@@@@@@@@@@@@@@@@@@@Y:
           ^?JJJJJJJJJJ!:?JJJJJ^ 77:?J~^JJJJJJ^.?JJJJJG@@@@@#G#@@@@@@@@@@@@@@@@@@&#P5Y7!7#@@@@@@@@@B!.
           ?JJJJJJJJJJJJ!~?JJJJJ: 7JJJJ~?JJJJ? ^JJJJJJB@@@&##@@@@@@@@@@@@@@&#GY?~:.:!J5G#@@@@@@@@@@@&7
          ^JJJJJJJJJJJ!7JJ?JJJJJJ:^JJJJ??JJJJ~:?JJJJ?!B@@@@@@@@@@@@@&&#BG5YJ??J55GB&@@@@@@@@@@@@@@@#:
          !JJJJJJJJJJ?:..:7JJJJJJJ:!JJJJJJJJ?:?YJ7~: :&@@@@@@@@@@@&###&&@@@@@@@@@@@@@@@@@@@@@@@@@@@7
          !JJJJJJJJJJJJ?^..^?JJJJJ?^?JJJJJJJ!7J!:    Y@@@@#GY7~^^:::^~!7JPB&@@@@@@@@@@@@@@@@@@@@@@B.
          ^JJJJJJJJJJJJJJJ?!~!?JJJJ?!JJJJJJJ7!.     ~@@#Y~.                .^7YB&@@@@@@@@@@@@@@@@Y.
          :7??JJJJJJJ???JJJJJ???JJJJ77JJJJJ7:      ^&#?^:^^:^^^^^^^:...         :!YB@@@@@@@@@@@@@#.
             .^^^:........::^~77JJJJJ??JJJ?.      ~#Y:~~!!!!!!!!!!~~~~~~~~~~~~.     ^?5GB&@@@@YJ5?
                                .^!?JJJJJJ^      7B~  ~~~~~~~^^^~~~~!^^~~~~!~^.          :~!!:
                                    :!?JJJ:    .YG:   :!~~^:^^~~~~~~^^^^^~~:.
                                      .~?Y^   ~G?     ^~~~~~!~~~~~~^^:::::............
                                        .!? .YG^   .:~~~~~~~~~~~~^^^::^^^^~~~~~~~~~~~~~.
                                          ^JGY..:^^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~!!!^.
                             ........... ^PG?. .........::^^~~~~~^^^:::^^~~~~~~~~~~^::.
                                        J&5.:!                .:^~~~~~~~~~~~~~~~!!!:
                                       P&!   ^!                   .:^~!!!!!!!!~~^:.
                                       7:     ~!                     .::^^^::..
                                               !!
                                                7!
                                                 :.

"""
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.themes.theme import apply_theme, detect_system_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Notion Lite")
    apply_theme(app, detect_system_theme())

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# Anki-WaniKani-Hints

## Idea
Integrate with [WaniKani](https://www.wanikani.com) API to add "tips" for what radicals make up a kanji, as well as meaning/reading mnemonics for kanji and vocabulary. Utilizes (generated) local json cache to avoid duplicate queries and drastically increase speed.

## References
Tooltip CSS and rendering-related Python code adapted from [anki-kakijun](https://github.com/midse/anki-kakijun) (Due to overlap in rendering-methodology, using both addons simultaneously may result in undesirable behavior. [Kanji Colorizer](https://ankiweb.net/shared/info/1964372878) is recommended for stroke order diagrams).
### Options

`token` : WaniKani API token

`kanji_filter` : change the kanji tip filter name

`vocab_filter` : change the vocab tip filter name

`vocab_field` : if the field that `vocab_filter` is attached to's text-value is different from the raw vocabulary string (e.g. if you want the tip to appear under a furigana string), set `vocab_field` to the name of the field that contains the raw vocabulary string (i.e. without furigana). If null, uses the text-value of the field that has `vocab_filter` attached.

### Styling

The HTML/CSS styling of the tip itself can be modified by either editing `static.py` in the add-on directory directly, or by adding styling to the relevant classes (found in `static.py`) in the normal card editor.
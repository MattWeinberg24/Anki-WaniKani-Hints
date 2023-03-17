# Courtesy of https://github.com/midse/anki-kakijun under the MIT License

css = """
.tooltip {
    display:inline-block;
    position:relative;
    border-bottom:1px dotted #666;
    text-align:left;
    cursor: pointer;
}
.tooltip .bottom {
    width: max-content;
    min-width:100px;
    max-width:400px;

    left:50%;
    transform:translate(-50%, 0);
    padding:10px;
    color:#666666;
    background-color:#EEEEEE;
    font-weight:normal;
    font-size:13px;
    border-radius:8px;
    position:absolute;
    z-index:99999999;
    box-sizing:border-box;
    box-shadow:0 1px 8px rgba(0,0,0,0.5);
    display:none;
}
.tooltip:hover .bottom {
    display:block;
}
.radical-list {
    border-bottom:2px solid #666;
}
.reading-mnemonic, .meaning-mnemonic {
    border-bottom:2px solid #666;
}
radical, kanji, reading, ja {
    font-weight: bold;
}

"""
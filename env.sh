# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo $DIR
if [ -z "$PYTHONPATH" ] ; then
    export PYTHONPATH=$DIR
else
    export PYTHONPATH=$DIR:$PYTHONPATH
fi

alias gxs700-capture=$DIR/gxs700/capture.py
alias gxs700-decode=$DIR/gxs700/decode.py
alias gxs700-mask=$DIR/gxs700/mask.py
alias gxs700-stitch=$DIR/gxs700/stitch.sh
alias gxs700-dump=$DIR/gxs700/dump.py

#alias gxs700-cbct=$DIR/gxs700/cbct.py
#alias gxs700-fire=$DIR/gxs700/fire.py


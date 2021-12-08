#!/bin/bash

PYTHONHOME="/vol/research/xmodal_dl/txtreid-env/bin"
HOME="/vol/research/xmodal_dl/dalle-lightning"

echo $HOME
echo 'args:' $@

$PYTHONHOME/python $HOME/train_vae.py --root $HOME $@

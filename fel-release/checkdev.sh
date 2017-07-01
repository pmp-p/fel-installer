#!/bin/sh
fel=./fel-bin/sunxi-fel.${fel}
while true
do
    if sleep 1
    then
        echo $$ > devtest.txt
        $fel -l >> devtest.txt
        sync
    else
        break
    fi
done

#!/usr/bin/fish


function escape -a filename
    echo -n $filename | sed -Ee 's/[^a-zA-Z0-9_-]+/_/g' -e 'y/QWERTYUIOPASDFGHJKLZXCVBNM/qwertyuiopasdfghjklzxcvbnm/'
end


function make_fake -a title
    test -z "$title" ; and exit 1
    set filename spool/plain/(escape $title)
    set dir (dirname $filename)

    mkdir -p $dir

    touch $filename.pdf
    echo $filename.pdf
end


make_fake $argv

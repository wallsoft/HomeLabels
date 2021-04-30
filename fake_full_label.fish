#!/usr/bin/fish


function escape -a filename
    echo -n $filename | sed -Ee 's/[^a-zA-Z0-9_-]+/_/g' -e 'y/QWERTYUIOPASDFGHJKLZXCVBNM/qwertyuiopasdfghjklzxcvbnm/'
end


function make_fake -a category title subtitle description
    test -z "$category" ; and exit 1
    test -z "$title" ; and exit 1
    set filename spool/(escape $category)/(escape $title)
    set dir (dirname $filename)

    mkdir -p $dir

    touch $filename.pdf
    echo $filename.pdf
    touch $filename.txt
    echo $filename.txt
end


make_fake $argv

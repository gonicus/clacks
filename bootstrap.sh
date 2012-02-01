#!/bin/bash
HERE=$(pwd)


prepare_clacks() {
        cd $HERE
        echo -n "Creating virtual environment: "
        virtualenv --setuptools --system-site-packages clacks &> /dev/null && echo ok
        if [ $? -ne 0 ]; then
                echo "failed"
                exit 1
        fi

        echo -n "Cloning from git://github.com/clacks/clacks.git: "
        git clone git://github.com/clacks/clacks.git clacks/src &> /dev/null && echo ok
        if [ $? -ne 0 ]; then
                echo "failed"
                exit 1
        fi

        cd $HERE/clacks
        source bin/activate
        for component in common shell agent; do
                echo -n "Deploying component: $component"
                cd $HERE/clacks/src/$component
                ./setup.py develop &> /dev/null && echo ok
                if [ $? -ne 0 ]; then
                        echo "failed"
                        exit 1
                fi
        done
        deactivate
        cd $HERE
}


prepare_vim() {
	echo -n "Installing 'vundle': "
	git clone http://github.com/gmarik/vundle.git ~/.vim/bundle/vundle && echo ok
        if [ $? -ne 0 ]; then
                echo "failed"
                exit 1
        fi
	cat <<EOF > ~/.vimrc
set nocompatible               " be iMproved
filetype off                   " required!

set rtp+=~/.vim/bundle/vundle/
call vundle#rc()

" let g:Powerline_symbols = 'fancy'
let g:Powerline_symbols = 'unicode'
set laststatus=2
set encoding=utf-8 " Necessary to show unicode glyphs
set t_Co=256 " Explicitly tell vim that the terminal supports 256 colors


" let Vundle manage Vundle
" required! 
Bundle 'gmarik/vundle'

" My Bundles here:
"
" original repos on github
Bundle 'Lokaltog/vim-powerline'
Bundle 'sophacles/vim-bundle-python'
Bundle 'tpope/vim-fugitive'
Bundle 'Lokaltog/vim-easymotion'
Bundle 'rstacruz/sparkup', {'rtp': 'vim/'}
Bundle 'tpope/vim-rails.git'
" vim-scripts repos
Bundle 'L9'
Bundle 'FuzzyFinder'
" non github repos
Bundle 'git://git.wincent.com/command-t.git'
" ...

filetype plugin indent on     " required! 
"
" Brief help
" :BundleList          - list configured bundles
" :BundleInstall(!)    - install(update) bundles
" :BundleSearch(!) foo - search(or refresh cache first) for foo
" :BundleClean(!)      - confirm(or auto-approve) removal of unused bundles
"                                                                                                                                                                    
" see :h vundle for more details or wiki for FAQ                                                                                                                     
" NOTE: comments after Bundle command are not allowed..
EOF
	vim +BundleInstall +qall
}


if [ ! -d $HERE/clacks ]; then
        read -s -i y -n 1 -p "There is no clacks virtual environment available, do you want me to
create one for you? [Yn]" prmpt
        echo
        if [ -z "$prmpt" -o "$prmpt" = "y" ]; then
                prepare_clacks
        fi
fi

if [ ! -f $HERE/.vimrc ]; then
        read -s -i y -n 1 -p "There is no vim configuration installed. Do you want me to configure
vim for python? [Yn]" prmpt
        echo
        if [ -z "$prmpt" -o "$prmpt" = "y" ]; then
                prepare_vim
        fi
fi

if [ -d $HERE/clacks ]; then
        echo "Found virtual clacks environment - activating it..."
        cd $HERE/clacks
        source bin/activate
        cd $HERE
fi

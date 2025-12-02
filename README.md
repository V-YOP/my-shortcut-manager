# my-shortcut-manager

A dumb shortcut manager, Opening files with simple commands

# Usage

Add it to PATH first.

```sh
sm bas      # open the shortcut whose non-contiguous substring is 'bas'
sm _ls      # list all shortcuts
sm _add 'krita_files' 'D:/kra'  # add shortcut entry
sm _add 'google' 'https://google.com'  # add shortcut entry

sm _add_cmd -- my_script_id python my_script_path --my_script_args # add command shortcut
sm msi some_additional_arg # run command shortcut with additional_args
sm _rm my_script_id # remove shortcut by exact id
sm -h       # help
sm _ls -h   # _ls's help
```

# Auto-Completation

Add it to `~/.bashrc`：

```bash
_sm_complete() {
    # 获取当前输入和上下文
    local cur="${COMP_WORDS[COMP_CWORD]}"    # 当前输入的部分
    local prev="${COMP_WORDS[COMP_CWORD-1]}" # 上一个单词
    local cmd="sm"                           # 主命令

    # 如果已经有参数，则不做补全
    if [[ ${#COMP_WORDS[@]} -gt 2 ]]; then
        return 0
    fi

    # 动态获取候选项并处理 \r\n
    local options=$(sm _entries | tr '\r\n' ' ') # 替换 \r\n 为单空格
    COMPREPLY=( $(compgen -W "$options" -- "$cur") )
}

# 将补全函数绑定到命令 `sm`
complete -F _sm_complete sm
```

# GUI version (for windows, for Win+R)

A helper binary file is needed for Win+R to run the script.

```sh
g++ -mwindows -O2 -s -o gsm.exe gsm_launcher.cpp
```
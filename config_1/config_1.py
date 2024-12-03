import argparse
import tarfile
import os
import sys
import shlex


class VirtualFile:
    def __init__(self, name, is_dir=False, content=None, size=0, parent=None):
        self.name = name
        self.is_dir = is_dir
        self.content = content  # Для файлов - содержимое
        self.size = size  # Размер файла
        self.children = {}  # Для директорий - словарь дочерних элементов
        self.parent = parent  # Ссылка на родительский узел


class VirtualFileSystem:
    def __init__(self, tar_path):
        self.root = VirtualFile('/', is_dir=True)
        self.cwd = self.root  # Текущий каталог
        self.load_filesystem(tar_path)

    def load_filesystem(self, tar_path):
        if not os.path.isfile(tar_path):
            print(f"Файл {tar_path} не найден.")
            sys.exit(1)

        with tarfile.open(tar_path, 'r') as tar:
            for member in tar.getmembers():
                self.add_member(member, tar)

    def add_member(self, member, tar):
        # Нормализуем путь
        path = os.path.normpath(member.name)
        if path == '.':
            return  # Пропускаем запись текущего каталога
        if path.startswith('.' + os.sep):
            path = path[2:]  # Удаляем './' из начала пути
        path_parts = path.strip(os.sep).split(os.sep)

        current_node = self.root
        for part in path_parts[:-1]:
            if part not in current_node.children:
                new_dir = VirtualFile(part, is_dir=True, parent=current_node)
                current_node.children[part] = new_dir
            current_node = current_node.children[part]

        name = path_parts[-1]
        if member.isdir():
            if name not in current_node.children:
                new_dir = VirtualFile(name, is_dir=True, parent=current_node)
                current_node.children[name] = new_dir
        else:
            file_obj = tar.extractfile(member)
            content = file_obj.read() if file_obj else b''
            new_file = VirtualFile(name, is_dir=False, content=content, size=member.size, parent=current_node)
            current_node.children[name] = new_file

    def change_directory(self, path):
        node = self.get_node(path)
        if node and node.is_dir:
            self.cwd = node
        else:
            print(f"cd: {path}: Нет такого файла или каталога")

    def list_directory(self):
        for name in sorted(self.cwd.children):
            print(name)

    def get_node(self, path):
        if path.startswith('/'):
            current_node = self.root
            parts = path.strip('/').split('/')
        else:
            current_node = self.cwd
            parts = path.strip().split('/')

        for part in parts:
            if part == '' or part == '.':
                continue
            elif part == '..':
                if current_node.parent:
                    current_node = current_node.parent
            elif part in current_node.children:
                current_node = current_node.children[part]
            else:
                return None
        return current_node

    def head(self, filename, lines=10):
        node = self.get_node(filename)
        if node and not node.is_dir:
            content = node.content.decode('utf-8', errors='ignore')
            content_lines = content.split('\n')
            for line in content_lines[:lines]:
                print(line)
        else:
            print(f"head: не удалось открыть '{filename}' для чтения: Нет такого файла")

    def du(self, path=None):
        node = self.cwd
        if path:
            node = self.get_node(path)
            if not node:
                print(f"du: {path}: Нет такого файла или каталога")
                return
        size = self.calculate_size(node)
        print(f"{size}\t{self.get_full_path(node)}")

    def calculate_size(self, node):
        if not node.is_dir:
            return node.size
        total_size = 0
        for child in node.children.values():
            total_size += self.calculate_size(child)
        return total_size

    def get_full_path(self, node):
        path = ''
        while node.parent is not None:
            path = '/' + node.name + path
            node = node.parent
        return path if path else '/'


def parse_args():
    parser = argparse.ArgumentParser(description='Эмулятор оболочки UNIX-подобной ОС.')
    parser.add_argument('-n', '--hostname', required=True, help='Имя компьютера для приглашения.')
    parser.add_argument('-f', '--filesystem', required=True, help='Путь к архиву виртуальной файловой системы.')
    parser.add_argument('-s', '--script', help='Путь к стартовому скрипту.')
    return parser.parse_args()


def get_current_path(node):
    path = ''
    while node.parent is not None:
        path = '/' + node.name + path
        node = node.parent
    return path if path else '/'


def execute_script(script_path, vfs, hostname):
    if not os.path.isfile(script_path):
        print(f"Скрипт {script_path} не найден.")
        return
    with open(script_path, 'r') as f:
        for line in f:
            user_input = line.strip()
            if not user_input or user_input.startswith('#'):
                continue  # Пропускаем пустые строки и комментарии
            print(f"[{hostname}]:{get_current_path(vfs.cwd)}$ {user_input}")
            process_command(user_input, vfs)


def process_command(user_input, vfs):
    cmd_args = shlex.split(user_input)
    if not cmd_args:
        return
    command = cmd_args[0]
    params = cmd_args[1:]

    if command == 'ls':
        vfs.list_directory()
    elif command == 'cd':
        path = params[0] if params else '/'
        vfs.change_directory(path)
    elif command == 'exit':
        sys.exit(0)
    elif command == 'head':
        if not params:
            print("usage: head FILENAME")
        else:
            filename = params[0]
            lines = 10  # По умолчанию 10 строк
            # Проверка на опцию -n (количество строк)
            if len(params) >= 3 and params[0] == '-n':
                try:
                    lines = int(params[1])
                    filename = params[2]
                except ValueError:
                    print("head: неверный аргумент для '-n'")
                    return
            vfs.head(filename, lines)
    elif command == 'du':
        path = params[0] if params else None
        vfs.du(path)
    else:
        print(f"{command}: команда не найдена")


def main():
    args = parse_args()
    vfs = VirtualFileSystem(args.filesystem)
    hostname = args.hostname

    # Если указан скрипт, выполняем команды из него
    if args.script:
        execute_script(args.script, vfs, hostname)

    # Основной цикл
    while True:
        try:
            prompt = f"[{hostname}]:{get_current_path(vfs.cwd)}$ "
            user_input = input(prompt)
            process_command(user_input, vfs)
        except KeyboardInterrupt:
            print("\nДля выхода используйте команду 'exit'")
        except EOFError:
            print("\nВыход")
            sys.exit(0)


if __name__ == '__main__':
    main()

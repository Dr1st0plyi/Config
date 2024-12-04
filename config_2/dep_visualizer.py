import argparse
import requests
import gzip
import os
import subprocess

def parse_arguments():
    parser = argparse.ArgumentParser(description='Визуализатор графа зависимостей Ubuntu пакета.')
    parser.add_argument('--plantuml_path', required=True, help='Путь к программе для визуализации графов (plantuml.jar).')
    parser.add_argument('--package_name', required=True, help='Имя анализируемого пакета.')
    parser.add_argument('--output_path', required=True, help='Путь к файлу с изображением графа зависимостей.')
    return parser.parse_args()

def download_packages_file():
    url = 'http://archive.ubuntu.com/ubuntu/dists/focal/main/binary-amd64/Packages.gz'
    response = requests.get(url)
    if response.status_code == 200:
        with open('Packages.gz', 'wb') as f:
            f.write(response.content)
        with gzip.open('Packages.gz', 'rb') as f_in:
            with open('Packages.txt', 'wb') as f_out:
                f_out.write(f_in.read())
    else:
        print('Не удалось загрузить файл пакетов.')
        exit(1)

def parse_packages_file():
    packages = {}
    current_package = {}
    with open('Packages.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == '':
                if 'Package' in current_package:
                    packages[current_package['Package']] = current_package
                current_package = {}
            else:
                if ': ' in line:
                    key, _, value = line.partition(': ')
                    current_package[key] = value
                else:
                    continue  # Обработка переносов строк внутри значений
    return packages

def get_dependencies(package_name, packages, dependencies=None, visited=None):
    if dependencies is None:
        dependencies = set()
    if visited is None:
        visited = set()
    if package_name not in packages:
        return dependencies
    if package_name in visited:
        return dependencies
    visited.add(package_name)
    pkg_info = packages[package_name]
    if 'Depends' in pkg_info:
        depends_line = pkg_info['Depends']
        depends = [dep.strip() for dep in depends_line.split(',')]
        for dep in depends:
            dep_name = dep.split(' ')[0]
            dependencies.add((package_name, dep_name))
            get_dependencies(dep_name, packages, dependencies, visited)
    return dependencies

def generate_plantuml(dependency_pairs):
    lines = ['@startuml']
    for parent, child in dependency_pairs:
        lines.append(f'"{parent}" --> "{child}"')
    lines.append('@enduml')
    return '\n'.join(lines)

def generate_png(plantuml_code, plantuml_path, output_path):
    with open('diagram.puml', 'w', encoding='utf-8') as f:
        f.write(plantuml_code)
    subprocess.run(['java', '-jar', plantuml_path, 'diagram.puml'])
    os.rename('diagram.png', output_path)
    os.remove('diagram.puml')

def main():
    args = parse_arguments()
    download_packages_file()
    packages = parse_packages_file()
    dependency_pairs = get_dependencies(args.package_name, packages)
    plantuml_code = generate_plantuml(dependency_pairs)
    generate_png(plantuml_code, args.plantuml_path, args.output_path)
    print('Граф зависимостей успешно сохранен в', args.output_path)

if __name__ == '__main__':
    main()
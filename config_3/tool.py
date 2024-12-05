import xml.etree.ElementTree as ET
import sys

def parse_value(element):
    if element.tag == 'number':
        return element.text.strip()
    elif element.tag == 'string':
        return f'"{element.text.strip()}"'
    elif element.tag == 'array':
        items = [parse_value(child) for child in element]
        return '(list ' + ' '.join(items) + ' )'
    elif element.tag == 'var':
        name = element.attrib.get('name')
        value = parse_value(list(element)[0])
        return f'var {name} {value};'
    elif element.tag == 'expr':
        op = element.attrib.get('op')
        operands = [parse_value(child) for child in element]
        if op in ['+', '-']:
            # Формируем инфиксное выражение
            expr = f" .{{ {' '.join([operands[0], op, operands[1]])} }}."
            return expr
        elif op == 'sort':
            # Для функции sort()
            expr = f".{{ sort({', '.join(operands)}) }}."
            return expr
        elif op == 'min':
            # Для функции min()
            expr = f".{{ min({', '.join(operands)}) }}."
            return expr
        else:
            raise ValueError(f"Неизвестная операция: {op}")
    elif element.tag == 'comment':
        # Однострочный комментарий
        comment_text = element.text.strip()
        return f'NB. {comment_text}'
    elif element.tag == 'multiline_comment':
        # Многострочный комментарий
        comment_text = element.text.strip()
        return f'|#\n{comment_text}\n#|'
    else:
        raise ValueError(f"Неизвестный элемент: {element.tag}")

def parse_xml_to_config(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        output_lines = []
        for child in root:
            output = parse_value(child)
            output_lines.append(output)
        return '\n'.join(output_lines)
    except ET.ParseError as e:
        print(f"Ошибка разбора XML: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка в данных XML: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Использование: python tool.py <входной_xml> <выходной_файл>")
        sys.exit(1)

    input_xml = sys.argv[1]
    output_file = sys.argv[2]

    output_text = parse_xml_to_config(input_xml)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_text)

    print("Преобразование завершено успешно.")

if __name__ == '__main__':
    main()
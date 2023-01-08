import argparse
import ast


# Класс для парсинга аргументов
class Parser(argparse.ArgumentParser):
    def __init__(self, prog, desc, args):
        super().__init__(prog=prog, description=desc)
        for arg in args:
            self.add_argument(arg[0], help=arg[1])


# Класс для тестирования двух файлов
class Tester:
    def __init__(self, path_orig, path_test):
        orig = open(path_orig)
        test = open(path_test)

        code1 = orig.read()
        code2 = test.read()

        self.tree1 = ast.parse(code1)
        self.tree2 = ast.parse(code2)

        orig.close()
        test.close()

    def test(self):
        NameFormatter().visit(self.tree1)
        CommentCleaner().clean(self.tree1)

        NameFormatter().visit(self.tree2)
        CommentCleaner().clean(self.tree2)

        checker = SimilaityCheck(ast.unparse(
            self.tree1), ast.unparse(self.tree2))

        return round(checker.similarity_score(), 5)


# Класс с расстоянием Левенштейна
class SimilaityCheck:
    def __init__(self, S1, S2):
        self.S1 = S1
        self.S2 = S2

    def __levenshtein_dist(self):
        n, m = len(self.S1), len(self.S2)
        if n > m:
            self.S1, self.S2 = self.S2, self.S1
            n, m = m, n

        current_row = range(n + 1)
        for i in range(1, m + 1):
            previous_row, current_row = current_row, [i] + [0] * n
            for j in range(1, n + 1):
                add, delete, change = previous_row[j] + \
                    1, current_row[j - 1] + 1, previous_row[j - 1]
                if self.S1[j - 1] != self.S2[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)

        return current_row[n]

    def similarity_score(self):
        return 1 - self.__levenshtein_dist() / max(len(self.S1), len(self.S2))


# Этот класс старается минимизировать влияние названий переменных на оригинальность
class NameFormatter(ast.NodeTransformer):
    def __init__(self):
        self.identifiers = {}
        super().__init__()

    def visit_Name(self, node):
        try:
            id_ = self.identifiers[node.id]
        except KeyError:
            id_ = f'n{len(self.identifiers)}'
            self.identifiers[node.id] = id_
        return ast.copy_location(ast.Name(id=id_), node)


# Этот класс очищает docstrings
class CommentCleaner:
    def __init__(self):
        pass

    def clean(self, tree):
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                continue

            if not len(node.body):
                continue

            if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Str):
                continue

            if not isinstance(node.body[0], ast.Expr):
                continue

            node.body = node.body[1:]


args = Parser(
    prog='python3 compare.py', desc='Anti-plagiarism test',
    args=[['input', 'path to file with original files'],
          ['output', 'path to file with testable files']]).parse_args()

# Работа с файлам
file_in = open(args.input, 'r')
file_out = open(args.output, 'w')

paths = file_in.read()
paths = paths.split('\n')

file_in.close()

print('Kowalski, analysis! Процесс может занять некоторое время...')
# Главный цикл
for i in paths:
    # Чтение путей файлов
    try:
        path_orig, path_test = i.split()
    except:
        print(f'Не удалось прочитать строку <{i}>')

    # Работа Tester + запись в файл
    try:
        score = Tester(path_orig, path_test).test()
        file_out.write(f'{path_orig} <-> {path_test} = {str(score)}\n')
        print(f'{path_orig} <-> {path_test} = {str(score)}')
    except FileNotFoundError:
        print(f'Не найден один из файлов {path_orig} и {path_test}')
        file_out.write(f'{path_orig} <-> {path_test} = failed\n')
    except Exception as e:
        print(
            e, f'Произошла неожиданная ошибка при обработке файлов {path_orig} и {path_test}! Пропускаю...', sep='\n')
        file_out.write(f'{path_orig} <-> {path_test} = failed\n')

print(f'Процесс завершен. Результат записан в {args.output}')

file_out.close()
